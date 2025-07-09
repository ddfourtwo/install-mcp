#!/usr/bin/env python3
"""
Multi-Secret Web Collector for MCP servers
Collects multiple secrets in one session via web interface
"""

import sys
import os
import json
import time
import threading
import webbrowser
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
import socket

class MultiSecretCollectorHandler(BaseHTTPRequestHandler):
    def __init__(self, *args, server_name=None, secrets=None, env_file=None, server_instance=None, **kwargs):
        self.server_name = server_name
        self.secrets = secrets  # List of dicts with 'name' and 'description'
        self.env_file = env_file
        self.server_instance = server_instance
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            # Build form fields for all secrets
            secret_fields = []
            for i, secret in enumerate(self.secrets):
                # Check if already collected
                existing = self.check_existing_secret(secret['name'])
                field_html = f"""
                <div class="secret-group">
                    <label for="secret_{i}">
                        <strong>{secret['description']}</strong>
                        <span class="var-name">{secret['name']}</span>
                    </label>
                    <input type="password" id="secret_{i}" name="{secret['name']}" 
                           placeholder="Enter {secret['description']}" 
                           {"value='[Already Set]' readonly" if existing else "required"}>
                    <div class="show-hide">
                        <input type="checkbox" id="show_{i}" onchange="toggleSecret({i})">
                        <label for="show_{i}">Show</label>
                    </div>
                </div>
                """
                secret_fields.append(field_html)
            
            html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>MCP Multi-Secret Collection</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 600px;
            margin: 50px auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        .container {{
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            margin-bottom: 10px;
        }}
        .server-name {{
            color: #666;
            font-size: 18px;
            margin-bottom: 20px;
        }}
        .description {{
            background: #e8f4f8;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
            border-left: 4px solid #0084ff;
        }}
        .secret-group {{
            margin-bottom: 25px;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 5px;
        }}
        .secret-group label {{
            display: block;
            margin-bottom: 8px;
            color: #333;
        }}
        .var-name {{
            font-family: monospace;
            background: #e3e3e3;
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 14px;
            margin-left: 10px;
        }}
        input[type="password"], input[type="text"] {{
            width: 100%;
            padding: 12px;
            font-size: 16px;
            border: 2px solid #ddd;
            border-radius: 5px;
            margin-bottom: 8px;
            box-sizing: border-box;
        }}
        input[type="password"]:focus, input[type="text"]:focus {{
            outline: none;
            border-color: #0084ff;
        }}
        input[readonly] {{
            background: #e9ecef;
            color: #6c757d;
        }}
        button {{
            background: #0084ff;
            color: white;
            border: none;
            padding: 12px 30px;
            font-size: 16px;
            border-radius: 5px;
            cursor: pointer;
            width: 100%;
        }}
        button:hover {{
            background: #0066cc;
        }}
        .warning {{
            background: #fff3cd;
            padding: 10px;
            border-radius: 5px;
            margin-bottom: 20px;
            font-size: 14px;
            color: #856404;
        }}
        .show-hide {{
            display: flex;
            align-items: center;
            gap: 5px;
            font-size: 14px;
        }}
        .progress {{
            background: #d4edda;
            padding: 10px;
            border-radius: 5px;
            margin-bottom: 20px;
            color: #155724;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Secure Multi-Secret Collection</h1>
        <div class="server-name">for {self.server_name}</div>
        
        <div class="description">
            <strong>This server requires {len(self.secrets)} secret{"s" if len(self.secrets) > 1 else ""}.</strong><br>
            Please fill in all required fields below.
        </div>
        
        <div class="warning">
            This page is served locally on your machine. Your secrets will be saved to:<br>
            <code>{self.env_file}</code>
        </div>
        
        <form method="POST" action="/save" id="secretForm">
            {"".join(secret_fields)}
            
            <button type="submit">Save All Secrets</button>
        </form>
    </div>
    
    <script>
        function toggleSecret(index) {{
            const input = document.getElementById('secret_' + index);
            const checkbox = document.getElementById('show_' + index);
            if (input.readOnly) return;
            input.type = checkbox.checked ? 'text' : 'password';
        }}
        
        // Auto-close after 10 minutes
        setTimeout(() => {{
            document.body.innerHTML = '<div class="container"><h1>Session Expired</h1><p>Please run the command again.</p></div>';
        }}, 600000);
    </script>
</body>
</html>
"""
            self.wfile.write(html.encode())
        
        elif self.path == '/success':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            saved_count = len([s for s in self.secrets if s['name'] in self.server_instance.collected_secrets])
            
            html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Success - MCP Multi-Secret Collection</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 500px;
            margin: 50px auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        .container {{
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            text-align: center;
        }}
        .success {{
            color: #4caf50;
            font-size: 48px;
            margin-bottom: 20px;
        }}
        h1 {{
            color: #333;
            margin-bottom: 20px;
        }}
        p {{
            color: #666;
            margin-bottom: 20px;
        }}
        .summary {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
            text-align: left;
        }}
        .summary ul {{
            margin: 10px 0;
            padding-left: 20px;
        }}
        .close {{
            color: #999;
            font-size: 14px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Secrets Saved Successfully!</h1>
        <div class="summary">
            <strong>Saved {saved_count} secret{"s" if saved_count != 1 else ""} to {self.env_file.name}:</strong>
            <ul>
                {"".join([f"<li>{s['name']}</li>" for s in self.secrets if s['name'] in self.server_instance.collected_secrets])}
            </ul>
        </div>
        <p>You can now close this window and return to your terminal.</p>
        <p class="close">This window will close automatically in 5 seconds...</p>
    </div>
    <script>
        setTimeout(() => {{
            window.close();
        }}, 5000);
    </script>
</body>
</html>
"""
            self.wfile.write(html.encode())
            # Signal that collection is complete
            self.server.all_collected = True
    
    def do_POST(self):
        if self.path == '/save':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode('utf-8')
            params = parse_qs(post_data)
            
            try:
                # Collect all provided secrets
                for secret in self.secrets:
                    secret_name = secret['name']
                    if secret_name in params and params[secret_name][0]:
                        value = params[secret_name][0]
                        if value != '[Already Set]':
                            self.server_instance.collected_secrets[secret_name] = value
                
                # Save all to .env file
                if self.server_instance.collected_secrets:
                    self.save_secrets_to_env()
                
                # Redirect to success page
                self.send_response(302)
                self.send_header('Location', '/success')
                self.end_headers()
                
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                self.wfile.write(f"Error: {str(e)}".encode())
    
    def check_existing_secret(self, secret_name):
        """Check if a secret already exists in the env file"""
        if self.env_file.exists():
            try:
                with open(self.env_file, 'r') as f:
                    for line in f:
                        if line.strip().startswith(f"{secret_name}="):
                            return True
            except:
                pass
        return False
    
    def save_secrets_to_env(self):
        """Save all collected secrets to the env file"""
        env_file_path = Path(self.env_file)
        env_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Read existing content
        lines = []
        existing_secrets = {}
        
        if env_file_path.exists():
            with open(env_file_path, 'r') as f:
                for line in f:
                    if '=' in line and not line.strip().startswith('#'):
                        key = line.split('=', 1)[0].strip()
                        existing_secrets[key] = line
                    else:
                        lines.append(line)
        
        # Update with new secrets
        for name, value in self.server_instance.collected_secrets.items():
            existing_secrets[name] = f"{name}={value}\n"
        
        # Write back all secrets
        with open(env_file_path, 'w') as f:
            # Write non-secret lines first
            for line in lines:
                f.write(line)
            # Then write all secrets
            for line in existing_secrets.values():
                f.write(line)
        
        # Set restrictive permissions
        os.chmod(env_file_path, 0o600)
    
    def log_message(self, format, *args):
        # Suppress request logging
        pass

def find_free_port():
    """Find a free port on localhost"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        s.listen(1)
        port = s.getsockname()[1]
    return port

def run_multi_server(server_name, secrets, env_file):
    """Run the web server for multiple secrets"""
    port = find_free_port()
    
    # Create the server first
    server = HTTPServer(('localhost', port), None)
    server.all_collected = False
    server.collected_secrets = {}  # Initialize collected secrets storage
    server.timeout = 1  # Check for completion every second
    
    # Create a custom handler with our parameters
    handler = lambda *args, **kwargs: MultiSecretCollectorHandler(
        *args, 
        server_name=server_name,
        secrets=secrets,
        env_file=env_file,
        server_instance=server,
        **kwargs
    )
    
    # Set the handler after creating the server
    server.RequestHandlerClass = handler
    
    # Open browser after a short delay
    def open_browser():
        time.sleep(0.5)
        webbrowser.open(f'http://localhost:{port}')
    
    browser_thread = threading.Thread(target=open_browser)
    browser_thread.daemon = True
    browser_thread.start()
    
    print(f"🌐 Opening browser to collect {len(secrets)} secrets...")
    print(f"   URL: http://localhost:{port}")
    print(f"   If browser doesn't open, please visit the URL manually.")
    print()
    
    # Run server until all secrets are collected or timeout
    start_time = time.time()
    timeout = 600  # 10 minutes for multiple secrets
    
    while not server.all_collected and (time.time() - start_time) < timeout:
        server.handle_request()
    
    server.server_close()
    
    if server.all_collected:
        print("✅ All secrets collected successfully!")
        return True
    else:
        print("❌ Secret collection timed out or was cancelled.")
        return False

def main():
    if len(sys.argv) < 2:
        print("Usage: multi-secret-collector <server_name> [<secret_name:description>...]")
        print("Example: multi-secret-collector github GITHUB_TOKEN:'GitHub Personal Access Token' GITHUB_ORG:'GitHub Organization'")
        sys.exit(1)
    
    server_name = sys.argv[1]
    
    # Parse secrets from remaining arguments
    secrets = []
    for arg in sys.argv[2:]:
        if ':' in arg:
            name, description = arg.split(':', 1)
            secrets.append({'name': name, 'description': description})
        else:
            print(f"Warning: Invalid secret format '{arg}', expected 'NAME:Description'")
    
    if not secrets:
        print("Error: No secrets specified")
        sys.exit(1)
    
    # Use central .env file
    mcp_base_dir = Path.home() / "mcp-servers"
    env_file = mcp_base_dir / ".env"
    
    success = run_multi_server(server_name, secrets, env_file)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()