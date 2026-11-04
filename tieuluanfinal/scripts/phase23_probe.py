"""Small local source-structure diagnostic, never writes datasets."""

import argparse
import gzip
import time
import zipfile
from pathlib import Path

import openpyxl
import pandas as pd
import requests

from src.common.contracts import ROOT


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--network-diagnostic", action="store_true")
    parser.add_argument("--download-progress", action="store_true")
    args = parser.parse_args()
    if args.download_progress:
        for path in (ROOT / "data/raw/ch3/cifar10").glob("*.part"):
            total = path.stat().st_size
            ends = []
            with path.open("rb") as handle:
                for offset in range(0, total, 4 * 1024**2):
                    handle.seek(min(offset + 4 * 1024**2, total) - 64)
                    ends.append(any(handle.read(64)))
            print(
                path.name, "logical_bytes", total, "nonzero_block_ends", sum(ends), "/", len(ends), flush=True
            )
        return
    with gzip.open(ROOT / "artifacts/manifests/phase20/before-files.csv.gz", "rt") as handle:
        print("baseline_header", handle.readline().strip(), flush=True)
    if args.network_diagnostic:
        url = "https://cave.cs.toronto.edu/kriz/cifar-10-binary.tar.gz"
        start = time.monotonic()
        with requests.get(url, headers={"Range": "bytes=0-65535"}, stream=True, timeout=(15, 30)) as response:
            print("range_response", response.status_code, dict(response.headers), flush=True)
            block = next(response.iter_content(65536))
            print("range_bytes", len(block), "seconds", time.monotonic() - start, flush=True)
        return
    for name in (
        "ch2/bank/bank_marketing.zip",
        "ch4/bis/WS_SPP_csv_col.zip",
        "ch4/gold/CMO-Historical-Data-Monthly.xlsx",
    ):
        path = ROOT / "data/raw" / name
        if not path.exists():
            print(name, "not downloaded yet", flush=True)
            continue
        with zipfile.ZipFile(path) as archive:
            print(name, archive.namelist()[:8], flush=True)
            for member in archive.namelist():
                if member.endswith(".csv"):
                    frame = pd.read_csv(archive.open(member), nrows=3)
                    print("CSV", frame.shape, list(frame.columns[:25]), list(frame.columns[-8:]), flush=True)
                    print(frame.iloc[:, :10].to_dict("records"), flush=True)
        if Path(name).suffix == ".xlsx":
            workbook = openpyxl.load_workbook(path, read_only=True, data_only=True)
            print("sheets", workbook.sheetnames, flush=True)
            sheet = workbook["Monthly Prices"]
            rows = list(sheet.values)
            print("Monthly Prices", [str(row[0]) for row in rows[:9]], flush=True)
            workbook.close()


if __name__ == "__main__":
    main()
