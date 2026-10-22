"""Small read-only diagnostics for V3 source schemas; never evaluate TEST."""

import argparse
import json
import tarfile

from src.common.contracts import ROOT
from src.common.eda_sources import load_series, source


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cifar-labels", action="store_true")
    args = parser.parse_args()
    if args.cifar_labels:
        path = ROOT / source("ch3_cifar10")["contract"]["files"][0]["path"]
        with (
            tarfile.open(path, "r:gz") as archive,
            archive.extractfile("cifar-10-batches-bin/batches.meta.txt") as stream,
        ):
            text = stream.read(4096).decode("utf-8")
        print(json.dumps({"text_repr": repr(text), "lines": text.splitlines()}))
        return
    for dataset in ("ch4_gold_pink_sheet", "ch4_bis_house_prices", "ch4_household_power"):
        frame, features, audit = load_series(dataset)
        print(
            json.dumps(
                {
                    "dataset": dataset,
                    "shape": list(frame.shape),
                    "features": features,
                    "start": str(frame.time.min()),
                    "end": str(frame.time.max()),
                    "series": frame.series.nunique(),
                    "target_missing": int(frame.target.isna().sum()),
                    "audit": audit,
                },
                default=str,
            ),
            flush=True,
        )


if __name__ == "__main__":
    main()
