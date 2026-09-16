# Synthetic Liquidity Depth Scanner

**Executable cash-exit capacity for Solana tokenized equities and stock-quoted launches — measured, not estimated.**

A [CoolBB](https://coolbb.site) product. The scanner probes live Jupiter swap quotes at escalating order sizes and builds an **executable cash-exit curve** for each asset. It answers:

> *If I hold $X of this asset, how much USDC can I actually get out, and what breaks first?*

Printed market cap and pool TVL do not answer that question. This tool does.

---

## Why it exists

| Problem | What the scanner measures |
|---------|---------------------------|
| Printed price ≠ exit price | Cash recovery at $1k → $1M notionals |
| TVL/mcap ratio is a weak predictor | Exit capacity and mcap-to-exit ratio |
| Routing cliffs are invisible in dashboards | Cliff detection via route-change bisection |
| Hard no-route walls | Smallest notional where Jupiter returns no route |
| Ticker impersonation | Mint-keyed registry with impersonation flags |
| RFQ depth is quoted, not committed | RFQ venue share tagged separately |

For the full research findings and methodology, see the dashboard **Why it matters** page or [docs/HOW_IT_WORKS.md](docs/HOW_IT_WORKS.md).

---

## Features

- **Tiered probe scheduler** — xStocks and top launches probed every 15 min; long tail every 6 hours
- **Sell ladder** — $1k → $10k → $50k → $100k → $250k → $500k → $1M with micro-quote baseline
- **Launch diagnostics** — two-hop routing (token → quote stock → USDC) with binding-leg detection
- **Letter grades (A–F)** — based on exit capacity, cliffs, no-route ceilings, and mcap/exit ratio
- **Degradation alerts** — exit capacity drops, new cliffs, tightened no-route walls
- **Bilingual dashboard** — English and Chinese (Next.js 15, React Three Fiber charts)
- **REST API** — leaderboard, asset detail, live exit quotes, alert feed

---

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Worker    │────▶│  PostgreSQL  │◀────│     API     │
│ (scheduler) │     │  (Timescale) │     │  (FastAPI)  │
└──────┬──────┘     └──────────────┘     └──────┬──────┘
       │                                         │
       ▼                                         ▼
┌─────────────┐                          ┌─────────────┐
│   Jupiter   │                          │  Dashboard  │
│  Swap/Price │                          │  (Next.js)  │
└─────────────┘                          └─────────────┘
```

| Component | Entry point | Role |
|-----------|-------------|------|
| **Worker** | `python -m liquidity_scanner.worker` | Registry sync, scheduled probes, scoring, alerts |
| **API** | `uvicorn liquidity_scanner.api.main:app` | Serves assets, curves, leaderboard, alerts |
| **Dashboard** | `dashboard/` | Visualizes leaderboard, asset detail, position calculator |
| **Database** | Postgres 16 + TimescaleDB | Assets, probes, rungs, scores, alerts |

**Data sources:** StonkFun API (launch discovery), Jupiter API (live quotes + prices), issuer-verified xStock mint allowlist in `src/liquidity_scanner/constants.py` (24 mints).

---

## Tech stack

| Layer | Stack |
|-------|-------|
| Backend | Python 3.11, FastAPI, SQLAlchemy (async), APScheduler, httpx |
| Database | PostgreSQL 16 + TimescaleDB, Alembic migrations |
| Frontend | Next.js 15, React 19, Recharts, React Three Fiber |
| External APIs | Jupiter Swap/Price, StonkFun public API |
| CI | GitHub Actions — unit tests + optional live Jupiter smoke |

---

## Prerequisites

- Python 3.11+
- Node.js 20+ (for dashboard)
- Docker (for Postgres / full stack)
- Jupiter API key (free tier) — [developers.jup.ag](https://developers.jup.ag), **1 request/second**

This MVP is designed for the **free Jupiter API**. Paid tier is not required.

---

## Quick start (local development)

```bash
# 1. Configure environment
cp .env.example .env
# Edit .env — set JUP_API_KEY (free tier, 1 RPS)

# 2. Start database
docker compose up -d db

# 3. Install backend + run migrations
pip install -e ".[dev]"
alembic upgrade head

# 4. Seed the asset registry (optional — worker also syncs every 6 h)
lds sync-registry

# 5. Start API and worker (separate terminals)
uvicorn liquidity_scanner.api.main:app --reload --app-dir src
python -m liquidity_scanner.worker

# 6. Start dashboard
cd dashboard && npm install && npm run dev
```

| Service | URL |
|---------|-----|
| Dashboard | http://localhost:3000 |
| API | http://localhost:8000 |
| API docs | http://localhost:8000/docs |
| Postgres | localhost:5432 |

---

## Docker Compose (full stack)

```bash
cp .env.example .env   # set JUP_API_KEY
docker compose up
```

Services: `db` (5432), `api` (8000), `worker`, `dashboard` (3000).

Run migrations inside the API container on first boot:

```bash
docker compose exec api alembic upgrade head
```

---

## CLI

The `lds` command is installed with the package:

```bash
lds sync-registry   # Pull xStocks + graduated launches from StonkFun, run impersonation checks
```

---

## API endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Service health check |
| `GET` | `/assets` | List active assets with latest score (`?kind=xstock\|launch`) |
| `GET` | `/assets/{mint}` | Asset detail + latest exit-curve rungs |
| `GET` | `/assets/{mint}/history` | Probe/score history |
| `GET` | `/exit-quote?mint=&notional=` | Live probe for a specific position size (uses Jupiter credits) |
| `GET` | `/leaderboard?sort=` | Ranked by `mcap_exit_ratio` (default) or `exit_capacity_95` |
| `GET` | `/alerts` | Recent degradation/cliff/no-route alerts |

---

## Dashboard pages

Routes are locale-prefixed (`/en`, `/zh`):

| Page | Route | Description |
|------|-------|-------------|
| Home | `/[lang]` | Product overview and key findings |
| Why it matters | `/[lang]/why` | Research evidence — cliffs, TVL fallacy, impersonation |
| Methodology | `/[lang]/methodology` | How probes and scoring work |
| Roadmap | `/[lang]/roadmap` | Product roadmap |
| Scanner | `/[lang]/scanner` | Live leaderboard |
| Asset detail | `/[lang]/scanner/asset/[mint]` | Exit curve chart, route table, scores |
| Calculator | `/[lang]/scanner/calculator` | Position-size exit quote tool |

Set `NEXT_PUBLIC_API_URL` (default `http://localhost:8000`) to point the dashboard at your API.

---

## Free-tier polling strategy

The worker probes **one asset at a time** through a shared token-bucket limiter (`JUP_RPS=1`). Each completed probe writes a new score row to Postgres; the API and dashboard always read the **latest** value, so users see cached data between refresh cycles without hitting Jupiter on every page load.

| Tier | Assets | Refresh interval | Typical API calls/asset |
|------|--------|------------------|-------------------------|
| **A** | 24 xStocks + top 20 launches | Every 30 min | ~10 (xStock) / ~24 (launch) |
| **B** | Next 50 launches | Every 2 hours | ~24 |
| **C** | Remaining launches | Every 12 hours | ~24 |

The scheduler picks the highest-priority asset whose interval has elapsed and probes it sequentially. When nothing is due, it sleeps and polls again. Cliff bisection (extra quotes) is disabled on free tier to conserve requests; set `ENABLE_CLIFF_BISECTION=true` if you upgrade.

---

## Configuration

Key environment variables (see [.env.example](.env.example)):

| Variable | Default | Purpose |
|----------|---------|---------|
| `DATABASE_URL` | `postgresql+asyncpg://scanner:scanner@localhost:5432/liquidity_scanner` | Async Postgres connection |
| `JUP_API_KEY` | *(empty)* | Jupiter API key (free tier) |
| `JUP_RPS` | `1` | Max Jupiter requests per second |
| `QUOTE_SAMPLES` | `1` | Quotes per ladder rung (1 for free tier) |
| `TIER_A_REFRESH_MINUTES` | `30` | Min minutes between re-probes for tier A |
| `TIER_B_REFRESH_HOURS` | `2` | Min hours between re-probes for tier B |
| `TIER_C_REFRESH_HOURS` | `12` | Min hours between re-probes for tier C |
| `MAX_TIER_A_LAUNCHES` | `20` | Launch count in tier A (besides xStocks) |
| `ENABLE_CLIFF_BISECTION` | `false` | Extra quotes to refine routing cliffs |
| `ENABLE_SCHEDULER` | `true` | Worker scheduler on/off |
| `LOG_LEVEL` | `INFO` | Structlog level |

Probe ladder sizes, RFQ venue list, and cliff thresholds live in `src/liquidity_scanner/config.py`.

---

## Testing

```bash
pytest                          # Unit tests + regression fixtures
pytest tests/test_live_smoke.py # Live Jupiter quote (requires JUP_API_KEY)
```

Regression fixtures cover SPYx, STONK, STRCx cliff detection, and FTR no-route ceiling. CI runs unit tests on every push; live smoke runs when `JUP_API_KEY` is configured as a GitHub secret.

---

## Project structure

```
src/liquidity_scanner/
├── api/            FastAPI routes
├── probe/          Jupiter client, rate limiter, ladder probe engine
├── scoring/        Pure scoring from rung data
├── registry/       StonkFun discovery + impersonation detection
├── scheduler/      APScheduler jobs, tier assignment, credit guard
├── alerting/       Score comparison + webhook notifier
├── db/             SQLAlchemy models + async session
├── pipeline.py     Probe → score → alert orchestration
├── worker.py       Scheduler process entry point
└── cli.py          lds sync-registry

dashboard/          Next.js frontend (en/zh)
tests/              Unit tests + regression fixtures
alembic/            Database migrations
docs/               Architecture and code logic reference
```

Research artifacts in the repo root (`measure_two_hop.py`, `scan_results.json`, `two_hop_*.json`) are feasibility-phase outputs. The production probe engine in `src/liquidity_scanner/probe/` supersedes them.

---

## Documentation

- **[docs/HOW_IT_WORKS.md](docs/HOW_IT_WORKS.md)** — Full architecture, workflow, scoring logic, database schema, and data-flow diagrams

---

## Disclaimer

Research tool only. Not investment advice. Executable quotes reflect Jupiter router state at probe time and may change. RFQ venue depth is quoted, not committed.

---

## License

Proprietary — © CoolBB. All rights reserved.
