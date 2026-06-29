#!/usr/bin/env python3
"""
Meridian Treasury Dashboard Server
Serves the HTML dashboard and provides a live API for state updates.
When the treasury engine modifies treasury_state.json, the dashboard
auto-refreshes via polling.
"""

import http.server
import json
import os
import socketserver
import sys
import subprocess
from urllib.parse import urlparse, parse_qs

PORT = 8499
BASE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)))
DASHBOARD_DIR = os.path.join(BASE_DIR, 'dashboard')
DATA_DIR = os.path.join(BASE_DIR, 'demo-data')
STATE_FILE = os.path.join(DATA_DIR, 'treasury_state.json')
ENGINE = os.path.join(BASE_DIR, 'skill', 'treasury_engine.py')


class TreasuryHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DASHBOARD_DIR, **kwargs)

    def do_GET(self):
        parsed = urlparse(self.path)
        
        if parsed.path == '/api/state':
            self.serve_state()
        elif parsed.path == '/api/run':
            self.run_command(parsed.query)
        elif parsed.path == '/' or parsed.path == '/index.html':
            self.serve_file('index.html')
        elif parsed.path == '/treasury_state.json':
            self.serve_state_file()
        else:
            super().do_GET()

    def serve_state(self):
        try:
            with open(STATE_FILE, 'r') as f:
                state = json.load(f)
            self.send_json(state)
        except Exception as e:
            self.send_json({'error': str(e)}, status=500)

    def serve_state_file(self):
        self.serve_file('treasury_state.json', data_dir=True)

    def serve_file(self, filename, data_dir=False):
        path = os.path.join(DATA_DIR if data_dir else DASHBOARD_DIR, filename)
        try:
            with open(path, 'r') as f:
                content = f.read()
            content_type = 'text/html' if filename.endswith('.html') else 'application/json'
            self.send_response(200)
            self.send_header('Content-Type', content_type)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(content.encode())
        except FileNotFoundError:
            self.send_error(404)

    def run_command(self, query_string):
        params = parse_qs(query_string)
        cmd = params.get('cmd', [''])[0]
        
        if not cmd:
            self.send_json({'error': 'No command provided'}, status=400)
            return
        
        # Safety: only allow specific commands
        allowed = ['check', 'sweep', 'status', 'forecast', 'emergency', 'add', 'parse']
        base_cmd = cmd.split()[0] if cmd.split() else ''
        
        if base_cmd not in allowed:
            self.send_json({'error': f'Command not allowed: {base_cmd}'}, status=403)
            return
        
        try:
            result = subprocess.run(
                [sys.executable, ENGINE] + cmd.split(),
                capture_output=True, text=True, timeout=60,
                cwd=BASE_DIR
            )
            output = result.stdout
            if result.returncode != 0:
                output = result.stderr
            
            # Read updated state
            with open(STATE_FILE, 'r') as f:
                state = json.load(f)
            
            self.send_json({
                'output': output,
                'state': state,
                'success': result.returncode == 0
            })
        except subprocess.TimeoutExpired:
            self.send_json({'error': 'Command timed out (60s)', 'output': 'Command timed out. Nemotron inference may be slow on first call.'}, status=504)
        except Exception as e:
            self.send_json({'error': str(e)}, status=500)

    def send_json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def log_message(self, format, *args):
        # Suppress default logging
        pass


def main():
    # Also copy state file to dashboard dir for file:// access
    try:
        import shutil
        shutil.copy2(STATE_FILE, os.path.join(DASHBOARD_DIR, 'treasury_state.json'))
    except:
        pass
    
    with socketserver.TCPServer(('127.0.0.1', PORT), TreasuryHandler) as httpd:
        print(f"╔══════════════════════════════════════════════╗")
        print(f"║  Meridian Treasury Dashboard                  ║")
        print(f"║  http://127.0.0.1:{PORT}                        ║")
        print(f"╚══════════════════════════════════════════════╝")
        print(f"\n  Dashboard:  http://127.0.0.1:{PORT}")
        print(f"  State API:  http://127.0.0.1:{PORT}/api/state")
        print(f"  Run cmd:    http://127.0.0.1:{PORT}/api/run?cmd=check")
        print(f"\n  Press Ctrl+C to stop.\n")
        httpd.serve_forever()


if __name__ == '__main__':
    main()