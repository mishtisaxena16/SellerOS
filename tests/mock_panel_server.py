"""
Mock Seller Hub / Supplier Panel server — NOT a substitute for testing
against the real Flipkart/Meesho sites (the actual CSS selectors used
in flipkart_playwright_connector.py / meesho_connector.py remain
genuinely unverified against those, and no amount of local mocking
changes that). What this DOES let me verify for real: the connector's
own *mechanics* — login flow, row extraction via data-* attributes,
pagination click-through, rate-limit detection, error propagation —
using the exact same SELECTORS dict the real connector uses, driven by
a real headless Chromium instance, not just read-through code review.
"""
import http.server
import threading
import urllib.parse

ORDERS_PER_PAGE = 3
TOTAL_PAGES = 3


def _orders_page_html(page: int) -> str:
    rows = ""
    for i in range(ORDERS_PER_PAGE):
        order_num = (page - 1) * ORDERS_PER_PAGE + i + 1
        rows += (
            f'<div data-testid="order-row" data-order-id="ORD-{order_num:04d}" '
            f'data-status="shipped" style="display:block;min-height:20px;">Order ORD-{order_num:04d}</div>\n'
        )
    next_button = ""
    if page < TOTAL_PAGES:
        next_button = f'<a data-testid="pagination-next" href="/dash/orders?p={page + 1}">Next</a>'
    return f"""<html><body>
        <h1>Orders — page {page}</h1>
        {rows}
        {next_button}
    </body></html>"""


class MockPanelHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass  # keep test output quiet

    def _send_html(self, html: str):
        body = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)

        if parsed.path == "/login":
            self._send_html("""<html><body>
                <form method="POST" action="/do-login">
                    <input name="loginId" />
                    <input name="username" />
                    <input type="password" name="password" />
                    <button type="submit">Login</button>
                </form>
            </body></html>""")
        elif parsed.path in ("/dash", "/panel", "/dash/panel"):
            self._send_html("<html><body><h1>Dashboard home</h1></body></html>")
        elif parsed.path in ("/dash/orders", "/panel/orders"):
            page = int(params.get("p", ["1"])[0])
            if params.get("status", [""])[0] == "rate_limited_test":
                self._send_html('<html><body><div>Sorry, too many requests right now.</div></body></html>')
                return
            self._send_html(_orders_page_html(page))
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == "/do-login":
            # Real login forms redirect after POST; simulate that via a
            # client-side meta-refresh so Playwright's page.click() +
            # wait_for_url(".../dash") sees a real navigation, same as
            # a real 302 would produce.
            length = int(self.headers.get("Content-Length", 0))
            self.rfile.read(length)
            self._send_html('<html><head><meta http-equiv="refresh" content="0;url=/dash/panel"></head><body></body></html>')
        else:
            self.send_response(404)
            self.end_headers()


def start_mock_server(port: int) -> threading.Thread:
    server = http.server.ThreadingHTTPServer(("127.0.0.1", port), MockPanelHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread
