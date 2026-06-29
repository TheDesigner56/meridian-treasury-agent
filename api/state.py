"""
Vercel serverless function: GET /api/state
Returns the current treasury state as JSON.
"""
import json
import os
from http.server import BaseHTTPRequestHandler

def handler(req):
    """Handle GET /api/state — return treasury state."""
    # In production, this would read from a database or the engine
    # For the demo, we read from the state file bundled with the deployment
    state_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'demo-data', 'treasury_state.json')
    
    try:
        with open(state_path, 'r') as f:
            state = json.load(f)
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
            },
            'body': json.dumps(state)
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
            },
            'body': json.dumps({'error': str(e)})
        }