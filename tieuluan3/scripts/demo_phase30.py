"""Offline Chapter5 demo; never opens a benchmark evaluator or modifies artifacts."""

import argparse
import json

from src.ch05_knowledge_rag.service import DATASETS, KgRagService, sample_request
from src.ch05_knowledge_rag.structural import inspect_entity


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", choices=DATASETS, required=True)
    parser.add_argument("--question")
    parser.add_argument("--qid", default="Q12206")
    args = parser.parse_args()
    if args.dataset == DATASETS[2]:
        result = inspect_entity(args.qid)
    else:
        request = sample_request(args.dataset)
        if args.question is not None:
            request["input"]["text"] = args.question
        result = KgRagService().compare(request)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
