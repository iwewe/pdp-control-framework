# Real Agent Enrollment + agent.conf Distribution Evidence — 2026-09-23

**Target:** Wazuh 4.14.7 manager (`hansip`, Ubuntu 24.04.4 LTS) + a genuinely
separate Wazuh 4.14.7 agent (not the manager's own local agent `000` used
in prior phases).

## Method

A separate agent host was needed because every prior phase
(authentication, PostgreSQL, privileged access, FIM, SCA) had only been
exercised against the manager's own local agent `000`. Docker was chosen
over LXD (the `lxc` shim on this host tried to auto-install the LXD snap
and failed with a connection reset to the snap store) and over a second
real VM (out of scope for this lab):

```bash
sudo apt-get install -y docker.io
sudo docker run -d --name pdp-agent-test --hostname pdp-agent-test ubuntu:24.04 sleep infinity
# inside the container: add the Wazuh apt repo, then:
WAZUH_MANAGER=192.168.1.52 apt-get install -y wazuh-agent
/var/ossec/bin/agent-auth -m 192.168.1.52   # enrolls and receives a key
/var/ossec/bin/wazuh-control start          # no systemd in the container, so start daemons directly
```

Enrollment succeeded immediately: `agent_control -l` on the manager showed
`ID: 001, Name: pdp-agent-test, IP: any, Active`.

## Finding 1 (blocking) — `<syscollector>` is not valid in a centralized `agent.conf`

Deploying `implementations/wazuh/shared/pdp-linux-baseline/agent.conf`
unmodified to a new `pdp-linux-baseline` agent group (via
`agent_groups -a -g ...`, copying the file to
`/var/ossec/etc/shared/pdp-linux-baseline/agent.conf`, and assigning agent
`001` to the group) produced, on the agent:

```
wazuh-agentd: ERROR: (1230): Invalid element in the configuration: 'syscollector'.
wazuh-agentd: ERROR: (1202): Configuration error at 'etc/shared/agent.conf'.
wazuh-syscheckd: ERROR: (1230): Invalid element in the configuration: 'syscollector'.
wazuh-syscheckd: ERROR: (1202): Configuration error at 'etc/shared/agent.conf'.
wazuh-logcollector: ERROR: (1230): Invalid element in the configuration: 'syscollector'.
wazuh-modulesd: ERROR: (1230): Invalid element in the configuration: 'syscollector'.
```

**`<syscollector>` is not a supported element inside a centralized/shared
`agent.conf` in Wazuh 4.14.7** — it must be configured locally in each
agent's own `ossec.conf`. Critically, this single invalid element
invalidated the **entire** `agent.conf` for every daemon that reads it
(agentd, syscheckd, logcollector, modulesd all logged the same error) —
not just the syscollector setting. That means the `<labels>`, `<syscheck>`,
and `<sca>` blocks in the *same file* silently stopped applying too.

