# Minimal production image for the SellerOS FastAPI backend.
#
# WHY THIS FILE EXISTS: there was no Dockerfile, docker-compose, or
# startup script anywhere in the project -- no defined way to run this
# in production at all. This is the smallest image that boots the app
# correctly, in particular installing the Playwright Chromium browser
# that meesho_connector.py / flipkart_playwright_connector.py require
# at runtime (backend/requirements.txt installs the `playwright`
# Python package, but NOT the browser binary -- those are two separate
# install steps, and without the second one every Meesho/Flipkart
# Playwright call fails immediately).
FROM python:3.12-slim

WORKDIR /app

# System packages Playwright's Chromium needs to actually launch
# (fonts, X11/GTK libs, etc.) -- `playwright install --with-deps`
# handles this list itself, so it is not duplicated here.
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

# Installs the Chromium binary AND its OS-level dependencies. This is
# the step that was missing project-wide -- meesho_connector.py's own
# error message (session.py) already tells the operator to run
# `playwright install chromium` if this wasn't done.
RUN playwright install --with-deps chromium

COPY . .

# selleros.db (sqlite) and the Chroma knowledge-base vector store both
# write to disk at runtime -- mount a volume over /app/data in
# docker-compose.yml (or your orchestrator) so they survive a restart.
RUN mkdir -p /app/data
ENV DATABASE_URL=sqlite:////app/data/selleros.db

EXPOSE 8000

# Liveness/readiness probes already exist at /health and /health/ready
# (backend/main.py) -- point your orchestrator's health checks there.
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
