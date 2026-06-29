"""
Vercel serverless function: GET /api/run?cmd=<command>
Runs a treasury engine command and returns the output + updated state.

This is the serverless version of the local server.py run_command endpoint.
It imports the treasury engine, runs the command, and returns results.
"""
import json
import os
import sys
import subprocess
from http.server import BaseHTTPRequestHandler

# Add the skill directory to path so we can import the engine
SKILL_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'skill')
sys.path.insert(0, SKILL_DIR)

def handler(req):
    """Handle GET /api/run?cmd=<command> — execute treasury command."""
    from urllib.parse import urlparse, parse_qs
    
    # Parse query string
    parsed = urlparse(req.path + '?' + req.query_string if hasattr(req, 'query_string') else req.path)
    params = parse_qs(parsed.query)
    cmd = params.get('cmd', [''])[0]
    
    if not cmd:
        return {
            'statusCode': 400,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': 'No command provided'})
        }
    
    # Security: only allow specific commands
    allowed = ['check', 'sweep', 'status', 'forecast', 'emergency', 'add', 'parse']
    base_cmd = cmd.split()[0] if cmd.split() else ''
    
    if base_cmd not in allowed:
        return {
            'statusCode': 403,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': f'Command not allowed: {base_cmd}'})
        }
    
    try:
        # Run the engine
        engine_path = os.path.join(SKILL_DIR, 'treasury_engine.py')
        result = subprocess.run(
            [sys.executable, engine_path] + cmd.split(),
            capture_output=True, text=True, timeout=30,
            cwd=os.path.dirname(os.path.dirname(__file__))
        )
        output = result.stdout
        if result.returncode != 0:
            output = result.stderr
        
        # Read updated state
        state_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'demo-data', 'treasury_state.json')
        with open(state_path, 'r') as f:
            state = json.load(f)
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
            },
            'body': json.dumps({
                'output': output,
                'state': state,
                'success': result.returncode == 0
            })
        }
    except subprocess.TimeoutExpired:
        return {
            'statusCode': 504,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': 'Command timed out (30s)', 'output': 'Command timed out.'})
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': str(e)})
        }