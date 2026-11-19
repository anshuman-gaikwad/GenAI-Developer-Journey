from pathlib import Path

import requests

# Project folder
BASE_DIR = Path(__file__).resolve().parent.parent

# Raw data folder
RAW_DIR = BASE_DIR / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

# Official Government PDF documents
documents = [
    {
        "name": "consumer_protection_act_2019.pdf",
        "url": "https://consumeraffairs.gov.in/public/upload/files/CP%20Act%202019_1732700731.pdf",
    },
    {
        "name": "ecommerce_rules_2020.pdf",
        "url": "https://consumeraffairs.gov.in/public/upload/files/E%20commerce%20rules_1732703966.pdf",
    },
    {
        "name": "ecommerce_amendment_rules_2021.pdf",
        "url": "https://consumeraffairs.gov.in/public/upload/files/Consumer%20Protection%20%28E-Commerce%29%20%28Amendment%29%20Rules%2C%202021_1732704241.pdf",
    },
]


def download_documents():

    for document in documents:
        file_path = RAW_DIR / document["name"]

        try:
            print("\nDownloading:", document["name"])

            response = requests.get(document["url"], timeout=30)

            response.raise_for_status()

            # Check PDF format
            if not response.content.startswith(b"%PDF"):
                raise ValueError("Downloaded file is not a valid PDF")

            # Save PDF
            with open(file_path, "wb") as file:
                file.write(response.content)

            print("Download successful:", document["name"])

        except requests.exceptions.Timeout:
            print("Download timeout:", document["name"])

        except requests.exceptions.RequestException as error:
            print("Download error:", error)

        except (ValueError, OSError) as error:
            print("File error:", error)


if __name__ == "__main__":
    download_documents()
