#!/usr/bin/env python3
"""Download Vosk PT-BR model used by Jarvis offline assistant."""

import os
import urllib.request
import zipfile

MODEL_ZIP_URL = "https://alphacephei.com/vosk/models/vosk-model-small-pt-0.3.zip"
ZIP_NAME = "vosk-model-small-pt-0.3.zip"
MODEL_DIR = "vosk-model-small-pt-0.3"


def main() -> None:
    if os.path.isdir(MODEL_DIR):
        print(f"Modelo ja existe: {MODEL_DIR}")
        return

    print("[DOWNLOAD] Baixando modelo PT-BR...")
    urllib.request.urlretrieve(MODEL_ZIP_URL, ZIP_NAME)

    print("[DOWNLOAD] Extraindo...")
    with zipfile.ZipFile(ZIP_NAME, "r") as zf:
        zf.extractall(".")

    os.remove(ZIP_NAME)
    print("[DOWNLOAD] Concluido.")


if __name__ == "__main__":
    main()
