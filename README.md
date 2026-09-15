# Synthetic Liquidity Depth Scanner

Measures executable cash-exit capacity for Solana tokenized equities and stock-quoted launches.

See [docs/HOW_IT_WORKS.md](docs/HOW_IT_WORKS.md) for architecture, workflow, and code logic.

## Quick start

```bash
cp .env.example .env
# Add JUP_API_KEY from https://developers.jup.ag

docker compose up -d db
pip install -e ".[dev]"
alembic upgrade head

# Run API + scheduler worker
uvicorn liquidity_scanner.api.main:app --reload --app-dir src
python -m liquidity_scanner.worker
```

## Dashboard

```bash
cd dashboard && npm install && npm run dev
```

Open http://localhost:3000

## Tests

```bash
pytest
```
