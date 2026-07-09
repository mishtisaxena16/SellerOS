import os
import subprocess
import chromadb

from chunking import clean_text, semantic_chunk
from embedding import get_embedding

# =========================
# Clone / Update Repository
# =========================

REPO_URL = "https://github.com/mishtisaxena16/SellerOS.git"
LOCAL_PATH = "./SellerOS"

if not os.path.exists(LOCAL_PATH):
    print("Cloning repository...")
    subprocess.run(
        ["git", "clone", REPO_URL, LOCAL_PATH],
        check=True
    )
else:
    print("Updating repository...")
    subprocess.run(
        ["git", "-C", LOCAL_PATH, "pull"],
        check=True
    )

# =========================
# ChromaDB Setup
# =========================

client = chromadb.PersistentClient(
    path="./chroma_db"
)

collection = client.get_or_create_collection(
    name="selleros_docs"
)

# =========================
# Repository Settings
# =========================

REPO_PATH =  os.path.join(
    LOCAL_PATH,
    "knowledge"
)

IGNORE_DIRS = {
    ".git",
    "_pycache_",
    "node_modules",
    ".venv",
    "venv"
}

documents_loaded = 0
chunks_loaded = 0

# =========================
# Read Repository Files
# =========================

for root, dirs, files in os.walk(REPO_PATH):

    dirs[:] = [
        d for d in dirs
        if d not in IGNORE_DIRS
    ]

    for file in files:

        # Index only markdown files
        if not file.endswith(".md"):
            continue

        filepath = os.path.join(root, file)

        try:

            with open(
                filepath,
                "r",
                encoding="utf-8",
                errors="ignore"
            ) as f:

                content = f.read()

            if not content.strip():
                continue

            content = clean_text(content)

            chunks = semantic_chunk(content)

            # -------------------------
            # Generate Metadata
            # -------------------------

            # Folder name (amazon, gst, meesho, etc.)
            platform = os.path.basename(
                os.path.dirname(filepath)
            )

            # Remove .md extension
            module = os.path.splitext(file)[0]

            # Remove numeric prefix
            # Example:
            # 01_seller_onboarding -> seller_onboarding
            if "_" in module:
                module = module.split("_", 1)[1]

            for idx, chunk in enumerate(chunks):

                if not chunk.strip():
                    continue

                embedding = get_embedding(chunk)

                if embedding is None:
                    print(
                        f"Embedding failed for {filepath}"
                    )
                    continue

                chunk_id = f"{platform}{module}{idx}"

                collection.upsert(
                    ids=[chunk_id],
                    documents=[chunk],
                    embeddings=[embedding],
                    metadatas=[{
                        "platform": platform,
                        "module": module,
                        "source": file,
                        "chunk": idx
                    }]
                )

                chunks_loaded += 1

            documents_loaded += 1

            print(f"Indexed: {filepath}")

        except Exception as e:

            print(
                f"Error processing {filepath}"
            )

            print(e)

# =========================
# Summary
# =========================

print("\n===== SUMMARY =====")

print(
    f"Markdown Files Indexed: {documents_loaded}"
)

print(
    f"Total Chunks Indexed: {chunks_loaded}"
)

print(
    f"Total Chunks in ChromaDB: {collection.count()}"
)

print("Knowledge Base Indexed Successfully")