**Fix:** removed the `<syscollector>` block from
`implementations/wazuh/shared/pdp-linux-baseline/agent.conf` (syscollector
runs from the agent's local default config regardless). After the fix and
an agent restart, all errors stopped and `wazuh-syscheckd` correctly
started monitoring `/etc/ssh`, `/etc/audit`, `/etc/systemd`, `/etc/cron.d`
with `whodata` as configured.

## Finding 2 (blocking, unresolved) — the SCA policy cannot run at all via centralized distribution

Once Finding 1 was fixed, `pdp_linux_baseline.yml` loaded via the group
(the policy file itself was also added to the group's shared directory, at
the exact path its own `agent.conf` references:
`/var/ossec/etc/shared/pdp_linux_baseline.yml`). The SCA module logged a
clean load and evaluation:

```
sca: INFO: Loaded policy '/var/ossec/etc/shared/pdp_linux_baseline.yml'
sca: INFO: Evaluation finished for policy '/var/ossec/etc/shared/pdp_linux_baseline.yml'
```

But querying the manager's authoritative per-agent database
(`/var/ossec/queue/db/001.db`, table `sca_check`) showed **all 6 checks
result `not applicable`**, each with the identical `reason`:

```
Ignoring check for running command 'sshd -T'. The internal option 'sca.remote_commands' is disabled
Ignoring check for running command 'systemctl is-enabled auditd'. The internal option 'sca.remote_commands' is disabled
... (all 6 checks, same pattern)
```

`/var/ossec/etc/internal_options.conf` confirms this is by design:

```
# Enable it to accept execute commands from SCA policies pushed from the manager in the shared configuration
# Local policies ignore this option
sca.remote_commands=0
```

Every one of the 6 checks in `pdp_linux_baseline.yml` uses a `c:<command>`
rule (`sshd -T`, `systemctl is-enabled ...`). Wazuh disables command
execution by default for any SCA policy delivered via centralized/shared
configuration, specifically to stop a compromised manager from pushing
arbitrary shell commands to agents. **This means the policy, as written,
produces zero usable results when deployed the way
`implementations/wazuh/DEPLOYMENT.md` (before this fix) instructed.**

**Attempted remediation (did not work):** set `sca.remote_commands=1` in
`local_internal_options.conf` on the agent, then on both the agent and the
manager, with a full `wazuh-control stop` + `start` (not just `restart`)
each time to guarantee a genuinely fresh process (confirmed via `ps aux`
that a new, non-zombie `wazuh-modulesd` PID was running). The log warning
did stop appearing (likely due to Wazuh's repeated-message log
suppression, not a real change), but the authoritative `sca_check` table
in `001.db` still showed `not applicable` with the exact same "disabled"
reason string after every attempt. This was tested exhaustively (4
separate restart cycles, both scopes) before concluding it does not take
effect through this mechanism in this installation.

### Practical impact

`implementations/wazuh/sca/pdp_linux_baseline.yml` can currently only
produce real results when configured as a **local** policy directly in an
endpoint's own `ossec.conf` (exactly how it was validated in
`release/runtime-validation/wazuh-4.14.7/SCA_EVIDENCE_2026-09-23.md`,
against the manager's own local agent `000`). It cannot currently be
distributed centrally via agent groups and actually evaluate anything.

### Recommended follow-up (not applied in this pass)

1. Document this limitation prominently (done, in
   `implementations/wazuh/DEPLOYMENT.md`) and stop recommending
   group-based SCA distribution until one of the below is resolved.
2. Investigate the correct, supported way to enable `sca.remote_commands`
   for centrally-managed fleets (may require Wazuh vendor documentation/
   support beyond what this lab could determine).
3. Consider redesigning the policy's checks to avoid `c:` commands where
   a `f:`/`r:` (file-content) check can substitute -- e.g., checking
   `sshd_config` directives directly instead of `sshd -T`'s *effective*
   configuration output, accepting the tradeoff that file-based checks
   don't reflect config-include resolution the way `sshd -T` does.

## Finding 3 — `pdp-database/agent.conf` has no equivalent problem

`implementations/wazuh/shared/pdp-database/agent.conf` (`labels`,
`localfile`, `syscheck` -- no `syscollector`, no `sca`) was deployed to a
second group (`pdp-database`) assigned to the same agent, alongside
`pdp-linux-baseline`. It loaded cleanly with no configuration errors, and
`wazuh-syscheckd` correctly began monitoring `/etc/postgresql` with
`whodata` as configured.

## Summary

| Item | Result |
|---|---|
| Agent enrollment via `agent-auth` | PASS |
| `pdp-linux-baseline/agent.conf` distribution (after fix) | PASS |
| `pdp-database/agent.conf` distribution | PASS |
| SCA policy execution via centralized distribution | **FAIL** (all checks `not applicable`; local-only policy deployment works, see `SCA_EVIDENCE_2026-09-23.md`) |
