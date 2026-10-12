# Competitor intel agent — Hermes + Composio + Olostep

A scheduled agent that checks competitor pricing, changelog and blog pages every week and posts what changed, with analysis, to Slack.

- **Hermes Agent** runs the job on a schedule and does the reasoning.
- **Composio** gives Hermes its tools through one MCP connection.
- **Olostep** (via Composio) scrapes each page into structured JSON and researches the "why" behind a change.
- **Slack** (via Composio) receives one message per run.

```
Hermes cron (Mon 09:00)
  └─ skill: competitor-intel
       ├─ OLOSTEP_SCRAPE_PAGE × 9      structured JSON per page
       ├─ compare with state/<id>.json  last run's copy
       ├─ OLOSTEP_ANSWER_QUESTION × ≤3  sourced context for the biggest changes
       ├─ save new state
       └─ SLACK_SEND_MESSAGE            one update
```

## Sample output

A real run from 2026-10-13 against Linear, Notion and Asana — see [`assets/sample-slack-update.txt`](assets/sample-slack-update.txt) and the agent's own run report in [`assets/sample-run-report.md`](assets/sample-run-report.md).

## Setup

Needs macOS (Apple Silicon) or Linux, a Composio account, an Olostep API key, a Slack workspace, and a model key for Hermes (OpenRouter works).

**1. Install Hermes and give it a model**

```bash
curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash
echo 'OPENROUTER_API_KEY=sk-or-...' >> ~/.hermes/.env
hermes config set model.provider openrouter
```

**2. Connect Composio to Hermes**

Copy your Connect MCP key from [dashboard.composio.dev](https://dashboard.composio.dev), then:

```bash
echo 'COMPOSIO_API_KEY=ck_...' >> ~/.hermes/.env
cat config.example.yaml >> ~/.hermes/config.yaml
hermes mcp test composio        # expect: Connected, Tools discovered
```

**3. Connect Olostep and Slack inside Composio**

```bash
curl -fsSL https://composio.dev/install | sh
composio login
composio link olostep            # paste your Olostep API key
composio link slack              # approve in the browser
```

**4. Install the skill and watch list**

Edit `watchlist.json` (your competitors, your Slack channel), then:

```bash
./install.sh
```

**5. Schedule it**

```bash
hermes cron create "0 9 * * 1" \
  "Run the weekly competitor intel check by following the competitor-intel skill." \
  --name competitor-intel --skill competitor-intel --deliver local \
  --model anthropic/claude-sonnet-5 --provider openrouter

hermes gateway install           # background service that fires scheduled jobs
```

Run it once now instead of waiting for Monday:

```bash
hermes cron run <job_id>
```

The first run has nothing to compare against, so it only saves a baseline. Changes show up from the second run.

## Files

| File | Purpose |
|---|---|
| `watchlist.json` | Pages to watch and the Slack channel |
| `schemas.json` | What to extract from each page type (pricing, changelog, blog) |
| `skills/competitor-intel/SKILL.md` | The agent's instructions |
| `config.example.yaml` | Composio MCP block for Hermes |
| `install.sh` | Copies the above into `~/.hermes/` |
| `seed-baseline.py` | Optional: seeds "last week" from Wayback Machine copies |

State lives in `~/.hermes/competitor-intel/state/`, one JSON file per page.

## How the sample output was produced

The sample is one real run, not a week of waiting. `seed-baseline.py 20261006` saved the closest Wayback Machine copy of each page (captured 2026-09-22 to 2026-10-06) as the "last run", using the same Olostep extraction. The agent then ran live on 2026-10-13 and reported the difference.

## What it costs

- Olostep: structured extraction is 10 credits per page, so about 90 credits per run for 9 pages, plus retries and up to 3 Answers calls.
- A run takes about 4–5 minutes.

## Known limits

- **Extraction varies a little between runs.** The JSON comes from an LLM reading the page, so which 8 changelog entries or 6 plan limits it picks can differ. The skill compares by title and plan name and ignores wording to keep false alarms down, but treat a surprising change as a prompt to look, not as fact.
- **Geo-routed pages.** Some sites localize by visitor location. The skill requests `country: "US"`, retries when a price comes back in another currency, and refuses to report a price change across currencies.
- **Script-rendered pages** need the `wait_before_scraping` delay; without it some changelog pages come back empty.
- **Scraped content is untrusted.** The skill tells the agent to treat it as data and to post only to the configured channel. For extra safety, limit the cron toolset to file access plus the Composio MCP server (`hermes tools`).

## Going further

- `OLOSTEP_CREATE_MONITOR` lets Olostep watch the pages itself and record change events, so the agent only wakes up when something moved.
- `OLOSTEP_START_BATCH` scrapes thousands of URLs in one call if your watch list grows.
