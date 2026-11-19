"""
chunking.py - GrahakNyay Day 07

Reads PDF and TXT documents and splits them into chunks.
Keeps document title, source, and page number.
"""

import hashlib
from pathlib import Path

from pypdf import PdfReader

BASE_DIR = Path(__file__).resolve().parent.parent

DOCUMENT_FOLDERS = [BASE_DIR / "docs", BASE_DIR / "data" / "raw"]

CHUNK_SIZE = 250
CHUNK_OVERLAP = 40


def get_documents():
    """Find PDF and TXT files in the document folders."""

    files = []

    for folder in DOCUMENT_FOLDERS:
        if folder.exists():
            files.extend(folder.rglob("*.pdf"))
            files.extend(folder.rglob("*.txt"))

    # Remove duplicate paths.
    unique_files = {file.resolve(): file.resolve() for file in files}

    return sorted(unique_files.values())


def read_document(file_path):
    """Read a document page by page."""

    pages = []

    if file_path.suffix.lower() == ".pdf":
        reader = PdfReader(str(file_path))

        title = (
            reader.metadata.title
            if reader.metadata and reader.metadata.title
            else file_path.stem
        )

        for page_number, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""

            if text.strip():
                pages.append(
                    {
                        "title": title,
                        "source": file_path.name,
                        "page": page_number,
                        "text": text,
                    }
                )

    elif file_path.suffix.lower() == ".txt":
        text = file_path.read_text(encoding="utf-8")

        if text.strip():
            pages.append(
                {
                    "title": file_path.stem,
                    "source": file_path.name,
                    "page": 1,
                    "text": text,
                }
            )

    return pages


def split_into_chunks(text):
    """Split text into overlapping word-based chunks."""

    words = text.split()
    chunks = []

    start = 0

    while start < len(words):
        end = start + CHUNK_SIZE

        chunk_text = " ".join(words[start:end])

        if chunk_text.strip():
            chunks.append(chunk_text)

        if end >= len(words):
            break

        start = end - CHUNK_OVERLAP

    return chunks


def chunk_documents():
    """Read all documents and return chunks with metadata."""

    all_chunks = []

    for file_path in get_documents():
        try:
            pages = read_document(file_path)

            for page_data in pages:
                text_chunks = split_into_chunks(page_data["text"])

                for index, chunk_text in enumerate(text_chunks, start=1):
                    unique_text = (
                        f"{page_data['source']}-"
                        f"{page_data['page']}-"
                        f"{index}-"
                        f"{chunk_text}"
                    )

                    chunk_id = hashlib.sha256(unique_text.encode("utf-8")).hexdigest()

                    all_chunks.append(
                        {
                            "id": chunk_id,
                            "text": chunk_text,
                            "title": page_data["title"],
                            "source": page_data["source"],
                            "page": page_data["page"],
                        }
                    )

        except Exception as error:  # noqa: BLE001
            print(f"Could not process {file_path.name}: {error}")

    return all_chunks


if __name__ == "__main__":
    chunks = chunk_documents()

    print("Total chunks:", len(chunks))

    for chunk in chunks[:3]:
        print("\nTitle:", chunk["title"])
        print("Source:", chunk["source"])
        print("Page:", chunk["page"])
        print("Text:", chunk["text"][:200])
