import { spawnSync } from "node:child_process";
import { existsSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import openapiTS, { astToString } from "openapi-typescript";

const frontendRoot = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const backendRoot = resolve(frontendRoot, "../backend");
const generatedPath = resolve(frontendRoot, "shared/src/contracts/api.generated.ts");
const pythonCandidates = [
  resolve(backendRoot, ".venv/bin/python"),
  resolve(backendRoot, ".venv/Scripts/python.exe"),
  "python",
  "python3",
];
const python = pythonCandidates.find((candidate) => candidate === "python" || candidate === "python3" || existsSync(candidate));

function loadOpenApiSchema() {
  const result = spawnSync(
    python,
    ["-c", "import json; from app.main import app; print(json.dumps(app.openapi()))"],
    { cwd: backendRoot, encoding: "utf8" },
  );

  if (result.status !== 0) {
    throw new Error(`Unable to export FastAPI OpenAPI schema.\n${result.stderr}`);
  }

  return JSON.parse(result.stdout);
}

function formatGeneratedContracts(source) {
  return [
    "// Generated from backend/app/main.py. Do not edit by hand.",
    "// Run `npm run contracts:generate` from frontend/ after changing the API schema.",
    "",
    source.trim(),
    "",
  ].join("\n");
}

const schema = loadOpenApiSchema();
const generated = formatGeneratedContracts(astToString(await openapiTS(schema, { alphabetize: true })));

if (process.argv.includes("--check")) {
  const current = existsSync(generatedPath) ? readFileSync(generatedPath, "utf8") : "";
  if (current !== generated) {
    console.error("Generated API contracts are stale. Run `npm run contracts:generate`.");
    process.exit(1);
  }
  console.log("Generated API contracts match FastAPI OpenAPI.");
} else {
  writeFileSync(generatedPath, generated);
  console.log(`Generated ${generatedPath}`);
}
