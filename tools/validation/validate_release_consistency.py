#!/usr/bin/env python3
"""
Release-metadata consistency check.

Catches the kind of version/count drift found during the 0.10.0-rc2 review
(reports/WAZUH_IMPLEMENTATION_GAP_ANALYSIS.md, pdp-check.txt): files that
quietly keep an old version label or a stale count after the underlying
framework content moves on. This does not validate legal or technical
correctness -- only that release metadata agrees with itself and with the
framework content it describes.
"""
from pathlib import Path
import sys
import yaml
import json


def find_repo_root(start):
    p = Path(start).resolve()
    for candidate in [p] + list(p.parents):
        if (candidate / "FRAMEWORK_MANIFEST.yml").exists():
            return candidate
    raise RuntimeError("Repository root not found")


ROOT = find_repo_root(Path(__file__).parent)
errors = []


def load_yaml(path):
    return yaml.safe_load((ROOT / path).read_text(encoding="utf-8"))


def load_json(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


VERSION = (ROOT / "VERSION").read_text(encoding="utf-8").strip()

# --- A/E. version consistency across release metadata -----------------
manifest = load_yaml("FRAMEWORK_MANIFEST.yml")
manifest_version = manifest["framework"]["version"]
if manifest_version != VERSION:
    errors.append(
        f"FRAMEWORK_MANIFEST.yml framework.version={manifest_version!r} "
        f"!= VERSION={VERSION!r}"
    )

gates = load_yaml("release/RELEASE_GATES.yml")
if gates.get("framework_version") != VERSION:
    errors.append(
        f"release/RELEASE_GATES.yml framework_version={gates.get('framework_version')!r} "
        f"!= VERSION={VERSION!r}"
    )

compat = load_yaml("release/compatibility/COMPATIBILITY_MATRIX.yml")
compat_version = compat.get("metadata", {}).get("framework_version")
if compat_version != VERSION:
    errors.append(
        f"release/compatibility/COMPATIBILITY_MATRIX.yml metadata.framework_version="
        f"{compat_version!r} != VERSION={VERSION!r}"
    )

coverage_json_path = ROOT / "reports/COVERAGE_REPORT.json"
if coverage_json_path.exists():
    coverage = load_json("reports/COVERAGE_REPORT.json")
    if coverage.get("framework_version") != VERSION:
        errors.append(
            f"reports/COVERAGE_REPORT.json framework_version="
            f"{coverage.get('framework_version')!r} != VERSION={VERSION!r}"
        )
else:
    errors.append("reports/COVERAGE_REPORT.json is missing")

readiness_path = ROOT / f"release/RELEASE_READINESS_{VERSION}.yml"
if not readiness_path.exists():
    errors.append(
        f"No release readiness file for current version: "
        f"release/RELEASE_READINESS_{VERSION}.yml"
    )
else:
    readiness = yaml.safe_load(readiness_path.read_text(encoding="utf-8"))
    if readiness.get("framework_version") != VERSION:
        errors.append(
            f"{readiness_path.relative_to(ROOT)} framework_version="
            f"{readiness.get('framework_version')!r} != VERSION={VERSION!r}"
        )

# --- D. README carries the current version string ---------------------
readme = (ROOT / "README.md").read_text(encoding="utf-8")
if VERSION not in readme:
    errors.append(f"README.md does not mention current VERSION ({VERSION!r})")

# --- C. manifest count consistency -------------------------------------
legal = load_yaml("framework/legal/LEGAL_MAPPING.yml")
controls = load_yaml("framework/controls/CONTROL_CATALOGUE.yml")
reqs = load_yaml("framework/requirements/CONTROL_REQUIREMENTS.yml")
profiles = load_yaml("framework/profiles/CONTROL_PROFILES.yml")
taxonomy = load_yaml("framework/taxonomy/PDP_EVENT_TAXONOMY.yml")
tests = load_yaml("implementations/wazuh/WAZUH_TEST_CATALOGUE.yml")

actual_counts = {
    "legal_requirements": len(legal.get("requirements", [])),
    "controls": len(controls.get("controls", [])),
    "generic_requirements": len(reqs.get("requirements", [])),
    "control_profiles": len(profiles.get("profiles", [])),
    "event_categories": len(taxonomy.get("event_categories", [])),
    "wazuh_tests": len(tests.get("tests", [])),
}
manifest_counts = manifest.get("counts", {})
for key, actual in actual_counts.items():
    declared = manifest_counts.get(key)
    if declared != actual:
        errors.append(
            f"FRAMEWORK_MANIFEST.yml counts.{key}={declared!r} "
            f"but actual count is {actual}"
        )

# --- duplicate ID detection across ID-bearing catalogues ----------------
def find_dupes(items, key="id"):
    seen = {}
    dupes = []
    for item in items:
        v = item.get(key)
        seen[v] = seen.get(v, 0) + 1
    return [k for k, n in seen.items() if n > 1]


for label, items in (
    ("framework/legal/LEGAL_MAPPING.yml requirements", legal.get("requirements", [])),
    ("framework/controls/CONTROL_CATALOGUE.yml controls", controls.get("controls", [])),
    ("framework/requirements/CONTROL_REQUIREMENTS.yml requirements", reqs.get("requirements", [])),
    ("implementations/wazuh/WAZUH_TEST_CATALOGUE.yml tests", tests.get("tests", [])),
):
    dupes = find_dupes(items)
    if dupes:
        errors.append(f"Duplicate IDs in {label}: {dupes}")

# --- cross-reference integrity: catch typo'd/stale IDs -------------------
control_ids = {x["id"] for x in controls.get("controls", [])}
requirement_ids = {x["id"] for x in reqs.get("requirements", [])}

for lr in legal.get("requirements", []):
    for c in lr.get("mapped_controls", []) or []:
        if c not in control_ids:
            errors.append(f"{lr['id']}: unknown mapped_controls entry {c!r}")

for req in reqs.get("requirements", []):
    for c in req.get("supports_controls", []) or []:
        if c not in control_ids:
            errors.append(f"{req['id']}: unknown supports_controls entry {c!r}")

for t in tests.get("tests", []):
    for c in t.get("controls", []) or []:
        if c not in control_ids:
            errors.append(f"{t['id']}: unknown controls entry {c!r}")
    for r in t.get("requirements", []) or []:
        if r not in requirement_ids:
            errors.append(f"{t['id']}: unknown requirements entry {r!r}")

if errors:
    print("FAILED")
    for e in errors:
        print(f"- {e}")
    sys.exit(1)

print("OK")
print(f"Release metadata consistent at version {VERSION}")
