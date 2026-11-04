"""Run local A0/A1/A2 on record-bound TRAIN demo; never a benchmark/TEST executor."""

import argparse
import json

from threadpoolctl import threadpool_limits

from scripts.phase31_benchmark import load_inputs
from src.ch06_multi_agent.core import DOMAINS
from src.ch06_multi_agent.executor import ProcessExecutor
from src.ch06_multi_agent.service import AgentService, sample_request
from src.ch06_multi_agent.tools import ToolCatalog


def demo(domain, question=None):
    view, catalog, _ = load_inputs()
    service = AgentService(ProcessExecutor(ToolCatalog(catalog).call), view["taskset"]["sha256"])
    request = sample_request(domain)
    if question is not None:
        request["question"] = question
    with threadpool_limits(limits=1):
        return service.compare(request)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--domain", choices=DOMAINS, required=True)
    parser.add_argument("--question")
    args = parser.parse_args()
    print(json.dumps(demo(args.domain, args.question), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
