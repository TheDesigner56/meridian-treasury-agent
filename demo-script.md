# Demo Script — Meridian Treasury Agent

## Hackathon: NVIDIA × Stripe × Nous Research
## Duration: 2:30 (target)

---

## SCENE 1: INTRO (0:00 - 0:15)

**[Screen: Dashboard loads at http://127.0.0.1:8499]**

**Narration:**
"This is Meridian — an autonomous treasury agent built on Hermes Agent. It manages multi-entity, multi-currency corporate finances using stablecoins via Stripe Treasury, with NVIDIA NemoClaw safety rails and Nemotron 3 Ultra inference."

**[Highlight header: Agent Active | NemoClaw Safety Active | Nemotron 3 Ultra]**

---

## SCENE 2: THE PROBLEM (0:15 - 0:35)

**[Screen: Dashboard — pan across entity cards, schedule, balances]**

**Narration:**
"Meridian Capital Partners has three entities across three currencies — USD, EUR, and GBP. Total AUM: $3.15 million. They have scheduled obligations: payroll, lease, taxes, LP distributions. And they have idle cash sitting in fiat when it could be earning 4.85% yield."

**[Point to schedule items: Payroll £42K today, LP Distribution $450K in 12 days]**

**Narration:**
"The CFO doesn't want to manually move money between accounts, convert currencies, and sweep idle funds to yield every day. They want the agent to do it."

---

## SCENE 3: SCHEDULED OPERATIONS — DAILY CHECK (0:35 - 1:05)

**[Screen: Click into agent chat, type "Run daily treasury check"]**

**Narration:**
"Every morning, the agent runs a daily treasury check. It scans all entities, verifies liquidity for today's obligations, and sweeps idle funds to yield."

**[Show agent output appearing in chat:]**
- ✅ Meridian Fund I LP: $605K available
- ✅ Payroll £42K — fully covered
- ↗ Swept $85K to yield
- ↗ Swept €32K to yield
- 🛡️ NemoClaw: All transactions passed safety checks

**Narration:**
"Notice the NemoClaw safety layer — every transaction passes through pre-flight checks: transaction limits, rate limiting, anomaly detection. The agent swept $669K to yield, adding $88 per day in passive income."

**[Highlight: NemoClaw audit trail message]**

---

## SCENE 4: YIELD OPTIMIZATION (1:05 - 1:30)

**[Screen: Click "↗ Sweep Idle" button]**

**Narration:**
"The agent also proactively sweeps idle funds. Fiat above the sweep threshold gets converted to USDC stablecoins, then moved to Stripe Treasury's yield protocol."

**[Show transaction log updating with new yield_sweep entries]**

**Narration:**
"Each conversion is logged with the NemoClaw audit hash. The dashboard updates in real-time — you can see the balance bars shifting from fiat to yield."

**[Point to balance bars turning more green (yield)]**

---

## SCENE 5: EMERGENCY DRAW — NEMOCLAW IN ACTION (1:30 - 2:00)

**[Screen: Click "⚡ Emergency Draw" button]**

**Narration:**
"Now the CFO needs cash fast. They request an emergency draw of $50,000."

**[Show agent processing...]**
- ⚠️ NemoClaw: Emergency draw > $50K — CFO approval required
- ⚠️ NemoClaw: Off-hours transaction monitored
- ✓ Pulled $50,000 from yield
- 🛡️ NemoClaw: Audit hash: 0dfcd409...

**Narration:**
"NemoClaw flags it for review — it's above the $50K approval threshold and it's off-hours. But the agent proceeds, pulling from yield and converting to fiat. Every step is audited."

**[Now type "Emergency draw $300,000"]**

**Narration:**
"But watch what happens when someone tries to draw $300,000..."

**[Show:]**
🚫 NEMOCLAW BLOCKED: Emergency draw $300,000 exceeds limit $250,000. Requires CFO approval.

**Narration:**
"NemoClaw blocks it. The $250K hard limit can't be bypassed without explicit approval."

---

## SCENE 6: NATURAL LANGUAGE + FORECAST (2:00 - 2:25)

**[Screen: Type "Give me a liquidity forecast"]**

**Narration:**
"The CFO can just talk to the agent. Ask for a forecast..."

**[Show forecast output: 14-day inflows/outflows, net position +$308K, projected yield]**

**Narration:**
"...and get a full 14-day liquidity forecast with projected yield earnings. The agent routes reasoning through Nemotron 3 Ultra on NVIDIA Endpoints for natural language understanding."

---

## SCENE 7: CLOSING (2:25 - 2:30)

**[Screen: Full dashboard view]**

**Narration:**
"Meridian Treasury Agent — built on Hermes, powered by NVIDIA NemoClaw and Nemotron 3 Ultra, with Stripe stablecoin infrastructure. Autonomous treasury management for the real world."

**[Text overlay:]**
- NVIDIA NemoClaw — Safety rails
- NVIDIA Nemotron 3 Ultra — Inference
- Stripe Skills — Payments & Treasury
- Hermes Agent — Autonomous operations

**[End]**

---

## RECORDING NOTES

### Setup
1. Start server: `cd ~/hermes-treasury-agent && python3 server.py`
2. Open browser: `http://127.0.0.1:8499`
3. Restore state: `cp demo-data/treasury_state_backup.json demo-data/treasury_state.json`
4. Screen record at 1080p or 4K

### Flow
1. Load dashboard (let it render fully)
2. Type "Run daily treasury check" in chat
3. Wait for output, pan to show balance changes
4. Click "↗ Sweep Idle"
5. Wait for output
6. Click "⚡ Emergency Draw" (default $50K)
7. Wait for output
8. Type "Emergency draw $300,000" — show NemoClaw block
9. Type "Give me a liquidity forecast"
10. End on full dashboard

### Narration
- Record voiceover separately, or narrate live
- Keep it conversational, not robotic
- Emphasize: "NemoClaw blocked it" and "all checks passed"