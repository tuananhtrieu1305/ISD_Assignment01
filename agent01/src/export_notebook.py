"""Export executed notebook cells for genuine browser screenshots without syntax colors."""

import json
from pathlib import Path

import nbformat
from nbconvert import HTMLExporter

BASE = Path(__file__).resolve().parent


def main():
    notebook = nbformat.read(BASE / "notebooks/Discovering_AI_Agent.ipynb", as_version=4)
    code = [cell for cell in notebook.cells if cell.cell_type == "code"]
    if any(not cell.execution_count or not cell.outputs for cell in code):
        raise ValueError("Every cell must have actual execution and outputs")
    if any(output.output_type == "error" for cell in code for output in cell.outputs):
        raise ValueError("Notebook contains execution error")
    exporter = HTMLExporter(template_name="classic")
    html, _ = exporter.from_notebook_node(notebook)
    css = """<style>
    html,body,#notebook,#notebook-container { background:#fff!important;
      box-shadow:none!important; color:#000!important; margin:0!important;
      padding:0!important; width:1060px!important; }
    * { color:#000!important; text-shadow:none!important; }
    a {text-decoration:none!important;}
    .cell {box-sizing:border-box!important; width:1060px!important; padding:12px 10px!important;
      filter:grayscale(1)!important;}
    .input_area {background:#fff!important; border:1px solid #000!important; border-radius:0!important;}
    .highlight,.highlight pre,.output_area,.output_subarea {background:#fff!important;}
    .input_area pre {font:20px/1.3 Consolas,"Liberation Mono",monospace!important;
      white-space:pre-wrap!important; overflow-wrap:anywhere!important; padding:12px!important;}
    .output_subarea pre {font:19px/1.3 Consolas,"Liberation Mono",monospace!important;
      white-space:pre-wrap!important; overflow-wrap:anywhere!important; padding:8px 0!important;}
    .prompt {min-width:60px!important; width:60px!important; padding:12px 4px!important;
      font:17px/1.3 Consolas,monospace!important;}
    .output_subarea {max-width:none!important; overflow:hidden!important;}
    .output_png img {width:auto!important;max-width:560px!important;height:auto!important;}
    </style>"""
    html = html.replace("</head>", css + "</head>")
    folder = BASE / "evidence/notebook_browser"
    folder.mkdir(parents=True, exist_ok=True)
    destination = folder / "executed_notebook.html"
    destination.write_text(html, encoding="utf-8")
    print(json.dumps({"html": str(destination), "executed_code_cells": len(code)}))


if __name__ == "__main__":
    main()
