---
name: treasury-agent
description: Autonomous treasury management agent for multi-entity, multi-currency operations using stablecoins via Stripe Treasury. Integrates NVIDIA NemoClaw safety patterns, Nemotron 3 Ultra inference routing, NVIDIA agent skills, and Stripe Skills for Hermes. Manages scheduled obligations, yield optimization, and emergency liquidity draws.
version: 2.0.0
author: Hermes Agent Hackathon Submission
metadata:
  hermes:
    tags: [treasury, stablecoin, stripe, nvidia, nemoclaw, nemotron, finance, hackathon]
    related_skills: [stripe-link-cli, stripe-projects]
---

# Treasury Agent — NVIDIA × Stripe × Nous Research Hackathon

## Hackathon Integration Map

This agent uses ALL four required integrations from the Hermes Agent Accelerated Business Hackathon:

| Hackathon Requirement | Integration | How |
|----------------------|------------|-----|
| **NemoClaw** (NVIDIA safety) | Safety rails module | Implements NemoClaw's network policy patterns: transaction limits, approval gates, anomaly detection, audit logging — the same controls NemoClaw enforces at the sandbox level, applied to treasury operations |
| **Nemotron 3 Ultra** (NVIDIA speed) | NVIDIA Endpoints inference | Routes agent reasoning through `integrate.api.nvidia.com` using Nemotron 3 Ultra 550B model for fast treasury decisions |
| **NVIDIA agent skills** | Docs-routing skill pattern | Uses NemoClaw's agent skill pattern — the agent can query NVIDIA's docs MCP server for treasury/finance guidance and applies NemoClaw-style safety presets |
| **Stripe Skills for Hermes** | stripe-link-cli + stripe-projects | Real Stripe integration — agent can make payments via Stripe Link virtual cards, provision SaaS services via Stripe Projects, and manage billing |

## Architecture

```
┌──────────────────────────────────────────────────┐
│           Hermes Agent (JARVIS)                  │
│                                                  │
│  ┌────────────────────────────────────────────┐  │
│  │     Treasury Agent Skill (this file)       │  │
│  │  • Liquidity Planner                       │  │
│  │  • Yield Optimizer                         │  │
│  │  • Payment Scheduler                       │  │
│  │  • Emergency Handler                       │  │
│  │  • FX Converter                            │  │
│  └──────────┬─────────────────────────────────┘  │
│             │                                    │
│  ┌──────────▼──────────┐  ┌───────────────────┐  │
│  │  NemoClaw Safety     │  │  Nemotron 3 Ultra │  │
│  │  • Tx limits         │  │  inference.local   │  │
│  │  • Approval gates    │  │  → integrate.api   │  │
│  │  • Anomaly detection │  │    .nvidia.com     │  │
│  │  • Audit trail       │  │  Nemotron-3-Ultra  │  │
│  └──────────┬──────────┘  └─────────┬─────────┘  │
│             │                        │            │
│  ┌──────────▼──────────────────────▼─────────┐  │
│  │   treasury_state.json (shared state)      │  │
│  └──────────┬───────────────────────────────┘  │
│             │ fetch (5s poll)                    │
│  ┌──────────▼───────────────────────────────┐  │
│  │   Dashboard (HTML/JS)                     │  │
│  └───────────────────────────────────────────┘  │
│                                                  │
│  ┌───────────────────────────────────────────┐  │
│  │  Stripe Skills (installed)                │  │
│  │  • stripe-link-cli → virtual card payments│  │
│  │  • stripe-projects → SaaS provisioning    │  │
│  │  • Stripe Treasury → stablecoin yield     │  │
│  │  • Stripe API → FX conversion             │  │
│  └───────────────────────────────────────────┘  │
│                                                  │
│  ┌───────────────────────────────────────────┐  │
│  │  NVIDIA Agent Skills                       │  │
│  │  • NemoClaw docs MCP server                │  │
│  │  • Safety presets (network policy tiers)   │  │
│  │  • Docs-routing skill pattern               │  │
│  └───────────────────────────────────────────┘  │
└──────────────────────────────────────────────────┘
```

