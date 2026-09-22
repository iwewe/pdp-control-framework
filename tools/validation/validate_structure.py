#!/usr/bin/env python3
from pathlib import Path
import sys
import yaml
import xml.etree.ElementTree as ET

def find_repo_root(start):
    p = Path(start).resolve()
    for candidate in [p] + list(p.parents):
        if (candidate / "FRAMEWORK_MANIFEST.yml").exists():
            return candidate
    raise RuntimeError("Repository root not found")

ROOT = find_repo_root(Path(__file__).parent)
errors = []

def load_yaml(path):
    try:
        with open(path, encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception as e:
        errors.append(f"YAML error {path}: {e}")
        return None

def parse_rule_xml(path):
    try:
        return ET.fromstring(path.read_text(encoding="utf-8"))
    except Exception as e:
        errors.append(f"Rule XML error {path}: {e}")
        return None

def parse_decoder_fragment(path):
    try:
        text = path.read_text(encoding="utf-8")
        return ET.fromstring("<wazuh_decoder_fragment>" + text + "</wazuh_decoder_fragment>")
    except Exception as e:
        errors.append(f"Decoder XML fragment error {path}: {e}")
        return None

for p in ROOT.rglob("*.yml"):
    load_yaml(p)

for p in (ROOT / "implementations" / "wazuh" / "rules").glob("*.xml"):
    parse_rule_xml(p)
for p in (ROOT / "implementations" / "wazuh" / "decoders").glob("*.xml"):
    parse_decoder_fragment(p)

controls = load_yaml(ROOT / "framework" / "controls" / "CONTROL_CATALOGUE.yml") or {}
requirements = load_yaml(ROOT / "framework" / "requirements" / "CONTROL_REQUIREMENTS.yml") or {}
legal = load_yaml(ROOT / "framework" / "legal" / "LEGAL_MAPPING.yml") or {}
tests = load_yaml(ROOT / "implementations" / "wazuh" / "WAZUH_TEST_CATALOGUE.yml") or {}
manifest = load_yaml(ROOT / "implementations" / "wazuh" / "manifests" / "TRACEABILITY.yml") or {}

control_ids = {x["id"] for x in controls.get("controls", [])}
requirement_ids = {x["id"] for x in requirements.get("requirements", [])}
legal_ids = {x["id"] for x in legal.get("requirements", [])}
test_ids = {x["id"] for x in tests.get("tests", [])}

for art in manifest.get("artifacts", []):
    target = ROOT / art["path"]
    if not target.exists():
        errors.append(f"Missing artifact: {art['path']}")
    for x in art.get("controls", []):
        if x not in control_ids:
            errors.append(f"Unknown control {x} in {art['path']}")
    for x in art.get("requirements", []):
        if x not in requirement_ids:
            errors.append(f"Unknown requirement {x} in {art['path']}")
    for x in art.get("legal_requirements", []):
        if x not in legal_ids:
            errors.append(f"Unknown legal requirement {x} in {art['path']}")
    for x in art.get("tests", []):
        if x not in test_ids:
            errors.append(f"Unknown test {x} in {art['path']}")

seen = set()
for p in (ROOT / "implementations" / "wazuh" / "rules").glob("*.xml"):
    rule_root = parse_rule_xml(p)
    if rule_root is None:
        continue
    for rule in rule_root.iter("rule"):
        rid = int(rule.attrib["id"])
        if not 100000 <= rid <= 120000:
            errors.append(f"Rule ID outside Wazuh custom range: {rid} ({p.name})")
        if rid in seen:
            errors.append(f"Duplicate Wazuh rule ID: {rid}")
        seen.add(rid)

if errors:
    print("FAILED")
    for e in errors:
        print(f"- {e}")
    sys.exit(1)

print("OK")
print(f"Validated {len(legal_ids)} legal requirements")
print(f"Validated {len(control_ids)} controls")
print(f"Validated {len(requirement_ids)} generic requirements")
print(f"Validated {len(test_ids)} Wazuh tests")
print(f"Validated {len(seen)} custom Wazuh rule IDs")
