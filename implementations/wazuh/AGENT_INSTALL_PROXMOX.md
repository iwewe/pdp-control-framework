# Wazuh Agent Install Runbook — Proxmox VE (Debian) Hosts

Self-contained runbook for enrolling Proxmox VE hosts as Wazuh agents
into this framework's lab manager. Written to be followed directly —
no need to read the rest of the repository first. Background and the
reasoning behind each step: `implementations/wazuh/DEPLOYMENT.md`.

## Before you start

- **Manager address:** `192.168.1.52` (LAN). This is a DHCP-assigned
  address on the manager (not a static/reserved lease) — confirm it
  still resolves before a large rollout, and ask the manager owner to
  set a static IP or DHCP reservation if this hasn't been done, so
  agent configs don't silently break after a lease renewal.
- **Exact agent version required: `4.14.7`.** The manager runs Wazuh
  `4.14.7`. Do not install a newer agent version than the manager —
  Wazuh does not support that combination.
- **Enrollment currently has no password** (`authd` `use_password: no`
  on this manager) — any host that can reach port `1515` on the
  manager can self-enroll. Fine on a private LAN you control; don't
  run these commands from an untrusted network.
- **Decide per host, before installing:** does this Proxmox host also
  run PostgreSQL? If yes, it needs the `pdp-database` group in
  addition to `pdp-linux-baseline` (step 5).
- Run every command below as root (or with `sudo`) on the Proxmox host
  being enrolled.

## 1. Install the Wazuh agent package

```bash
curl -s https://packages.wazuh.com/key/GPG-KEY-WAZUH | gpg --no-default-keyring --keyring gnupg-ring:/usr/share/keyrings/wazuh.gpg --import
chmod 644 /usr/share/keyrings/wazuh.gpg
echo "deb [signed-by=/usr/share/keyrings/wazuh.gpg] https://packages.wazuh.com/4.x/apt/ stable main" | tee /etc/apt/sources.list.d/wazuh.list
apt-get update
WAZUH_MANAGER="192.168.1.52" apt-get install wazuh-agent=4.14.7-*
```

`WAZUH_MANAGER` at install time writes the manager address straight
into the agent's `ossec.conf` — no manual edit needed afterward.
Confirm the installed version:

```bash
/var/ossec/bin/wazuh-control info
# expect: WAZUH_VERSION="v4.14.7"
```

## 2. Set a unique per-host asset label

`pdp.asset_id` and `pdp.processing_activity_id` must be unique per
host — they are **not** set by the group's shared configuration on
purpose (see `DEPLOYMENT.md` section 2, "Per-host asset labels"). Add
them to this host's own `ossec.conf`, inside the existing top-level
`<ossec_config>` block:

```bash
python3 - <<'PY'
import re
path = "/var/ossec/etc/ossec.conf"
asset_id = "ASSET-PROXMOX-CHANGE-ME"           # e.g. the host's real hostname or inventory ID
pa_id = "PA-CHANGE-ME"                          # the real processing-activity ID for this host's workload
block = f"""
  <labels>
    <label key="pdp.asset_id">{asset_id}</label>
    <label key="pdp.processing_activity_id">{pa_id}</label>
  </labels>
"""
content = open(path).read()
content = content.replace("</ossec_config>", block + "</ossec_config>")
open(path, "w").write(content)
print("Inserted labels block -- edit asset_id/pa_id above before running, then verify:")
PY
```

Replace `ASSET-PROXMOX-CHANGE-ME` and `PA-CHANGE-ME` with real values
*before* running this, then confirm the file is still well-formed XML
(a broken `ossec.conf` fails the agent to start):

```bash
python3 -c "import xml.etree.ElementTree as ET; ET.parse('/var/ossec/etc/ossec.conf'); print('XML OK')"
```

**Known open question — verify on the first host, not all of them:**
whether this local label correctly overrides the group's own
`pdp.environment` label (same `<labels>` mechanism, different key) or
causes any conflict has not been tested in this lab with more than one
agent. After completing this runbook on the *first* Proxmox host,
check a generated alert/event for that agent on the manager and
confirm both the local (`pdp.asset_id`) and group
(`pdp.environment`) labels appear correctly before repeating this on
every other host.

## 3. Enable SCA remote commands

Every check in the PDP SCA policy uses a `c:<command>` rule, which
Wazuh disables by default for centrally-distributed SCA policies. This
is a **local-only setting** — it cannot be pushed from the manager, so
it must be set on every agent individually:

```bash
echo "sca.remote_commands=1" >> /var/ossec/etc/local_internal_options.conf
```

## 4. Start the agent

```bash
systemctl enable wazuh-agent
systemctl restart wazuh-agent
systemctl status wazuh-agent --no-pager
```

## 5. On the manager: assign this agent to its group(s)

Run this on the manager (`192.168.1.52`), not the agent. Find the new
agent's ID first:

```bash
sudo /var/ossec/bin/agent_control -l
```

Then assign the group(s) decided in "Before you start":

```bash
# every Proxmox host:
sudo /var/ossec/bin/agent_groups -a -i <agent_id> -g pdp-linux-baseline

# only if this host also runs PostgreSQL:
sudo /var/ossec/bin/agent_groups -a -i <agent_id> -g pdp-database
```

The agent picks up the group's shared configuration (SCA policy,
`pdp.environment` label) on its next check-in, or immediately after
another `systemctl restart wazuh-agent` on the agent side.

## 6. Verify

On the manager:

```bash
sudo /var/ossec/bin/agent_control -i <agent_id>
# expect: Status: Active, and Shared file hash matching the group's
```

Confirm the SCA policy actually ran (not "not applicable" — that
symptom means step 3 was skipped):

```bash
sudo /var/ossec/bin/agent_control -i <agent_id>
# check "Syscheck last started/ended" is recent; for SCA specifically,
# the manager's ossec.log will show:
sudo grep "<agent_id>" /var/ossec/logs/ossec.log | grep -i sca | tail -5
```

Repeat steps 1-6 for each Proxmox host, replacing the asset label
values in step 2 for every host.
