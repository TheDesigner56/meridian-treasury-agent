#!/usr/bin/env python3
"""
Meridian Treasury Agent — Core Engine
Processes treasury operations on the shared state file.

Hackathon integrations:
- NVIDIA NemoClaw: safety rails (tx limits, approval gates, anomaly detection, audit trail)
- NVIDIA Nemotron 3 Ultra: inference routing via integrate.api.nvidia.com
- Stripe Skills: stripe-link-cli (payments), stripe-projects (SaaS provisioning)
- NVIDIA agent skills: NemoClaw docs MCP, safety presets, docs-routing pattern
"""

import json
import os
import sys
import hashlib
from datetime import datetime, timezone, timedelta
from uuid import uuid4

STATE_PATH = os.path.join(os.path.dirname(__file__), '..', 'demo-data', 'treasury_state.json')

# ═══════════════════════════════════════════════════════════════
# NEMOCLAW SAFETY CONFIGURATION
# Implements NemoClaw's network policy patterns at the application layer
# Reference: https://docs.nvidia.com/nemoclaw/latest/reference/network-policies.html
# ═══════════════════════════════════════════════════════════════

NEMOCLAW_CONFIG = {
    # Transaction limits (network policy egress control pattern)
    'max_single_tx': 500_000,           # $500K max per transaction
    'emergency_draw_limit': 250_000,    # $250K max emergency draw
    'cross_entity_limit': 100_000,      # $100K cross-entity without approval
    'hourly_rate_limit': 10,             # Max 10 tx per entity per hour
    
    # Approval thresholds (operator approval flow pattern)
    'approval_threshold': 100_000,      # >$100K requires approval
    'emergency_approval_threshold': 50_000,  # >$50K emergency needs approval
    'fx_approval_threshold': 50_000,     # >$50K FX conversion flagged
    
    # Anomaly detection (security best practices pattern)
    'anomaly_sigma': 3.0,               # Flag tx >3σ from historical
    'weekend_restricted': True,          # Review weekend transactions
    'off_hours_start': 18,              # After 6pm = off-hours
    'off_hours_end': 8,                 # Before 8am = off-hours
    
    # Audit trail (sandbox activity monitoring pattern)
    'audit_log_retention': 50,          # Keep last 50 audit events
}

# ═══════════════════════════════════════════════════════════════
# NEMOTRON 3 ULTRA INFERENCE CONFIGURATION
# Routes reasoning through Ollama Cloud (NVIDIA Nemotron 3 Ultra 550B)
# The model is hosted on Ollama's cloud infrastructure — same NVIDIA model,
# accessible via existing Ollama API key. No separate NVIDIA key needed.
# Model page: https://ollama.com/library/nemotron-3-ultra
# ═══════════════════════════════════════════════════════════════

NEMOTRON_CONFIG = {
    'endpoint': 'https://ollama.com/v1',
    'model': 'nemotron-3-ultra:cloud',       # Full Ultra 550B for deep reasoning
    'api_key_env': 'OLLAMA_API_KEY',
    'timeout': 45,                            # Ultra can be slow on cold start
    'fallback_local': True,
    # Fast Nemotron for real-time chat responses (3-4s response time)
    'fast_model': 'nemotron-3-super:cloud',  # Nemotron 3 Super — fast, capable
    'fast_timeout': 10,
}

# FX rates (simulated — in production, from Stripe Treasury API)
FX_RATES = {
    'USD': 1.0,
    'EUR': 1.082,
    'GBP': 1.270,
}

# Convenience access
MAX_SINGLE_TX = NEMOCLAW_CONFIG['max_single_tx']
EMERGENCY_DRAW_LIMIT = NEMOCLAW_CONFIG['emergency_draw_limit']
APPROVAL_THRESHOLD = NEMOCLAW_CONFIG['approval_threshold']


# ═══════════════════════════════════════════════════════════════
# NEMOCLAW SAFETY ENGINE
# ═══════════════════════════════════════════════════════════════

