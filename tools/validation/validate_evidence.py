#!/usr/bin/env python3
from pathlib import Path
import json, sys
from jsonschema import Draft202012Validator, FormatChecker

def find_repo_root(start):
    p = Path(start).resolve()
    for candidate in [p] + list(p.parents):
        if (candidate / "FRAMEWORK_MANIFEST.yml").exists():
            return candidate
    raise RuntimeError("Repository root not found")

ROOT = find_repo_root(Path(__file__).parent)
SCHEMA = ROOT / "framework" / "schemas" / "evidence.schema.json"
RESULTS = ROOT / "implementations" / "wazuh" / "tests" / "results"

schema=json.loads(SCHEMA.read_text(encoding="utf-8"))
validator=Draft202012Validator(schema, format_checker=FormatChecker())
errors=[]

files=list(RESULTS.glob("*.evidence.json"))
for p in files:
    doc=json.loads(p.read_text(encoding="utf-8"))
    for e in validator.iter_errors(doc):
        errors.append(f"{p.name}: {e.message}")

if errors:
    print("FAILED")
    for e in errors:
        print("- "+e)
    sys.exit(1)

print(f"OK: validated {len(files)} normalized evidence objects")
