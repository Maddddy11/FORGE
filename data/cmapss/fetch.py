"""
Download and extract NASA CMAPSS Jet Engine Simulated Data.

Run from the repo root:
    python data/cmapss/fetch.py

Saves raw files to data/cmapss/raw/:
    train_FD001.txt  test_FD001.txt  RUL_FD001.txt  (and FD002-FD004)
"""
import sys
import urllib.request
import zipfile
from pathlib import Path

RAW_DIR = Path(__file__).parent / "raw"

# Files needed (we use FD001; others are downloaded for completeness)
_FILES = [
    "train_FD001.txt", "test_FD001.txt", "RUL_FD001.txt",
    "train_FD002.txt", "test_FD002.txt", "RUL_FD002.txt",
    "train_FD003.txt", "test_FD003.txt", "RUL_FD003.txt",
    "train_FD004.txt", "test_FD004.txt", "RUL_FD004.txt",
]

# Mirror base URLs (tried in order per file)
_MIRROR_BASES = [
    "https://raw.githubusercontent.com/hankroark/Turbofan-Engine-Degradation/master/CMAPSSData",
    "https://raw.githubusercontent.com/schwxd/CADA/master/dataset/CMAPSS",
]


def _download_file(filename: str, dest: Path) -> bool:
    for base in _MIRROR_BASES:
        url = f"{base}/{filename}"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                content = resp.read()
            if b"404" in content[:50] or len(content) < 100:
                continue
            dest.write_bytes(content)
            return True
        except Exception:
            continue
    return False


def fetch() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    missing = [f for f in _FILES if not (RAW_DIR / f).exists()]
    if not missing:
        print(f"All CMAPSS files already present in {RAW_DIR}")
        return

    print(f"Downloading {len(missing)} CMAPSS file(s)…")
    failed = []
    for filename in missing:
        dest = RAW_DIR / filename
        print(f"  {filename}…", end=" ", flush=True)
        if _download_file(filename, dest):
            print(f"OK ({dest.stat().st_size // 1024} KB)")
        else:
            print("FAILED")
            failed.append(filename)

    if failed:
        print(
            f"\n{len(failed)} file(s) could not be downloaded: {failed}\n"
            "\nManual download instructions:\n"
            "  1. Visit https://data.nasa.gov/dataset/CMAPSS-Jet-Engine-Simulated-Data/ff5v-kuh6\n"
            "  2. Download CMAPSSData.zip and extract the .txt files\n"
            f"  3. Place them in: {RAW_DIR}\n"
        )
        if "train_FD001.txt" in failed:
            sys.exit(1)
        print("Continuing — train_FD001.txt is present.")
    else:
        print(f"\nAll files saved to {RAW_DIR}")


if __name__ == "__main__":
    fetch()
