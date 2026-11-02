# emerald-mqtt-bridge — CLAUDE.md

BLE-to-MQTT bridge for an Emerald Electricity Advisor, run on a Raspberry Pi (garagepi, `/home/dietpi/emerald-bridge/`, a plain copy, not a git checkout) and consumed by Home Assistant.

## Forge (changed 2 Nov 2026)

**Gitea is the only home of this repo (changed 2 Nov 2026: demoted from a GitHub-mirrored repo).** Work on `https://git.kiztigs.com/kmbrimble/emerald-mqtt-bridge` (`origin`, gt credential helper); use `gt`, not `gh`, for issues and PRs.
`main` is protected: PR + the green `CI / check (pull_request)` (`.gitea/workflows/ci.yml`); butler-bot merges its own green PRs. The GitHub copy `github.com/kmbrimble/emerald-mqtt-bridge` is **archived and frozen** (its README says so; there is no mirror any more): never push to it.
Nothing deploys from this repo automatically: garagepi runs a plain copy in `/home/dietpi/emerald-bridge/`; deploying a change there is manual (copy `emerald.py`, restart the service).

Known issue: `# noqa: F821` in `emerald.py` marks a real latent bug (issue #2); do not widen it.
