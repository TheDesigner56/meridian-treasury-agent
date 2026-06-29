"""
Vercel serverless function: GET /api/state
Returns the current treasury state as JSON.
"""
import json
import os
from typing import Dict, Any

def handler(request):
    """Handle GET /api/state — return treasury state."""
    # Try multiple paths — works for both local dev and Vercel
    possible_paths = [
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'demo-data', 'treasury_state.json'),
        os.path.join(os.getcwd(), 'demo-data', 'treasury_state.json'),
        os.path.join(os.path.dirname(os.path.dirname(__file__)), 'demo-data', 'treasury_state.json'),
    ]
    
    for state_path in possible_paths:
        try:
            with open(state_path, 'r') as f:
                state = json.load(f)
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'GET, OPTIONS',
                },
                'body': json.dumps(state)
            }
        except:
            continue
    
    return {
        'statusCode': 404,
        'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
        'body': json.dumps({'error': 'State file not found'})
    }