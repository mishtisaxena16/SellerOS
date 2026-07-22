from pathlib import Path

from ingest import IngestionPipeline


FAILED_FILES = [
    r"C:\Users\vasvi\OneDrive\Documents\programming\Marketsellers\SellerOS\knowledge\meesho\14. FAQs_corpus.md",
    r"C:\Users\vasvi\OneDrive\Documents\programming\Marketsellers\SellerOS\knowledge\meesho\7. image_guide.md",
]


pipeline = IngestionPipeline()

for file_path in FAILED_FILES:

    print("\n" + "=" * 80)

    try:
        chunks = pipeline.ingest_document(
            Path(file_path)
        )

        print(
            f"SUCCESS: {file_path}"
        )
        print(
            f"Inserted {chunks} chunks"
        )

    except Exception as e:

        print(
            f"FAILED: {file_path}"
        )
        print(
            f"Reason: {e}"
        )
