# emerald-mqtt-bridge — CLAUDE.md

BLE-to-MQTT bridge for an Emerald Electricity Advisor, run on a Raspberry Pi (garagepi, `/home/dietpi/emerald-bridge/`, a plain copy, not a git checkout) and consumed by Home Assistant.

## Forge (changed 2 Nov 2026)

**Gitea is primary; GitHub is a read-only push mirror and must never be pushed to directly** (the mirror force-syncs and prunes refs; Gitea syncs on every push and every 10 minutes).
Work on `https://git.kiztigs.com/kmbrimble/emerald-mqtt-bridge` (`origin`, gt credential helper); use `gt`, not `gh`, for issues and PRs. `main` is protected: PR + the green
`CI / check (pull_request)` (`.gitea/workflows/ci.yml`: py_compile, ruff `E9,F`, the YAML and the systemd unit parse); butler-bot merges its own green PRs. GitHub has Issues, Wiki, Projects,
Discussions and PRs switched off. The repo stays public on GitHub because the README is a how-to for others (it tells readers to clone it from GitHub); nothing deploys from it automatically.
Deploying a change to garagepi is manual (copy `emerald.py`, restart the service).

Known issue: `# noqa: F821` in `emerald.py` marks a real latent bug (issue #2); do not widen it.
