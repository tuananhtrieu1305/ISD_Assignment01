"""Create and execute an independent, self-contained notebook using the pinned kernel."""

import ast
import inspect
import json
import os
import sys
import textwrap
from pathlib import Path

import nbformat
from jupyter_client import KernelManager
from nbclient import NotebookClient

from discovering_ai_agent import experiment as ex

BASE = Path(__file__).resolve().parent


def function_code(*functions):
    return "\n\n".join(inspect.getsource(function).strip() for function in functions)


def make():
    tree = ast.parse(Path(ex.__file__).read_text())
    constants = "\n".join(
        ast.get_source_segment(Path(ex.__file__).read_text(), node)
        for node in tree.body if isinstance(node, ast.Assign)
    )
    cells = [
        ("Khởi tạo và mê cung", """import json, platform
from collections import deque
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
%matplotlib inline

plt.rcParams.update({"text.color": "black", "axes.labelcolor": "black",
                     "xtick.color": "black", "ytick.color": "black",
                     "font.size": 12, "figure.facecolor": "white"})
""" + constants + """
print("Python:", platform.python_version(), "| NumPy:", np.__version__)
print("Maze:", MAZE.shape, "| Free cells:", int((MAZE == 0).sum()))
print("Start:", START, "| Goal:", GOAL, "| Q shape:", MAZE.shape + (4,))
"""),
        ("Môi trường và phản hồi", function_code(ex.valid, ex.transition) + """
print("Down from start:", transition(MAZE, START, 3, GOAL))
print("Wall from start:", transition(MAZE, START, 1, GOAL))
print("Goal transition:", transition(MAZE, (9, 8), 1, GOAL))
"""),
        ("Chọn hành động và cập nhật Q", function_code(ex.choose_action, ex.update_q) + """
probe = np.zeros((10, 10, 4))
update_q(probe, (9, 8), 1, GOAL, 50, True)
print("Terminal update with alpha=0.1:", probe[9, 8, 1])
print("alpha=0.1 | gamma=0.9 | epsilon: 0.5 -> 0.01")
"""),
        ("Huấn luyện có seed và giới hạn bước", function_code(ex.train) + """
result = train(episodes=5000, seed=42, max_steps=400)
Q = result["q"]
for left in (0, 1000, 4000):
    right = left + 1000
    success = result["successes"][left:right].mean()
    mean_return = result["returns"][left:right].mean()
    print(f"Episodes {left+1:4d}-{right}: success={success:.1%}, return={mean_return:.2f}")
print("Final epsilon:", result["epsilon"], "| Truncated:", result["truncated"])
"""),
        ("Đánh giá chính sách greedy", function_code(ex.greedy_path) + """
path, status = greedy_path(MAZE, Q, START, GOAL)
print("Greedy status:", status, "| Moves:", len(path) - 1)
print("Learned route:", path)
"""),
        ("BFS chỉ làm đối chứng sau huấn luyện", function_code(ex.shortest_path, ex.valid_path) + """
reference = shortest_path(MAZE, START, GOAL)
assert status == "goal" and valid_path(MAZE, path)
assert len(path) == len(reference)
print("BFS minimum moves:", len(reference) - 1)
print("Valid route:", valid_path(MAZE, path), "| Same length:", len(path) == len(reference))
print("Greedy undiscounted return:", 50 - (len(path) - 2))
"""),
        ("Đường đi học được", """fig, ax = plt.subplots(figsize=(5, 4.6), dpi=130)
ax.imshow(MAZE, cmap=ListedColormap(["white", "0.7"]), vmin=0, vmax=1)
rows, columns = zip(*path)
ax.plot(columns, rows, color="black", linewidth=2)
ax.scatter(START[1], START[0], marker="o", s=90,
           facecolors="white", edgecolors="black", zorder=4)
ax.scatter(GOAL[1], GOAL[0], marker="*", s=180, color="black", zorder=4)
ax.set(xticks=range(10), yticks=range(10), xlabel="Column", ylabel="Row")
ax.set_title("Learned route   S start   G goal")
ax.text(START[1]+0.25, START[0], "S", color="black")
ax.text(GOAL[1]-0.7, GOAL[0], "G", color="black")
fig.tight_layout()
plt.show()
"""),
        ("Phần thưởng trong quá trình học", """fig, ax = plt.subplots(figsize=(7, 3.1), dpi=130)
returns = result["returns"]
ax.plot(np.arange(1, 5001), returns, color="0.75", linewidth=0.5,
        label="Each episode")
rolling = np.convolve(returns, np.ones(100)/100, mode="valid")
ax.plot(np.arange(100, 5001), rolling, color="black", linewidth=1.5,
        label="Mean over 100 episodes")
ax.set(xlabel="Episode", ylabel="Undiscounted return",
       title="Q learning on the fixed maze")
ax.legend(frameon=False)
fig.tight_layout()
plt.show()
"""),
        ("Kết quả kiểm chứng", """summary = {
    "seed": 42, "episodes": 5000, "q_shape": list(Q.shape),
    "free_cells": int((MAZE == 0).sum()), "greedy_status": status,
    "learned_moves": len(path)-1, "bfs_moves": len(reference)-1,
    "valid_route": valid_path(MAZE, path),
    "greedy_return": 50-(len(path)-2),
    "last_1000_success_rate": float(result["successes"][-1000:].mean()),
    "last_1000_mean_return": float(result["returns"][-1000:].mean()),
    "truncated_episodes": int(result["truncated"]),
    "execution_device": "CPU NumPy", "path": path,
}
print(json.dumps(summary))
"""),
    ]
    notebook = nbformat.v4.new_notebook()
    notebook.cells = [nbformat.v4.new_markdown_cell(
        "# DISCOVERING AI Agent\n\n"
        "Q-learning maze adapted from https://www.geeksforgeeks.org/machine-learning/what-is-reinforcement-learning/ .\n\n"
        "The maze, rewards and learning schedule follow the article. This notebook adds seed42, "
        "a 400-step safety limit, strict greedy evaluation and an independent BFS comparison. "
        "BFS is never used to train or modify Q. All code cells are self-contained. "
        "CPU NumPy is sufficient; this notebook is independent of the six-chapter V3 project."
    )]
    for title, code in cells:
        notebook.cells.append(nbformat.v4.new_markdown_cell("## " + title))
        notebook.cells.append(nbformat.v4.new_code_cell(textwrap.dedent(code).strip()))
    notebook.metadata.kernelspec = {"display_name": "Python 3.11 pinned WSL", "language": "python", "name": "python3"}
    destination = BASE / "notebooks/Discovering_AI_Agent.ipynb"
    destination.parent.mkdir(parents=True, exist_ok=True)
    nbformat.write(notebook, destination)
    manager = KernelManager(kernel_name="python3")
    manager.kernel_spec.argv = [sys.executable, "-m", "ipykernel_launcher", "-f", "{connection_file}"]
    client = NotebookClient(notebook, km=manager, timeout=180,
                            resources={"metadata": {"path": str(BASE)}}, allow_errors=False)
    try:
        client.execute(env={**os.environ, "CUDA_VISIBLE_DEVICES": "", "PYTHONDONTWRITEBYTECODE": "1"})
    finally:
        if manager.has_kernel:
            manager.shutdown_kernel(now=True)
    nbformat.write(notebook, destination)
    output = "".join(item.get("text", "") for item in notebook.cells[-1].outputs if item.output_type == "stream")
    summary = json.loads(output)
    evidence = BASE / "evidence"
    evidence.mkdir(exist_ok=True)
    (evidence / "results.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"notebook": str(destination), "code_cells": len(cells), "result": summary}, ensure_ascii=False))


if __name__ == "__main__":
    make()
