# Real SCA Policy Evidence — 2026-09-23

**Target:** Wazuh 4.14.7 (real manager, agent `000`/local)
**Environment:** Ubuntu 24.04.4 LTS
**Policy:** `implementations/wazuh/sca/pdp_linux_baseline.yml` (`pdp_linux_baseline_v01`)

## Method

1. Confirmed the policy file already deployed at
   `/var/ossec/etc/shared/default/pdp_linux_baseline.yml` is byte-identical
   to the repository copy.
2. Added an explicit `<policies>` entry under the manager's local `<sca>`
   block in `/var/ossec/etc/ossec.conf` (it was not referenced there yet,
   so only Wazuh's bundled `cis_ubuntu24-04.yml` was running):
   ```xml
   <policies>
     <policy enabled="yes">/var/ossec/etc/shared/default/pdp_linux_baseline.yml</policy>
   </policies>
   ```
3. `sudo /var/ossec/bin/wazuh-analysisd -t` — exit code 0, no errors.
4. `sudo /var/ossec/bin/wazuh-control restart` — clean restart; `ossec.log`
   showed `sca: INFO: Loaded policy '/var/ossec/etc/shared/default/pdp_linux_baseline.yml'`
   and `sca: INFO: Evaluation finished for policy '...'` with no
   errors/warnings referencing the policy.

## Results

All 6 checks defined in the policy executed and produced a result (none
were skipped or errored). SCA summary alert: **score 33% (2/6 passed)**.

| Check ID | Title | Result | Manual verification |
|---|---|---|---|
| 910001 | Direct SSH root login is disabled | FAIL | `sshd -T`: `permitrootlogin without-password` (not `no`) |
| 910002 | SSH empty-password authentication is disabled | PASS | `sshd -T`: `permitemptypasswords no` |
| 910003 | System audit service is enabled | FAIL | `systemctl is-enabled auditd`: `not-found` (auditd not installed) |
| 910004 | Time synchronization service is active | PASS | `systemctl is-enabled systemd-timesyncd`: `enabled` |
| 910005 | A supported host firewall is enabled | FAIL | `ufw`/`firewalld`: `not-found`; `nftables`: `disabled` |
| 910006 | Wazuh agent service is enabled | FAIL | `systemctl is-enabled wazuh-agent`: `not-found` (this host runs `wazuh-manager`, not `wazuh-agent`) |

**All 6 results were independently reproduced with direct shell commands
and matched exactly** — the policy's `sshd -T` / `systemctl is-enabled`
condition logic is correct.

## Interpretation

- **No bug found in the SCA policy itself.** Unlike the pgAudit decoder
  and FIM rules, this policy required no code changes — the checks
  correctly reflect this lab host's actual (unhardened, default) security
  posture.
- The 4 failures are genuine findings about this specific lab VM, not
  false positives: it does not have `auditd` installed, no host firewall
  is enabled, `PermitRootLogin` is not set to the strict `no` (it defaults
  to `without-password`), and — expected for a manager host — there is no
  `wazuh-agent` service (check `910006` is designed for monitored
  endpoints, not the manager itself).
- This confirms the policy YAML is syntactically correct, its
  `condition: all`/`condition: any` grouping behaves as documented, and its
  `c:<command> -> r:<regex>` checks execute successfully against a real
  Ubuntu 24.04 host via Wazuh 4.14.7's SCA module.

## What this does NOT validate

- SCA check-ID collision against a *different* real installation's other
  custom/bundled policies (this lab only ever had the vendor
  `cis_ubuntu24-04.yml` policy alongside ours, and no ID overlap was
  observed between the two).
- Execution on a genuinely separate managed *agent* (as opposed to the
  manager's own local agent `000`) — centralized `agent.conf` distribution
  to a real enrolled agent remains untested (see
  `implementations/wazuh/DEPLOYMENT.md`).
