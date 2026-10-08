import path from "node:path";
import { pathToFileURL } from "node:url";

const [inputPath, outputPath, nodeModulesPath] = process.argv.slice(2);
if (!inputPath || !outputPath || !nodeModulesPath) {
  throw new Error(
    "usage: node convert_svg_to_png.mjs <input.svg> <output.png> <node_modules>"
  );
}
const sharpModule = await import(
  pathToFileURL(path.join(nodeModulesPath, "sharp", "lib", "index.js")).href
);
const sharp = sharpModule.default;
await sharp(path.resolve(inputPath), { density: 240 })
  .png()
  .toFile(path.resolve(outputPath));
console.log(`Converted ${inputPath} -> ${outputPath}`);
