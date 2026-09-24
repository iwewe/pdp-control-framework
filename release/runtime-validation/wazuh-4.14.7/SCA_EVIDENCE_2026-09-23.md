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

## Addendum — centralized (group-pushed) SCA on a separate managed agent

The scenario above only validated the SCA policy as a *local* policy on
the manager's own agent `000`. A second, previously-open item was whether
`c:`-based checks in this policy also work when the policy is distributed
to a **separate enrolled agent** via a centralized `agent.conf` group
(`pdp-linux-baseline`), which is the actual production deployment model.

### Investigation

On first testing this against `pdp-agent-test` (agent `001`, enrolled in
the `pdp-linux-baseline` group), all 6 checks returned
`not applicable` / `"Invalid path or wrong permissions to run command '<cmd>'"`.
This was initially suspected to be the documented `sca.remote_commands`
internal option (default `0`), which restricts `c:` command execution for
policies pushed from a manager group.

Setting `sca.remote_commands=1` in the agent's
`/var/ossec/etc/local_internal_options.conf` did **not**, by itself,
change the result — which is what had this item marked as an open
blocker.

**Root cause, confirmed by direct inspection:** `pdp-agent-test` is a
minimal Docker container (PID 1 is `sleep`, no init system) that never
had `sshd` or `systemctl` installed at all — `which systemctl sshd`
returned nothing, and neither binary existed anywhere on disk. This is
**not** an `sca.remote_commands` restriction: Wazuh's own vendor-shipped
`cis_ubuntu24-04.yml` policy, already running on the same agent, failed
with the *identical* `"Invalid path or wrong permissions"` message on
the equivalent `c:sshd -T` / `c:systemctl is-enabled ...` checks. A
restriction gate would produce a distinct "disabled by policy"-style
message, not a generic exec failure — this is a missing-binary problem,
confirmed independently of anything specific to our policy.

**Fix:** installed `openssh-server` in the container
(`apt-get install -y openssh-server`, then started `sshd` manually, since
the container has no init system to manage it as a service). This
transitively pulled in `systemd`/`libpam-systemd`, which also provided a
`systemctl` binary. After a clean agent restart (no debug flags, `sca.remote_commands=1`
retained in `local_internal_options.conf`), all 6 checks in
`pdp_linux_baseline.yml` returned genuine results with no
`not applicable`/exec errors:

```
('PDP: Direct SSH root login is disabled', 'failed', '')
('PDP: SSH empty-password authentication is disabled', 'passed', '')
('PDP: System audit service is enabled', 'failed', '')
('PDP: Time synchronization service is active', 'passed', '')
('PDP: A supported host firewall is enabled', 'failed', '')
('PDP: Wazuh agent service is enabled', 'failed', '')
```

(Verified via `sudo python3 -c "sqlite3 ...SELECT title, result, reason FROM sca_check WHERE policy_id = 'pdp_linux_baseline_v01'"` against `/var/ossec/queue/db/001.db` on the manager.)

Debug logging (`sca.debug=2`) captured the exact command executions and
results during the diagnosis, e.g.:

```
DEBUG: Executing command 'sshd -T', and testing output with pattern 'r:^\s*permitrootlogin\s+no$'
DEBUG: Command 'sshd -T' returned code 0
DEBUG: Result for rule 'c:sshd -T -> r:^\s*permitrootlogin\s+no$': 0
```

confirming the centralized/group-pushed policy's `c:` checks execute
correctly end-to-end (manager → shared group config → agent →
`sca.remote_commands=1` → command execution → pattern match → result
persisted to the agent's local SCA database) once the target binaries
actually exist on the agent host.

### Conclusion

- **`sca.remote_commands` was never the actual blocker.** It was already
  correctly set to `1` before this investigation and worked as documented
  once the underlying commands had something to execute.
- The real cause was specific to this lab's minimal test container, which
  lacked `sshd`/`systemctl` entirely — a test-environment gap, not a
  defect in `pdp_linux_baseline.yml` or in the framework's SCA design.
- **Recommendation for production deployment**: on any target host,
  confirm `openssh-server` and a service manager (`systemd` or
  distribution equivalent providing `systemctl`) are present before
  relying on this policy's `c:`-based checks; on a normal (non-minimal,
  non-container) Ubuntu 24.04 server these are present by default. No
  policy redesign to file-based (`f:`) checks is warranted — Wazuh's own
  vendor `cis_ubuntu24-04.yml` uses the identical `c:` command-based
  pattern for the same class of checks, so a file-based rewrite would
  make this policy *less* consistent with upstream Wazuh SCA conventions,
  not more robust.

## Addendum — SCA check-ID collision audit against all bundled Wazuh policies (2026-09-24)

Earlier collision testing (main section above) only checked our policy
(`910001`-`910006`) alongside the one other policy active in this lab,
the vendor `cis_ubuntu24-04.yml`. This audits against **every** SCA
policy Wazuh 4.14.7 ships, not just the one enabled by default.

**Method:** `/var/ossec/ruleset/sca/` on this install ships ~70 vendor
policies (most `.disabled` by default — covering every CIS benchmark
Wazuh supports: RHEL/CentOS/Rocky/Alma/SLES/Debian/Ubuntu/Amazon Linux/
Oracle Linux across versions, Windows, macOS, plus product-specific
policies for Apache, nginx, IIS, MySQL, PostgreSQL, MongoDB, Oracle DB,
SQL Server, and a generic `sca_distro_independent_linux.yml` and
`web_vulnerabilities.yml`). Extracted every `id:` field across the entire
set (`grep -oE 'id: [0-9]+'` over all files, enabled and disabled alike)
and computed the overall minimum and maximum.

**Result:** the full range across all bundled Wazuh SCA content is
**1000-40165**. Spot-checked several individual policies for their own
sub-ranges (`cis_postgre-sql-13`: 24000-24029; `cis_debian12`:
33010-33301; `cis_rhel9_linux`: 28000-28158; `web_vulnerabilities`:
14000-14015; `cis_ubuntu24-04`: 35500-35778;
`sca_distro_independent_linux`: 36000-36189) — none come remotely close
to our `910001`-`910006` range.

**Conclusion:** `implementations/wazuh/sca/pdp_linux_baseline.yml`'s ID
range does not collide with any Wazuh-bundled SCA policy, for any
platform or product Wazuh currently ships content for — not just the one
policy tested alongside it previously. Third-party/custom SCA content
from outside the Wazuh vendor distribution remains untested (impossible
to exhaustively rule out), but the practical collision risk from Wazuh's
own content is effectively nil given this margin.
