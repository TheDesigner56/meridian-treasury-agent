# Meridian Treasury Agent

**Autonomous treasury management agent for multi-entity, multi-currency operations using stablecoins.**

Built for the **Hermes Agent Accelerated Business Hackathon** — NVIDIA × Stripe × Nous Research.

## What It Does

An autonomous agent that manages corporate treasury operations:

- **Monitors** balances across multiple entities and currencies (USD, EUR, GBP)
- **Schedules** liquidity for upcoming obligations (payroll, expenses, taxes, distributions)
- **Optimizes** by sweeping idle funds to yield (fiat → stablecoin → yield at 4.85% APY)
- **Responds** to emergency draw requests via natural language
- **Converts** between fiat and stablecoins as needed
- **Reports** via natural language through a dashboard chat interface

## Hackathon Integrations

| Requirement | Integration | How |
|------------|------------|-----|
| **NemoClaw** (NVIDIA safety) | `NemoClawSafety` class | Pre-flight checks on every transaction: tx limits, approval gates, anomaly detection, rate limiting, off-hours/weekend flags, audit trail with SHA-256 hashes |
| **Nemotron 3 Ultra** (NVIDIA model) | `nemotron_inference()` | Routes reasoning through `integrate.api.nvidia.com/v1` using `nvidia/nemotron-3-ultra-550b` for natural language understanding and risk assessment |
| **NVIDIA agent skills** | NemoClaw docs MCP | References NemoClaw's docs MCP server (`docs.nvidia.com/nemoclaw/_mcp/server`), safety presets, and docs-routing skill pattern |
| **Stripe Skills** | stripe-link-cli + stripe-projects | Installed Hermes skills for agent-driven payments via Stripe Link virtual cards, SaaS provisioning via Stripe Projects, and stablecoin treasury operations |

## Architecture

```
hermes-treasury-agent/
├── dashboard/
│   └── index.html          # Live HTML dashboard (dark financial terminal)
├── demo-data/
│   ├── treasury_state.json  # Shared state (agent reads/writes, dashboard polls)
│   └── treasury_state_backup.json  # Clean state for demo resets
├── skill/
│   ├── SKILL.md             # Hermes skill documentation
│   └── treasury_engine.py   # Python engine (NemoClaw + Nemotron + treasury logic)
├── server.py                # HTTP server (dashboard + API)
├── demo-script.md           # 2:30 demo video script
└── README.md
```

## Quick Start

```bash
# 1. Start the server
cd ~/hermes-treasury-agent
python3 server.py

# 2. Open the dashboard
open http://127.0.0.1:8499

# 3. Chat with the agent
#    Type: "Run daily treasury check"
#    Click: "⚡ Emergency Draw"
#    Click: "↗ Sweep Idle"
```

## How It Works

1. **State File** (`treasury_state.json`) — single source of truth for balances, schedule, transactions, and agent log
2. **Engine** (`treasury_engine.py`) — processes treasury operations, passes every transaction through NemoClaw safety checks
3. **Server** (`server.py`) — serves dashboard HTML and exposes API endpoints (`/api/state`, `/api/run?cmd=...`)
4. **Dashboard** (`index.html`) — polls state every 5s, sends chat commands to engine, renders real-time updates

## NemoClaw Safety Rails

Every transaction passes through 8 pre-flight checks:

1. **Transaction limit** — $500K max per transaction
2. **Emergency draw limit** — $250K max per emergency draw
3. **Approval threshold** — >$100K flagged for review
4. **Cross-entity limit** — >$100K cross-entity requires approval
5. **Off-hours check** — >$50K after 6pm/weekends monitored
6. **Rate limit** — max 10 transactions per entity per hour
7. **Anomaly detection** — flags transactions >3σ from historical pattern
8. **Audit trail** — every transaction logged with SHA-256 hash

## Stripe Integration

- **stripe-link-cli** — agent can make payments via Stripe Link virtual cards or Shared Payment Tokens (SPT). Every spend gated by in-app approval.
- **stripe-projects** — agent can provision SaaS services (Neon, Twilio, Vercel) and manage billing.
- **Stripe Treasury** — stablecoin payments (USDC), stablecoin subscriptions, and stablecoin yield (public preview).

## Nemotron 3 Ultra

The agent routes reasoning through NVIDIA Endpoints:

```bash
# Set API key to enable Nemotron inference
export NVIDIA_INFERENCE_API_KEY="nvapi-..."
```

Without the key, the agent falls back to local reasoning. With it, natural language queries and risk assessments are processed by Nemotron 3 Ultra 550B.

## License

MIT — Built for the Hermes Agent Accelerated Business Hackathon.