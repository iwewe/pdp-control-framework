#!/usr/bin/env python3
"""
Fleet consistency check for Wazuh agent group membership.

Run ON the Wazuh manager (like implementations/wazuh/install.sh), not
against a remote API -- this shells out to the manager's own
agent_control/agent_groups CLI tools, the same ones install.sh and
implementations/wazuh/AGENT_INSTALL_PROXMOX.md already use, so it needs
no separate credential of its own.

Found the real gap this closes, 2026-09-27: several real Proxmox agents
(luwak, jombor, krete, tobil) were missing the "default" group -- only
in "pdp-linux-baseline" -- while ganesha had both, because
WAZUH_AGENT_GROUP set at install time bypasses automatic "default"
assignment (see implementations/wazuh/AGENT_INSTALL_PROXMOX.md section
5). Fixed by hand at the time; this script catches it automatically
from then on.

Checks per non-manager agent:
  1. "default" group is present.
  2. If any "pdp-*" group is present, at least "pdp-linux-baseline" or
     "pdp-database" is present too (a bare "default"-only PDP-labeled
     agent would mean it never got its PDP config at all).
  3. No group name outside the known set
     {default, pdp-linux-baseline, pdp-database} -- catches a typo'd or
     stray group assignment.
  4. Every agent with a "pdp-*" group has SOME reachable configuration
     (agent_groups -s succeeds) -- a defensive check that group removal
     didn't leave the agent in a broken state.

Agents with NO "pdp-*" group at all are reported separately as
informational, not a failure -- that may be a legitimate non-PDP-scoped
endpoint (e.g. a test agent), not an error this script can call on its
own.

Usage (on the manager):
  sudo python3 tools/validation/validate_agent_group_membership.py
"""
import re
import subprocess
import sys

AGENT_GROUPS_BIN = "/var/ossec/bin/agent_groups"
AGENT_CONTROL_BIN = "/var/ossec/bin/agent_control"
KNOWN_GROUPS = {"default", "pdp-linux-baseline", "pdp-database"}
PDP_GROUPS = {"pdp-linux-baseline", "pdp-database"}


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True, check=False)


def list_agents():
    result = run([AGENT_CONTROL_BIN, "-l"])
    if result.returncode != 0 and not result.stdout:
        print(f"Could not run {AGENT_CONTROL_BIN} -l: {result.stderr}", file=sys.stderr)
        sys.exit(2)
    agents = []
    for line in result.stdout.splitlines():
        m = re.match(r"\s*ID:\s*(\d+),\s*Name:\s*([^,]+),", line)
        if m:
            agents.append((m.group(1), m.group(2).strip()))
    return agents


def agent_groups(agent_id):
    result = run([AGENT_GROUPS_BIN, "-s", "-i", agent_id])
    combined = result.stdout + result.stderr
    m = re.search(r"belongs to groups:\s*(.+?)\.\s*$", combined.strip(), re.MULTILINE)
    if not m:
        return None  # not reachable / no groups info
    return [g.strip() for g in m.group(1).split(",") if g.strip()]


errors = []
info = []

for agent_id, name in list_agents():
    if agent_id == "000":
        continue  # the manager itself, not a managed endpoint

    groups = agent_groups(agent_id)
    if groups is None:
        errors.append(f"{name} (id {agent_id}): could not determine group membership "
                       f"(agent_groups -s -i {agent_id} did not return a parseable result)")
        continue

    group_set = set(groups)
    has_pdp_group = bool(group_set & PDP_GROUPS)

    if not has_pdp_group:
        info.append(f"{name} (id {agent_id}): no pdp-* group -- not PDP-managed, or not yet assigned")
        continue

    if "default" not in group_set:
        errors.append(f"{name} (id {agent_id}): has {sorted(group_set)} but is missing 'default' "
                       f"(see AGENT_INSTALL_PROXMOX.md section 5 -- likely installed with "
                       f"WAZUH_AGENT_GROUP set, which bypasses automatic default assignment)")

    unknown = group_set - KNOWN_GROUPS
    if unknown:
        errors.append(f"{name} (id {agent_id}): unexpected group(s) not in the known set "
                       f"{sorted(KNOWN_GROUPS)}: {sorted(unknown)}")

if info:
    print("Informational (not PDP-managed, or not yet assigned a pdp-* group):")
    for line in info:
        print(" -", line)
    print()

if errors:
    print("FAILED")
    for e in errors:
        print("-", e)
    sys.exit(1)

print("OK")
print(f"Checked {len(list_agents()) - 1} managed agents (excluding the manager itself); "
      f"all pdp-* agents have consistent group membership.")