## NemoClaw Safety Implementation

The agent implements NemoClaw's safety patterns at the application layer:

### Transaction Limits (NemoClaw Network Policy Pattern)
- **Max single transaction**: $500K (blocked above, requires CFO approval above $100K)
- **Emergency draw limit**: $250K per event
- **Cross-entity transfer limit**: $100K without explicit approval
- **Hourly rate limit**: Max 10 transactions per entity per hour

### Approval Gates (NemoClaw Operator Approval Pattern)
- Transactions above $100K trigger approval request
- Emergency draws above $50K require CFO confirmation
- Cross-currency conversions above $50K are flagged
- All transactions logged with full audit trail (NemoClaw sandbox activity pattern)

### Anomaly Detection (NemoClaw Security Best Practices Pattern)
- Transactions >3σ from historical pattern are flagged
- Unusual timing (weekend, off-hours) triggers review
- New payee addresses require verification
- Velocity checks on outgoing payments

## Nemotron Inference Routing

The agent routes reasoning through NVIDIA Nemotron models via Ollama Cloud:

### Models Used

| Model | Use Case | Response Time |
|-------|----------|---------------|
| **Nemotron 3 Ultra 550B** (`nemotron-3-ultra:cloud`) | Deep reasoning, complex analysis | 30-45s (cold start) |
| **Nemotron 3 Super** (`nemotron-3-super:cloud`) | Real-time chat, risk assessment, NL parsing | 2-4s |

### Configuration

```python
NEMOTRON_CONFIG = {
    'endpoint': 'https://ollama.com/v1',
    'model': 'nemotron-3-ultra:cloud',       # Full Ultra for deep reasoning
    'fast_model': 'nemotron-3-super:cloud',  # Fast Nemotron for real-time chat
    'api_key_env': 'OLLAMA_API_KEY',          # Uses existing Ollama key
}
```

The agent uses Nemotron for:
- Natural language intent parsing (chat → treasury command) — fast model
- Real-time risk assessment for emergency draws — fast model
- Deep liquidity forecasting reasoning — full Ultra model
- Yield optimization strategy selection — full Ultra model
- Liquidity forecasting reasoning
- Risk assessment for large transactions
- Yield optimization strategy selection

## Stripe Skills Integration

### stripe-link-cli (Installed)
- Agent can make payments via Stripe Link virtual cards
- One-time-use virtual cards for operational expenses
- Shared Payment Tokens (SPT) for recurring payments
- Every spend gated by in-app approval (NemoClaw pattern)

### stripe-projects (Installed)
- Agent can provision SaaS services (Neon, Twilio, Vercel)
- Credential management across providers
- Billing management from one place

### Stripe Treasury (Stablecoins)
- Stablecoin payments (USDC) settling as fiat
- Stablecoin subscriptions for recurring revenue
- Stablecoins in Treasury (public preview) — receive, store, send
- Fiat-to-crypto onramp for conversions

## State File

The shared state file (`treasury_state.json`) is the single source of truth.

## Commands

### Scheduled Operations
- **"Run daily treasury check"** — scans all entities, checks liquidity, sweeps excess
- **"Prepare for [obligation]"** — ensures liquidity for specific scheduled item
- **"Add obligation: [title] [amount] [currency] [due date]"** — adds to schedule

### Yield Optimization
- **"Sweep idle funds"** — moves excess above thresholds to yield
- **"Optimize yield"** — converts non-base currencies to USDC for yield

### Emergency
- **"Emergency draw [amount] [currency]"** — pulls from yield, converts, executes
- **"Pull [amount] from [entity]"** — targeted draw

### Reporting
- **"Treasury status"** — full position report
- **"Liquidity forecast"** — 14-day forecast of inflows/outflows

## Hackathon Submission

**Team**: Hermes Agent Hackathon
**Built with**: NVIDIA NemoClaw + Nemotron 3 Ultra + Stripe Skills + Hermes Agent
**Demo**: 1-3 minute video showing autonomous treasury management across multi-entity, multi-currency operations with stablecoins