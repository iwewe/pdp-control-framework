# Real Wazuh 4.14.7 Lab Validation

This directory is the release gate for **actual** Wazuh execution.

## Required lab

- Wazuh manager 4.14.7
- Ubuntu 24.04 test agent for SCA/FIM
- repository checked out on the manager
- custom decoder/rules copied to Wazuh's custom directories

Wazuh's official package list provides `wazuh-manager_4.14.7-1_amd64.deb`, and `wazuh-logtest` is the supported tool for real decoder/rule testing.

## Install custom content in the lab

Back up your existing custom content first.

```bash
sudo cp implementations/wazuh/decoders/pdp_pgaudit.xml \
  /var/ossec/etc/decoders/

sudo cp implementations/wazuh/rules/pdp_*.xml \
  /var/ossec/etc/rules/
```

Restart only after configuration review:

```bash
sudo systemctl restart wazuh-manager
```

## Run the real gate

```bash
sudo python3 release/runtime-validation/wazuh-4.14.7/run_real_lab_validation.py
```

The gate writes:

```text
release/runtime-validation/wazuh-4.14.7/RESULT.json
```

Promotion rule:

```text
RESULT.overall == PASS
AND version == 4.14.7
```

Only after that should the implementation status be promoted to `LAB_VALIDATED`.

## Additional Ubuntu agent validation

The server-side rule gate is not enough for SCA/FIM.

On an Ubuntu 24.04 agent also validate:

- custom SCA policy loads and executes,
- expected PASS and FAIL states for SSH/audit/time/firewall checks,
- FIM create/modify/delete events,
- centralized `agent.conf`,
- PDP labels present in generated alerts.

Record this in a separate lab evidence file before 1.0.