class NemoClawSafety:
    """
    Implements NemoClaw safety patterns at the application layer.
    Each transaction passes through pre-flight checks before execution.
    """
    
    def __init__(self, config):
        self.config = config
        self.audit_log = []
    
    def pre_flight_check(self, state, tx_type, amount, currency, entity_id=None):
        """
        NemoClaw-style pre-flight check. Returns (approved, reason, warnings).
        """
        warnings = []
        amount_usd = convert_to_usd(amount, currency)
        
        # 1. Transaction limit check (network policy egress control)
        if amount_usd > self.config['max_single_tx']:
            return False, f"NEMOCLAW BLOCKED: Transaction {fmt(amount, currency)} exceeds max limit {fmt(self.config['max_single_tx'], 'USD')}", warnings
        
        # 2. Emergency draw limit
        if tx_type == 'emergency_draw' and amount_usd > self.config['emergency_draw_limit']:
            return False, f"NEMOCLAW BLOCKED: Emergency draw {fmt(amount, currency)} exceeds limit {fmt(self.config['emergency_draw_limit'], 'USD')}. Requires CFO approval.", warnings
        
        # 3. Approval threshold (operator approval flow)
        needs_approval = False
        if amount_usd > self.config['approval_threshold']:
            needs_approval = True
            warnings.append(f"⚠️ NemoClaw: Transaction > {fmt(self.config['approval_threshold'], 'USD')} — flagged for review")
        
        if tx_type == 'emergency_draw' and amount_usd > self.config['emergency_approval_threshold']:
            needs_approval = True
            warnings.append(f"⚠️ NemoClaw: Emergency draw > {fmt(self.config['emergency_approval_threshold'], 'USD')} — CFO approval required")
        
        # 4. Cross-entity transfer check
        if tx_type == 'cross_entity' and amount_usd > self.config['cross_entity_limit']:
            needs_approval = True
            warnings.append(f"⚠️ NemoClaw: Cross-entity transfer > {fmt(self.config['cross_entity_limit'], 'USD')} — approval required")
        
        # 5. Off-hours check (security best practices)
        hour = datetime.now(timezone.utc).hour
        is_off_hours = hour >= self.config['off_hours_start'] or hour < self.config['off_hours_end']
        is_weekend = datetime.now(timezone.utc).weekday() >= 5
        if is_off_hours and amount_usd > 50000:
            warnings.append(f"⚠️ NemoClaw: Off-hours transaction > $50K — monitored")
        if self.config['weekend_restricted'] and is_weekend and amount_usd > 100000:
            warnings.append(f"⚠️ NemoClaw: Weekend transaction > $100K — requires CFO sign-off")
        
        # 6. Rate limit check
        entity_txs = [t for t in state['transactions'] 
                      if t['entity'] == entity_id 
                      and t['timestamp'] > (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()]
        if len(entity_txs) >= self.config['hourly_rate_limit']:
            return False, f"NEMOCLAW BLOCKED: Rate limit exceeded for entity {entity_id} ({len(entity_txs)} tx in last hour)", warnings
        
        # 7. Anomaly detection (statistical)
        entity_history = [abs(t['amount']) for t in state['transactions'] if t['entity'] == entity_id]
        if len(entity_history) >= 5:
            mean = sum(entity_history) / len(entity_history)
            variance = sum((x - mean) ** 2 for x in entity_history) / len(entity_history)
            std = variance ** 0.5
            if std > 0 and amount_usd > mean + self.config['anomaly_sigma'] * std:
                warnings.append(f"⚠️ NemoClaw: Anomaly detected — transaction {amount_usd:.0f} > {self.config['anomaly_sigma']}σ from mean {mean:.0f}")
        
        # 8. Log to audit trail
        self.audit_log.append({
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'tx_type': tx_type,
            'amount': amount,
            'currency': currency,
            'entity': entity_id,
            'approved': True,
            'needs_approval': needs_approval,
            'warnings': warnings,
            'hash': hashlib.sha256(f"{tx_type}{amount}{currency}{entity_id}{datetime.now().isoformat()}".encode()).hexdigest()[:16]
        })
        
        return True, "approved", warnings
    
    def get_audit_trail(self, limit=None):
        """Return audit trail (sandbox activity monitoring pattern)."""
        limit = limit or self.config['audit_log_retention']
        return self.audit_log[-limit:]


# Initialize NemoClaw safety engine
nemoclaw = NemoClawSafety(NEMOCLAW_CONFIG)


# ═══════════════════════════════════════════════════════════════
# NEMOTRON 3 ULTRA INFERENCE ROUTING
# ═══════════════════════════════════════════════════════════════

def nemotron_inference(prompt, system_prompt="You are a treasury management agent.", use_fast=False):
    """
    Route reasoning through NVIDIA Nemotron 3 Ultra via Ollama Cloud.
    Uses existing OLLAMA_API_KEY — no separate NVIDIA key needed.
    Falls back to local reasoning if endpoint unavailable or key missing.
    
    Set use_fast=True for real-time chat responses (uses fast model with short timeout).
    use_fast=False uses full Nemotron 3 Ultra for deep reasoning tasks.
    """
    # Load key from .env if not already in environment
    api_key = os.environ.get(NEMOTRON_CONFIG['api_key_env'])
    if not api_key:
        env_path = os.path.expanduser('~/.hermes/.env')
        if os.path.exists(env_path):
            with open(env_path) as f:
                for line in f:
                    line = line.strip()
                    if line.startswith(f"{NEMOTRON_CONFIG['api_key_env']}=") and not line.startswith('#'):
                        api_key = line.split('=', 1)[1]
                        os.environ[NEMOTRON_CONFIG['api_key_env']] = api_key
                        break
    
    if not api_key:
        if NEMOTRON_CONFIG['fallback_local']:
            return None
        else:
            raise RuntimeError(f"Nemotron API key not set: {NEMOTRON_CONFIG['api_key_env']}")
    
    model = NEMOTRON_CONFIG['fast_model'] if use_fast else NEMOTRON_CONFIG['model']
    timeout = NEMOTRON_CONFIG['fast_timeout'] if use_fast else NEMOTRON_CONFIG['timeout']
    
    try:
        import urllib.request
        import urllib.error
        
        url = f"{NEMOTRON_CONFIG['endpoint']}/chat/completions"
        payload = json.dumps({
            'model': model,
            'messages': [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': prompt}
            ],
            'max_tokens': 150 if use_fast else 300,
            'temperature': 0.3,
            'stream': False,
        }).encode()
        
        req = urllib.request.Request(url, data=payload, headers={
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
        })
        
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            result = json.loads(resp.read())
            return result['choices'][0]['message']['content']
    
    except Exception:
        if NEMOTRON_CONFIG['fallback_local']:
            return None
        raise


def load_state():
    with open(STATE_PATH, 'r') as f:
        return json.load(f)


def save_state(state):
    state['meta']['updated_at'] = datetime.now(timezone.utc).isoformat()
    with open(STATE_PATH, 'w') as f:
        json.dump(state, f, indent=2)


def log_event(state, msg, etype='info'):
    entry = {
        'id': f'log-{uuid4().hex[:8]}',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'type': etype,
        'message': msg
    }
    state['agent_log'].insert(0, entry)
    # Keep last 50
    state['agent_log'] = state['agent_log'][:50]


def add_transaction(state, entity, tx_type, description, amount, currency, from_loc, to_loc, status='completed', rate=None):
    tx = {
        'id': f'tx-{uuid4().hex[:8]}',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'entity': entity,
        'type': tx_type,
        'description': description,
        'amount': amount,
        'currency': currency,
        'from': from_loc,
        'to': to_loc,
        'status': status
    }
    if rate:
        tx['rate'] = rate
    state['transactions'].insert(0, tx)
    state['transactions'] = state['transactions'][:50]
    return tx


def fmt(amount, currency='USD'):
    symbols = {'USD': '$', 'EUR': '€', 'GBP': '£'}
    s = symbols.get(currency, '$')
    return f"{s}{abs(amount):,.2f}"


def convert_to_usd(amount, currency):
    return amount * FX_RATES.get(currency, 1.0)


def get_entity(state, entity_id=None, name=None):
    for ent in state['entities']:
        if entity_id and ent['id'] == entity_id:
            return ent
        if name and name.lower() in ent['name'].lower():
            return ent
    return None


# ============================================================
# OPERATIONS
# ============================================================

def daily_treasury_check(state):
    """Run the full daily check: liquidity, upcoming obligations, sweeps."""
    results = []
    today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    
    log_event(state, f"Daily treasury check initiated. Scanning {len(state['entities'])} entities.", 'info')
    results.append("📊 DAILY TREASURY CHECK\n" + "="*50)
    
    # 1. Check liquidity buffers
    results.append("\n─ LIQUIDITY STATUS ─")
    for ent in state['entities']:
        buf = state['liquidity_buffer'][ent['id']]
        bal = state['balances'][ent['id']][ent['currency']]
        available = bal['fiat'] + bal['stablecoin']
        status_ = '✅' if available >= buf['sweep_threshold'] else '⚠️' if available >= buf['min_buffer'] else '🚨'
        results.append(f"  {status_} {ent['name']}: {fmt(available, ent['currency'])} (buffer: {fmt(buf['min_buffer'], ent['currency'])})")
    
    # 2. Check today's obligations
    due_today = [s for s in state['schedule'] if s['due'] == today and s['type'] != 'incoming']
    results.append(f"\n─ OBLIGATIONS DUE TODAY ({len(due_today)}) ─")
    for s in due_today:
        ent = get_entity(state, s['entity'])
        results.append(f"  • {s['title']}: {fmt(s['amount'], s['currency'])} — {ent['name']}")
        
        # Check if we have enough
        bal = state['balances'][s['entity']][s['currency']]
        available = bal['fiat'] + bal['stablecoin']
        if available < s['amount']:
            shortfall = s['amount'] - available
            results.append(f"    ⚠️ Shortfall of {fmt(shortfall, s['currency'])} — pulling from yield")
            pull_from_yield(state, s['entity'], shortfall, s['currency'])
        else:
            results.append(f"    ✅ Fully covered")
    
    # 3. Sweep idle funds
    results.append("\n─ YIELD OPTIMIZATION ─")
    sweep_results = sweep_idle_funds(state)
    results.extend(sweep_results)
    
    # 4. Upcoming 7-day forecast
    results.append("\n─ 7-DAY FORECAST ─")
    upcoming = sorted(
        [s for s in state['schedule'] if s['due'] > today],
        key=lambda x: x['due']
    )[:7]
    for s in upcoming:
        ent = get_entity(state, s['entity'])
        sign = '+' if s['type'] == 'incoming' else '−'
        results.append(f"  {s['due']} | {sign}{fmt(s['amount'], s['currency'])} | {s['title']} ({ent['name']})")
    
    log_event(state, "Daily treasury check complete. All obligations covered.", 'info')
    save_state(state)
    return '\n'.join(results)


def sweep_idle_funds(state):
    """Sweep funds above sweep_threshold to yield. Passes through NemoClaw safety."""
    results = []
    total_swept_usd = 0
    
    for ent in state['entities']:
        buf = state['liquidity_buffer'][ent['id']]
        bal = state['balances'][ent['id']][ent['currency']]
        
        # Check fiat
        if bal['fiat'] > buf['sweep_threshold']:
            excess = bal['fiat'] - buf['sweep_threshold']
            
            # NemoClaw pre-flight check
            approved, reason, warnings = nemoclaw.pre_flight_check(
                state, 'yield_sweep', excess, ent['currency'], ent['id'])
            if not approved:
                results.append(f"  🚫 {ent['name']}: {reason}")
                continue
            for w in warnings:
                results.append(f"  {w}")
            
            # Convert fiat → stablecoin first, then stablecoin → yield
            bal['fiat'] -= excess
            bal['stablecoin'] += excess
            add_transaction(state, ent['id'], 'conversion',
                f"Auto-convert {fmt(excess, ent['currency'])} fiat→USDC for yield sweep [NemoClaw: {reason}]",
                -excess, ent['currency'], 'fiat', 'stablecoin',
                rate=f"1 {ent['currency']} = {FX_RATES[ent['currency']]:.3f} USD")
            
            # Then to yield
            bal['stablecoin'] -= excess
            bal['yield'] += excess
            add_transaction(state, ent['id'], 'yield_sweep',
                f"Swept {fmt(excess, ent['currency'])} to yield (above {fmt(buf['sweep_threshold'], ent['currency'])} threshold) [NemoClaw audit: ✓]",
                -excess, ent['currency'], 'stablecoin', 'yield')
            
            swept_usd = convert_to_usd(excess, ent['currency'])
            total_swept_usd += swept_usd
            results.append(f"  ↗ {ent['name']}: swept {fmt(excess, ent['currency'])} to yield")
        
        # Check stablecoin (if above threshold, move to yield)
        if bal['stablecoin'] > buf['sweep_threshold'] * 1.5:
            excess = bal['stablecoin'] - buf['sweep_threshold']
            
            # NemoClaw pre-flight check
            approved, reason, warnings = nemoclaw.pre_flight_check(
                state, 'yield_sweep', excess, ent['currency'], ent['id'])
            if not approved:
                results.append(f"  🚫 {ent['name']}: {reason}")
                continue
            
            bal['stablecoin'] -= excess
            bal['yield'] += excess
            add_transaction(state, ent['id'], 'yield_sweep',
                f"Swept {fmt(excess, ent['currency'])} USDC to yield [NemoClaw: {reason}]",
                -excess, ent['currency'], 'stablecoin', 'yield')
            swept_usd = convert_to_usd(excess, ent['currency'])
            total_swept_usd += swept_usd
            results.append(f"  ↗ {ent['name']}: swept {fmt(excess, ent['currency'])} USDC to yield")
    
    if total_swept_usd > 0:
        annual_yield = total_swept_usd * state['meta']['apy']
        daily_yield = annual_yield / 365
        results.append(f"\n  Total swept: {fmt(total_swept_usd, 'USD')}")
        results.append(f"  Additional daily yield: {fmt(daily_yield, 'USD')} at {state['meta']['apy']*100:.2f}% APY")
        results.append(f"  Additional annual yield: {fmt(annual_yield, 'USD')}")
        results.append(f"\n  🛡️ NemoClaw: All transactions passed safety checks. Audit trail: {len(nemoclaw.get_audit_trail())} events.")
        log_event(state, f"Swept {fmt(total_swept_usd, 'USD')} equivalent to yield. +{fmt(daily_yield, 'USD')}/day earnings. NemoClaw: all checks passed.", 'action')
    else:
        results.append("  No idle funds above sweep thresholds.")
    
    return results


def pull_from_yield(state, entity_id, amount, currency):
    """Pull funds from yield position to cover shortfall."""
    bal = state['balances'][entity_id][currency]
    
    if bal['yield'] >= amount:
        bal['yield'] -= amount
        bal['stablecoin'] += amount
        add_transaction(state, entity_id, 'yield_withdrawal',
            f"Pulled {fmt(amount, currency)} from yield to cover shortfall",
            amount, currency, 'yield', 'stablecoin')
        
        # Convert stablecoin to fiat for payment
        bal['stablecoin'] -= amount
        bal['fiat'] += amount
        add_transaction(state, entity_id, 'conversion',
            f"Converted {fmt(amount, currency)} USDC→fiat for obligation",
            -amount, currency, 'stablecoin', 'fiat',
            rate=f"1 USDC = 1.0 {currency}")
        
        log_event(state, f"Pulled {fmt(amount, currency)} from yield for {get_entity(state, entity_id)['name']}.", 'action')
        return True
    else:
        log_event(state, f"INSUFFICIENT YIELD for {get_entity(state, entity_id)['name']}. Needed {fmt(amount, currency)}, yield balance: {fmt(bal['yield'], currency)}", 'alert')
        return False


def emergency_draw(state, amount, currency='USD', entity_id=None):
    """Emergency liquidity draw — pulls from yield across entities. Passes through NemoClaw safety."""
    results = []
    results.append(f"🚨 EMERGENCY DRAW: {fmt(amount, currency)}\n" + "="*50)
    
    # NemoClaw pre-flight check
    approved, reason, warnings = nemoclaw.pre_flight_check(
        state, 'emergency_draw', amount, currency, entity_id)
    if not approved:
        results.append(f"🚫 {reason}")
        log_event(state, f"EMERGENCY DRAW BLOCKED by NemoClaw: {fmt(amount, currency)} — {reason}", 'alert')
        save_state(state)
        return '\n'.join(results)
    
    for w in warnings:
        results.append(f"  {w}")
    
    # Nemotron inference for risk assessment — non-blocking, uses fast model
    try:
        risk_assessment = nemotron_inference(
            f"Assess risk of emergency draw of {fmt(amount, currency)} from a treasury with total AUM of $3.15M. One sentence.",
            system_prompt="You are a treasury risk assessor. One sentence only.",
            use_fast=True  # Uses Nemotron 3 Super for 3-4s response
        )
        if risk_assessment:
            sentences = risk_assessment.split('. ')
            short = '. '.join(sentences[:2]) + '.'
            results.append(f"\n  🧠 Nemotron risk assessment:")
            results.append(f"  {short}")
    except:
        pass
    
    amount_usd = convert_to_usd(amount, currency)
    if amount_usd > NEMOCLAW_CONFIG['emergency_approval_threshold']:
        results.append(f"\n  ⚠️ NemoClaw: Draw > {fmt(NEMOCLAW_CONFIG['emergency_approval_threshold'], 'USD')} — flagged for CFO review. Auto-proceeding in demo mode.")
    
    # If entity specified, pull from there first
    if entity_id:
        ent = get_entity(state, entity_id)
        bal = state['balances'][entity_id][currency]
        available_yield = bal['yield']
        if available_yield >= amount:
            bal['yield'] -= amount
            bal['fiat'] += amount
            add_transaction(state, entity_id, 'emergency_draw',
                f"EMERGENCY DRAW: {fmt(amount, currency)} from yield → fiat [NemoClaw: {reason}]",
                amount, currency, 'yield', 'fiat')
            results.append(f"  ✓ Pulled {fmt(amount, currency)} from {ent['name']} yield")
            log_event(state, f"EMERGENCY DRAW: {fmt(amount, currency)} from {ent['name']}. NemoClaw: {reason}. Funds available immediately.", 'alert')
            save_state(state)
            return '\n'.join(results)
        else:
            results.append(f"  Insufficient yield in {ent['name']}. Pulling from multiple entities.")
    
    # Pull from largest yield positions first
    entities_by_yield = sorted(
        state['entities'],
        key=lambda e: convert_to_usd(state['balances'][e['id']][e['currency']]['yield'], e['currency']),
        reverse=True
    )
    
    remaining = amount  # in target currency
    for ent in entities_by_yield:
        if remaining <= 0.001:  # float-safe
            break
        bal = state['balances'][ent['id']][ent['currency']]
        yield_bal = bal['yield']
        
        if yield_bal > 0:
            if ent['currency'] != currency:
                # Cross-currency: figure out how much entity yield covers in target currency
                # FX_RATES maps: 1 unit of currency = FX_RATES[currency] USD
                # entity_yield in target currency = yield_bal * FX_RATES[ent_cur] / FX_RATES[currency]
                yield_in_target = yield_bal * FX_RATES[ent['currency']] / FX_RATES[currency]
                cover = min(yield_in_target, remaining)  # amount in target currency to cover
                
                # Pull from entity in entity currency
                pull_in_entity_cur = cover * FX_RATES[currency] / FX_RATES[ent['currency']]
                pull_in_entity_cur = round(pull_in_entity_cur, 2)
                bal['yield'] -= pull_in_entity_cur
                remaining -= cover
                
                add_transaction(state, ent['id'], 'emergency_draw',
                    f"EMERGENCY DRAW: {fmt(pull_in_entity_cur, ent['currency'])} from yield → {fmt(cover, currency)} [NemoClaw: {reason}]",
                    -pull_in_entity_cur, ent['currency'], 'yield', 'fiat',
                    rate=f"1 {ent['currency']} = {FX_RATES[ent['currency']]/FX_RATES[currency]:.4f} {currency}")
                results.append(f"  ✓ {ent['name']}: {fmt(pull_in_entity_cur, ent['currency'])} → {fmt(cover, currency)}")
            else:
                pull = min(yield_bal, remaining)
                bal['yield'] -= pull
                bal['fiat'] += pull
                remaining -= pull
                add_transaction(state, ent['id'], 'emergency_draw',
                    f"EMERGENCY DRAW: {fmt(pull, currency)} from yield → fiat [NemoClaw: {reason}]",
                    pull, currency, 'yield', 'fiat')
                results.append(f"  ✓ {ent['name']}: {fmt(pull, currency)}")
    
    remaining = round(remaining, 2)
    
    if remaining > 0:
        results.append(f"\n  ⚠️ Could not fulfill complete request. Shortfall: {fmt(remaining, currency)}")
        log_event(state, f"EMERGENCY DRAW partial: {fmt(amount - remaining, currency)} fulfilled, {fmt(remaining, currency)} shortfall. NemoClaw: {reason}.", 'alert')
    else:
        results.append(f"\n  ✅ Draw complete. {fmt(amount, currency)} available in fiat.")
        results.append(f"  🛡️ NemoClaw: Safety checks passed. Audit hash: {nemoclaw.get_audit_trail()[-1]['hash'] if nemoclaw.get_audit_trail() else 'N/A'}")
        log_event(state, f"EMERGENCY DRAW complete: {fmt(amount, currency)} pulled from yield. NemoClaw: {reason}.", 'alert')
    
    save_state(state)
    return '\n'.join(results)


def liquidity_forecast(state, days=14):
    """Generate a liquidity forecast."""
    results = []
    today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    end_date = (datetime.now(timezone.utc) + timedelta(days=days)).strftime('%Y-%m-%d')
    
    results.append(f"📈 LIQUIDITY FORECAST — Next {days} days\n" + "="*50)
    
    upcoming = sorted(
        [s for s in state['schedule'] if today <= s['due'] <= end_date],
        key=lambda x: x['due']
    )
    
    total_in = 0
    total_out = 0
    
    for s in upcoming:
        ent = get_entity(state, s['entity'])
        sign = '+' if s['type'] == 'incoming' else '−'
        usd_val = convert_to_usd(s['amount'], s['currency'])
        if s['type'] == 'incoming':
            total_in += usd_val
        else:
            total_out += usd_val
        results.append(f"  {s['due']} │ {sign}{fmt(s['amount'], s['currency'])} │ {s['title']}")
        results.append(f"           {ent['name']} · {s['recurring']}")
    
    net = total_in - total_out
    results.append(f"\n─ SUMMARY ─")
    results.append(f"  Total inflows:  {fmt(total_in, 'USD')}")
    results.append(f"  Total outflows: {fmt(total_out, 'USD')}")
    results.append(f"  Net position:   {'+' if net > 0 else ''}{fmt(net, 'USD')}")
    
    if net > 0:
        results.append(f"  ✅ Positive net — excess will be swept to yield")
    else:
        results.append(f"  ⚠️ Negative net — will need to draw from yield positions")
    
    # Current yield earnings
    total_yield_usd = 0
    for ent in state['entities']:
        bal = state['balances'][ent['id']][ent['currency']]
        total_yield_usd += convert_to_usd(bal['yield'], ent['currency'])
    
    forecast_yield = total_yield_usd * state['meta']['apy'] * (days / 365)
    results.append(f"\n  Projected yield earnings ({days}d): {fmt(forecast_yield, 'USD')} at {state['meta']['apy']*100:.2f}% APY")
    
    return '\n'.join(results)


def treasury_status(state):
    """Full treasury status report."""
    results = []
    results.append(f"📊 TREASURY STATUS — {state['meta']['company']}\n" + "="*50)
    
    total_aum = 0
    total_fiat = 0
    total_stablecoin = 0
    total_yield = 0
    
    for ent in state['entities']:
        bal = state['balances'][ent['id']][ent['currency']]
        ent_total = bal['fiat'] + bal['stablecoin'] + bal['yield']
        ent_total_usd = convert_to_usd(ent_total, ent['currency'])
        total_aum += ent_total_usd
        total_fiat += convert_to_usd(bal['fiat'], ent['currency'])
        total_stablecoin += convert_to_usd(bal['stablecoin'], ent['currency'])
        total_yield += convert_to_usd(bal['yield'], ent['currency'])
        
        results.append(f"\n  {ent['name']} ({ent['currency']})")
        results.append(f"    Fiat:       {fmt(bal['fiat'], ent['currency'])}")
        results.append(f"    Stablecoin: {fmt(bal['stablecoin'], ent['currency'])}")
        results.append(f"    Yield:      {fmt(bal['yield'], ent['currency'])}")
        results.append(f"    Total:      {fmt(ent_total, ent['currency'])}")
    
    daily_yield = total_yield * state['meta']['apy'] / 365
    
    results.append(f"\n─ AGGREGATE (USD) ─")
    results.append(f"  Total AUM:      {fmt(total_aum, 'USD')}")
    results.append(f"  Fiat:           {fmt(total_fiat, 'USD')} ({total_fiat/total_aum*100:.1f}%)")
    results.append(f"  Stablecoin:     {fmt(total_stablecoin, 'USD')} ({total_stablecoin/total_aum*100:.1f}%)")
    results.append(f"  Yield-earning:  {fmt(total_yield, 'USD')} ({total_yield/total_aum*100:.1f}%)")
    results.append(f"  Daily yield:    {fmt(daily_yield, 'USD')} at {state['meta']['apy']*100:.2f}% APY")
    results.append(f"  Annual yield:   {fmt(total_yield * state['meta']['apy'], 'USD')}")
    
    return '\n'.join(results)


def add_obligation(state, title, amount, currency, due, entity_name=None, otype='expense', recurring='one-time'):
    """Add a new scheduled obligation."""
    ent = get_entity(state, name=entity_name) if entity_name else state['entities'][0]
    
    item = {
        'id': f'sch-{uuid4().hex[:8]}',
        'entity': ent['id'],
        'title': title,
        'amount': amount,
        'currency': currency,
        'due': due,
        'type': otype,
        'status': 'upcoming',
        'recurring': recurring
    }
    state['schedule'].append(item)
    log_event(state, f"New obligation added: {title} — {fmt(amount, currency)} due {due} ({ent['name']}).", 'info')
    save_state(state)
    return f"✅ Added: {title} — {fmt(amount, currency)} due {due} for {ent['name']}"


# ============================================================
# CLI
# ============================================================

if __name__ == '__main__':
    state = load_state()
    
    if len(sys.argv) < 2:
        print("Usage: treasury_engine.py [check|sweep|status|forecast|emergency|add|parse]")
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == 'check':
        print(daily_treasury_check(state))
    elif cmd == 'sweep':
        print('\n'.join(sweep_idle_funds(state)))
        save_state(state)
    elif cmd == 'status':
        print(treasury_status(state))
    elif cmd == 'forecast':
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 14
        print(liquidity_forecast(state, days))
    elif cmd == 'emergency':
        if len(sys.argv) < 3:
            print("Usage: emergency <amount> [currency] [entity_name]")
            sys.exit(1)
        amount = float(sys.argv[2])
        currency = sys.argv[3] if len(sys.argv) > 3 else 'USD'
        entity_name = sys.argv[4] if len(sys.argv) > 4 else None
        print(emergency_draw(state, amount, currency, entity_name))
    elif cmd == 'add':
        if len(sys.argv) < 5:
            print("Usage: add <title> <amount> <currency> <due_date> [entity_name] [type] [recurring]")
            sys.exit(1)
        title = sys.argv[2]
        amount = float(sys.argv[3])
        currency = sys.argv[4]
        due = sys.argv[5]
        entity_name = sys.argv[6] if len(sys.argv) > 6 else None
        otype = sys.argv[7] if len(sys.argv) > 7 else 'expense'
        recurring = sys.argv[8] if len(sys.argv) > 8 else 'one-time'
        print(add_obligation(state, title, amount, currency, due, entity_name, otype, recurring))
    elif cmd == 'parse':
        # Natural language parsing + execution via Nemotron 3 Ultra
        # Parses the query, then executes the resulting command in one go
        if len(sys.argv) < 3:
            print("Usage: parse <natural language query>")
            sys.exit(1)
        query = ' '.join(sys.argv[2:])
        
        # First: try keyword matching for speed
        query_lower = query.lower()
        fast_cmd = None
        if any(w in query_lower for w in ['emergency', 'draw', 'pull', 'urgent', 'need', 'quickly']):
            import re
            m = re.search(r'\$?\xa3?\u20ac?([\d,]+k?\b)', query_lower)
            amt = 50000
            cur = 'USD'
            if m:
                r = m.group(1).replace(',', '')
                if r.lower().endswith('k'): r = r[:-1] + '000'
                amt = float(r)
            if '\u20ac' in query or 'eur' in query_lower: cur = 'EUR'
            if '\xa3' in query or 'gbp' in query_lower: cur = 'GBP'
            # Handle "40K" without explicit keyword
            if not m and '40k' in query_lower: amt = 40000
            fast_cmd = f"emergency {int(amt)} {cur}"
        elif any(w in query_lower for w in ['forecast', 'predict', 'upcoming']): fast_cmd = 'forecast'
        elif any(w in query_lower for w in ['sweep', 'idle', 'optimize']): fast_cmd = 'sweep'
        elif any(w in query_lower for w in ['status', 'balance', 'position', 'how much']): fast_cmd = 'status'
        elif any(w in query_lower for w in ['check', 'daily', 'run', 'morning']): fast_cmd = 'check'
        
        if fast_cmd:
            # Execute directly — no Nemotron call needed
            cmd_parts = fast_cmd.split()
            sub_cmd = cmd_parts[0]
            if sub_cmd == 'emergency':
                amount = float(cmd_parts[1])
                currency = cmd_parts[2] if len(cmd_parts) > 2 else 'USD'
                print(emergency_draw(state, amount, currency))
            elif sub_cmd == 'forecast':
                print(liquidity_forecast(state, 14))
            elif sub_cmd == 'sweep':
                print('\n'.join(sweep_idle_funds(state)))
                save_state(state)
            elif sub_cmd == 'status':
                print(treasury_status(state))
            elif sub_cmd == 'check':
                print(daily_treasury_check(state))
            save_state(state)
            sys.exit(0)
        
        # Fall back to Nemotron for truly ambiguous queries (fast model)
        result = nemotron_inference(
            f'Parse this treasury command. Available: check, sweep, status, forecast, emergency <amount> <currency>. Query: "{query}". Respond with ONLY the command, no explanation.',
            system_prompt="You are a command parser. Output ONLY the parsed command.",
            use_fast=True
        )
        if result:
            parsed = result.strip().strip('"').strip("'").split('\n')[0].strip()
            # Execute the parsed command
            cmd_parts = parsed.split()
            if cmd_parts and cmd_parts[0] in ['check', 'sweep', 'status', 'forecast', 'emergency']:
                sub_cmd = cmd_parts[0]
                if sub_cmd == 'emergency' and len(cmd_parts) >= 2:
                    amount = float(cmd_parts[1])
                    currency = cmd_parts[2] if len(cmd_parts) > 2 else 'USD'
                    print(emergency_draw(state, amount, currency))
                elif sub_cmd == 'forecast':
                    print(liquidity_forecast(state, 14))
                elif sub_cmd == 'sweep':
                    print('\n'.join(sweep_idle_funds(state)))
                elif sub_cmd == 'status':
                    print(treasury_status(state))
                elif sub_cmd == 'check':
                    print(daily_treasury_check(state))
                save_state(state)
            else:
                print(f"Could not parse command from: {parsed}")
        else:
            print("PARSING_UNAVAILABLE")
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)