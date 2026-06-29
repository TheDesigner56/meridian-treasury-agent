# Meridian Treasury Agent

**An autonomous agent that runs a real corporate treasury — multi-entity, multi-currency, on stablecoin rails — with hard safety limits it cannot bypass.**

Built for the **Hermes Agent Accelerated Business Hackathon** — NVIDIA × Stripe × Nous Research.

> **Try it live:** open the dashboard, click **Daily check**, then **Emergency draw**, then type `emergency draw $300,000` and watch NemoClaw block it.
> The entire agent runs **client-side** — every judge gets a working, interactive demo from a single link, no backend to spin up.

---

## The problem it solves

A CFO at a multi-entity fund spends hours a week doing mechanical, error-prone money movement:

- Cash sits idle in fiat across USD / EUR / GBP accounts instead of earning yield.
- Payroll, taxes, lease, and LP distributions come due on different days in different currencies.
- Emergencies need cash *now*, but moving large sums also needs guardrails.

Meridian is the agent that does this autonomously — and, critically, **does it safely**. It earns (sweeps idle cash to yield), spends (settles obligations), and runs real operations (forecasts, FX, emergency liquidity) — exactly the "agents that earn, spend, and run real operations" the hackathon asked for.

## What it does

| Capability | What the agent does |
|---|---|
| **Monitors** | Tracks fiat / stablecoin / yield balances across 3 entities and 3 currencies in real time |
| **Settles** | Pays scheduled obligations (payroll, NI, lease, tax, distributions) via Stripe, pulling from the yield buffer only when fiat is short |
| **Earns** | Sweeps idle fiat above each entity's threshold → USDC → Stripe Treasury yield at 4.85% APY |
| **Defends** | Runs every transaction through **NemoClaw** pre-flight checks; hard limits cannot be overridden |
| **Reasons** | Routes natural-language requests and risk assessment through **Nemotron 3 Ultra** |
| **Forecasts** | 14-day liquidity outlook across all currencies, normalized to USD |
| **Responds** | Emergency liquidity draws in plain English ("emergency draw £40K") |

## How it maps to the judging criteria

**Usefulness** — Treasury management is a concrete, expensive CFO pain. The agent automates the full daily loop (reconcile → settle → sweep) and handles real edge cases: cross-currency draws, shortfalls covered from yield, approval gates on large outflows.

**Viability** — Built on rails that already exist: Stripe Treasury for stablecoin yield/settlement, Stripe Skills for payments and SaaS provisioning, NVIDIA NemoClaw for safety, Nemotron 3 Ultra for reasoning. The same engine logic ships in two forms — a Python production engine (`skill/treasury_engine.py`, real Nemotron inference) and an in-browser engine (instant, zero-trust demo) — so it's deployable as a real backend *and* trivially demoable.

**Presentation** — A live, fully interactive financial dashboard. Click any control and watch balances animate, obligations settle, the NemoClaw audit trail populate, and Nemotron reasoning stream in. A **Reset demo** button replays the whole story.

## Hackathon integrations

| Sponsor requirement | Integration | How |
|---|---|---|
| **NemoClaw** (NVIDIA safety) | `NemoClawSafety` engine | 8 pre-flight checks on every transaction: transaction limit, emergency-draw cap, approval threshold, cross-entity limit, off-hours/weekend, rate limit, 3σ anomaly detection, SHA-256 audit trail. Hard limits **block**; soft limits **flag**. |
| **Nemotron 3 Ultra** (NVIDIA model) | `nemotron_inference()` | Routes NL intent parsing and risk assessment through Nemotron. Falls back to local reasoning when no key is set, so the demo always works. |
| **NVIDIA agent skills** | Docs-routing pattern | Applies NemoClaw's network-policy / safety-preset pattern at the application layer. |
| **Stripe Skills for Hermes** | stripe-link-cli + stripe-projects + Stripe Treasury | Agent pays obligations via Stripe Link, provisions SaaS via Stripe Projects, and earns yield on USDC via Stripe Treasury. |

## NemoClaw safety rails

Every transaction passes 8 pre-flight checks before any funds move:

1. **Transaction limit** — $500K max per transaction (hard block)
2. **Emergency-draw cap** — $250K max per emergency draw (hard block)
3. **Approval threshold** — >$100K flagged for CFO review
4. **Cross-entity limit** — >$100K cross-entity requires approval
5. **Off-hours / weekend** — large transactions outside business hours monitored
6. **Rate limit** — max 10 transactions per entity per hour (hard block)
7. **Anomaly detection** — transactions >3σ from the entity's history flagged
8. **Audit trail** — every transaction logged with a SHA-256 audit hash

The hard limits are not advisory. `emergency draw $300,000` is **blocked** — no funds move — because it exceeds the $250K cap. That's the safety story NemoClaw is built for, applied to money.

## Architecture

```
meridian-treasury-agent/
├── public/                     # Vercel static deploy (the live demo)
│   ├── index.html              # Dashboard + full in-browser treasury engine
│   └── treasury_state.json     # Seed state
├── dashboard/index.html        # Source dashboard (synced to public/)
├── skill/
│   ├── SKILL.md                # Hermes skill definition
│   └── treasury_engine.py      # Python production engine (NemoClaw + Nemotron + treasury logic)
├── demo-data/                  # State + clean backup for demo resets
├── server.py                   # Local server: serves dashboard + runs the Python engine live
├── demo-script.md              # Demo video script
└── vercel.json                 # Static deploy config
```

**Two engines, one logic.** The browser runs a faithful port of `treasury_engine.py` so the deployed demo is instant and self-contained. The Python engine is the production reference: same operations, same NemoClaw checks, plus real Nemotron 3 Ultra inference and persistent state.

## Run it

### Live demo (static)
The `public/` directory is a complete static app. Open `public/index.html`, or deploy the repo to any static host (Vercel auto-detects `public/`). No backend required.

### Local, with the real Python engine
```bash
# 1. Seed the state file
cp demo-data/treasury_state_backup.json demo-data/treasury_state.json

# 2. Start the server (serves the dashboard + runs the engine)
python3 server.py
#    → http://127.0.0.1:8499

# 3. Or drive the engine directly from the CLI
python3 skill/treasury_engine.py status
python3 skill/treasury_engine.py check
python3 skill/treasury_engine.py sweep
python3 skill/treasury_engine.py emergency 50000 USD
python3 skill/treasury_engine.py emergency 300000     # NemoClaw blocks this
python3 skill/treasury_engine.py forecast 14
```

### Enable real Nemotron 3 Ultra inference
```bash
export OLLAMA_API_KEY="..."   # Nemotron 3 Ultra via Ollama Cloud
```
Without a key, the agent falls back to deterministic local reasoning — the demo always runs.

## License

MIT — built for the Hermes Agent Accelerated Business Hackathon.
