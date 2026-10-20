import { copyFile, cp, mkdir } from "node:fs/promises";
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

await copyFile(
  path.join(appRoot, "node_modules", "katex", "dist", "katex.min.css"),
  path.join(bundleDir, "katex.min.css"),
);
await cp(
  path.join(appRoot, "node_modules", "katex", "dist", "fonts"),
  path.join(bundleDir, "fonts"),
  { recursive: true },
);

console.log("Built bundle/app.js, PDF worker, KaTeX stylesheet, and math fonts.");
