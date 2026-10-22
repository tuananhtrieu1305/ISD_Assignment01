import fs from "node:fs/promises";
import path from "node:path";
import { pathToFileURL } from "node:url";

const [inputPath, outputPath, artifactToolPackage] = process.argv.slice(2);
if (!inputPath || !outputPath || !artifactToolPackage) {
  throw new Error(
    "usage: node extract_docx_layout.mjs <input.docx> <output.json> <artifact-tool-package>"
  );
}

const artifactTool = await import(
  pathToFileURL(path.join(artifactToolPackage, "dist", "artifact_tool.mjs")).href
);
const model = await artifactTool.DocumentFile.importDocx(
  await artifactTool.FileBlob.load(path.resolve(inputPath))
);
const canvas = new OffscreenCanvas(1, 1);
const context = canvas.getContext("2d");
if (!context) {
  throw new Error("Canvas 2D context is unavailable");
}
const pages = artifactTool.drawDocumentToCtx(model, context, { pageIndex: 0 }).pages;
const fragments = artifactTool.collectRenderedDocumentTextFragments(pages);
const payload = {
  renderer: "artifact-tool-layout",
  inputPath: path.resolve(inputPath),
  pageCount: pages.length,
  pages: pages.map((page, index) => ({
    pageIndex: index,
    widthPx: page.widthPx,
    heightPx: page.heightPx,
  })),
  fragments,
};
await fs.mkdir(path.dirname(path.resolve(outputPath)), { recursive: true });
await fs.writeFile(outputPath, JSON.stringify(payload, null, 2), "utf8");
console.log(`Extracted ${fragments.length} text fragments across ${pages.length} pages.`);
