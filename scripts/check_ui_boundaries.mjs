import fs from "node:fs";
import path from "node:path";

const repoRoot = path.resolve(import.meta.dirname, "..");
const featuresRoot = path.join(repoRoot, "ui", "src", "features");
const importPattern =
  /\b(?:import|export)\s+(?:type\s+)?(?:[^"'`]+?\s+from\s+)?["']([^"']+)["']/g;

function collectFiles(dir) {
  const entries = fs.readdirSync(dir, { withFileTypes: true });
  const files = [];

  for (const entry of entries) {
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      files.push(...collectFiles(fullPath));
      continue;
    }
    if (/\.(ts|tsx)$/.test(entry.name)) {
      files.push(fullPath);
    }
  }

  return files;
}

function featureNameFor(filePath) {
  const relative = path.relative(featuresRoot, filePath);
  const [featureName] = relative.split(path.sep);
  return featureName;
}

function isCrossFeatureInternalImport(featureName, importPath) {
  if (!importPath.startsWith("../") || importPath.startsWith("../../")) {
    return false;
  }

  const segments = importPath.split("/");
  const targetFeature = segments[1];
  if (!targetFeature || targetFeature === featureName) {
    return false;
  }

  return segments.length > 2 && segments[2] !== "index";
}

const violations = [];

for (const filePath of collectFiles(featuresRoot)) {
  const featureName = featureNameFor(filePath);
  const relativePath = path.relative(repoRoot, filePath);
  const source = fs.readFileSync(filePath, "utf8");

  for (const match of source.matchAll(importPattern)) {
    const importPath = match[1];
    if (isCrossFeatureInternalImport(featureName, importPath)) {
      violations.push(`${relativePath}: ${importPath}`);
    }
  }
}

if (violations.length) {
  console.error("Cross-feature internal imports are not allowed:");
  for (const violation of violations) {
    console.error(`- ${violation}`);
  }
  process.exit(1);
}

console.log("UI feature boundaries are clean.");
