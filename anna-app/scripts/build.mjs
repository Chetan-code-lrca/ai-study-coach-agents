import { copyFile, mkdir } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { build } from "esbuild";

const appRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const bundleDir = path.join(appRoot, "bundle");
await mkdir(bundleDir, { recursive: true });

await build({
  absWorkingDir: appRoot,
  entryPoints: ["src/app.js"],
  outfile: "bundle/app.js",
  bundle: true,
  minify: true,
  sourcemap: false,
  format: "esm",
  platform: "browser",
  target: ["es2022"],
  external: ["/static/anna-apps/_sdk/latest/index.js"],
  logLevel: "info",
});

await copyFile(
  path.join(appRoot, "node_modules", "pdfjs-dist", "build", "pdf.worker.min.mjs"),
  path.join(bundleDir, "pdf.worker.min.mjs"),
);

console.log("Built bundle/app.js and copied bundle/pdf.worker.min.mjs.");
