# Demo Script — Meridian Treasury Agent

**Hackathon:** NVIDIA × Stripe × Nous Research · **Target length:** 2:00–2:30

Everything below runs **client-side in the dashboard** — no backend, no waiting. Hit **Reset demo** (top-right) before recording so the story starts clean.

---

## SCENE 1 — INTRO (0:00–0:15)

**[Dashboard loaded. Pan the header + hero balance.]**

> "This is Meridian — an autonomous treasury agent built on Hermes. It runs a real multi-entity, multi-currency corporate treasury on stablecoin rails, with NVIDIA NemoClaw safety limits and Nemotron 3 Ultra reasoning."

**[Point to the four integration pills: NemoClaw · Nemotron 3 Ultra · Stripe Treasury · Stripe Skills.]**

---

## SCENE 2 — THE SETUP (0:15–0:35)

**[Pan across the three entity cards and the schedule.]**

> "Meridian Capital Partners has three entities across USD, EUR, and GBP — $3.15M under management. Payroll and Employer NI are due *today* on the UK entity, but it only holds £38K in fiat. Idle cash elsewhere is sitting flat when it could be earning 4.85%."

---

## SCENE 3 — THE DAILY LOOP (0:35–1:10)

**[Click "Daily check".]**

> "Every morning the agent runs one check. Watch what happens."

**[Nemotron reasoning streams in, then results:]**
- Verifies liquidity per entity
- Settles payroll + NI — pulling the shortfall from the yield buffer, paying via Stripe
- Sweeps remaining idle fiat → USDC → Stripe Treasury yield

**[Point to the schedule: payroll + NI now show "paid ✓" and strike through. Balances animate. Activity log fills.]**

> "It settled today's obligations, covered the shortfall from yield, and swept the rest — all in one pass. Every line is logged with a NemoClaw audit hash."

---

## SCENE 4 — NEMOCLAW IN ACTION (1:10–1:50)

**[Click "Emergency draw" ($50K).]**

> "Now the CFO needs cash fast — a $50K emergency draw."

**[NemoClaw pre-flight panel runs all 8 checks; draw completes from yield, audit hash shown.]**

> "Eight pre-flight checks run before a dollar moves. This one's above the $50K threshold, so it's flagged for review — but it clears and pulls from the highest-yield position first."

**[Type `emergency draw $300,000` and send.]**

> "But watch the guardrail."

**[Show: 🚫 NEMOCLAW BLOCKED — exceeds $250K limit. No funds move.]**

> "NemoClaw blocks it. The $250K hard cap can't be bypassed by the agent. That's the safety story — applied to money."

---

## SCENE 5 — TALK TO IT (1:50–2:15)

**[Type `give me a 14-day liquidity forecast`.]**

> "And you just talk to it. Nemotron parses the request..."

**[Forecast streams: inflows vs outflows, net position, projected yield.]**

> "...a full 14-day forecast across three currencies. The Q3 management fee and the LP-047 capital call more than cover the bridge repayment and the Q2 distribution."

---

## SCENE 6 — CLOSE (2:15–2:30)

**[Full dashboard.]**

> "Meridian — an agent that earns, spends, and runs real treasury operations. Built on Hermes, NVIDIA NemoClaw and Nemotron 3 Ultra, and Stripe stablecoin infrastructure."

**[Overlay:]**
- NVIDIA NemoClaw — safety rails
- NVIDIA Nemotron 3 Ultra — reasoning
- Stripe Treasury + Skills — yield, payments, SaaS
- Hermes Agent — autonomous operations

---

## RECORDING NOTES

- **Reset** before each take (top-right "↺ Reset demo").
- Record at 1080p+; the dark terminal aesthetic reads well at high bitrate.
- The whole demo is client-side — clicks are instant; no need to wait on a server.
- Beats to land on camera: **payroll → "paid ✓"**, **$300K → "NEMOCLAW BLOCKED"**.
- Optional: enable `OLLAMA_API_KEY` and run `server.py` to show *real* Nemotron inference in the Python engine for a "this is production-real" aside.
