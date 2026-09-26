"""
Upload every file of a folder in one go (replaces v1's build_index.py).
Useful to load demo documents without clicking in the web page.
    python -m scripts.upload_folder samples
"""
import os
import sys

from app.ingest import UploadError, ingest_file


def main():
    folder = sys.argv[1] if len(sys.argv) > 1 else "samples"

    for filename in sorted(os.listdir(folder)):
        path = os.path.join(folder, filename)
        if not os.path.isfile(path) or filename.startswith("."):
            continue

        with open(path, "rb") as f:
            content = f.read()
        try:
            document = ingest_file(filename, content)
            print(f"OK   {filename}: {document['pages']} pages, {document['chunks']} chunks")
        except UploadError as error:
            print(f"SKIP {filename}: {error.message}")


if __name__ == "__main__":
    main()