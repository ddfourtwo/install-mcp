#!/usr/bin/env python3
"""
Web-based Secret Collector for MCP servers
Opens a local web server to collect secrets securely
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

class SecretCollectorHandler(BaseHTTPRequestHandler):
    def __init__(self, *args, server_name=None, secret_name=None, 
                 secret_description=None, env_file=None, **kwargs):
        self.server_name = server_name
        self.secret_name = secret_name
        self.secret_description = secret_description
        self.env_file = env_file
        self.secret_collected = False
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>MCP Secret Collection</title>
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
        input[type="password"], input[type="text"] {{
            width: 100%;
            padding: 12px;
            font-size: 16px;
            border: 2px solid #ddd;
            border-radius: 5px;
            margin-bottom: 20px;
            box-sizing: border-box;
        }}
        input[type="password"]:focus, input[type="text"]:focus {{
            outline: none;
            border-color: #0084ff;
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
        .error {{
            color: #d32f2f;
            margin-top: 10px;
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
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Secure Secret Collection</h1>
        <div class="server-name">for {self.server_name}</div>
        
        <div class="description">
            <strong>Required:</strong> {self.secret_description}<br>
            <strong>Variable:</strong> {self.secret_name}
        </div>
        
        <div class="warning">
            This page is served locally on your machine. Your secret will be saved to:<br>
            <code>{self.env_file}</code>
        </div>
        
        <form method="POST" action="/save">
            <input type="password" id="secret" name="secret" 
                   placeholder="Enter your {self.secret_description}" 
                   required autofocus>
            
            <div class="show-hide">
                <input type="checkbox" id="showSecret" onchange="toggleSecret()">
                <label for="showSecret">Show secret</label>
            </div>
            
            <button type="submit">Save Secret</button>
        </form>
        
        <div id="error" class="error"></div>
    </div>
    
    <script>
        function toggleSecret() {{
            const input = document.getElementById('secret');
            const checkbox = document.getElementById('showSecret');
            input.type = checkbox.checked ? 'text' : 'password';
        }}
        
        // Auto-close after 5 minutes
        setTimeout(() => {{
            document.body.innerHTML = '<div class="container"><h1>Session Expired</h1><p>Please run the command again.</p></div>';
        }}, 300000);
    </script>
</body>
</html>
"""
            self.wfile.write(html.encode())
        
        elif self.path == '/success':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            html = """
<!DOCTYPE html>
<html>
<head>
    <title>Success - MCP Secret Collection</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 500px;
            margin: 50px auto;
            padding: 20px;
            background: #f5f5f5;
        }
        .container {
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            text-align: center;
        }
        .success {
            color: #4caf50;
            font-size: 48px;
            margin-bottom: 20px;
        }
        h1 {
            color: #333;
            margin-bottom: 20px;
        }
        p {
            color: #666;
            margin-bottom: 20px;
        }
        .close {
            color: #999;
            font-size: 14px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Secret Saved Successfully!</h1>
        <p>Your secret has been securely saved to the .env file.</p>
        <p>You can now close this window and return to your terminal.</p>
        <p class="close">This window will close automatically in 3 seconds...</p>
    </div>
    <script>
        setTimeout(() => {
            window.close();
        }, 3000);
    </script>
</body>
</html>
"""
            self.wfile.write(html.encode())
            # Signal that collection is complete
            self.server.secret_collected = True
    
    def do_POST(self):
        if self.path == '/save':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode('utf-8')
            params = parse_qs(post_data)
            
            secret_value = params.get('secret', [''])[0]
            
            if secret_value:
                try:
                    # Save to .env file
                    env_file = Path(self.env_file)
                    env_file.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Read existing content
                    lines = []
                    if env_file.exists():
                        with open(env_file, 'r') as f:
                            lines = f.readlines()
                    
                    # Update or append the secret
                    found = False
                    for i, line in enumerate(lines):
                        if line.strip().startswith(f"{self.secret_name}="):
                            lines[i] = f"{self.secret_name}={secret_value}\n"
                            found = True
                            break
                    
                    if not found:
                        lines.append(f"{self.secret_name}={secret_value}\n")
                    
                    # Write back
                    with open(env_file, 'w') as f:
                        f.writelines(lines)
                    
                    # Set restrictive permissions
                    os.chmod(env_file, 0o600)
                    
                    # Redirect to success page
                    self.send_response(302)
                    self.send_header('Location', '/success')
                    self.end_headers()
                    
                except Exception as e:
                    self.send_response(500)
                    self.send_header('Content-type', 'text/plain')
                    self.end_headers()
                    self.wfile.write(f"Error: {str(e)}".encode())
            else:
                self.send_response(400)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                self.wfile.write(b"No secret provided")
    
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

def run_server(server_name, secret_name, secret_description, env_file):
    """Run the web server and open browser"""
    port = find_free_port()
    
    # Create a custom handler with our parameters
    handler = lambda *args, **kwargs: SecretCollectorHandler(
        *args, 
        server_name=server_name,
        secret_name=secret_name,
        secret_description=secret_description,
        env_file=env_file,
        **kwargs
    )
    
    server = HTTPServer(('localhost', port), handler)
    server.secret_collected = False
    server.timeout = 1  # Check for completion every second
    
    # Open browser after a short delay
    def open_browser():
        time.sleep(0.5)
        webbrowser.open(f'http://localhost:{port}')
    
    browser_thread = threading.Thread(target=open_browser)
    browser_thread.daemon = True
    browser_thread.start()
    
    print(f"🌐 Opening browser to collect secret...")
    print(f"   URL: http://localhost:{port}")
    print(f"   If browser doesn't open, please visit the URL manually.")
    print()
    
    # Run server until secret is collected or timeout
    start_time = time.time()
    timeout = 300  # 5 minutes
    
    while not server.secret_collected and (time.time() - start_time) < timeout:
        server.handle_request()
    
    server.server_close()
    
    if server.secret_collected:
        print("✅ Secret collected successfully!")
        return True
    else:
        print("❌ Secret collection timed out or was cancelled.")
        return False

def main():
    if len(sys.argv) != 4:
        print("Usage: web-secret-collector <server_name> <secret_name> <secret_description>")
        sys.exit(1)
    
    server_name = sys.argv[1]
    secret_name = sys.argv[2]
    secret_description = sys.argv[3]
    
    # Use central .env file
    mcp_base_dir = Path.home() / "mcp-servers"
    env_file = mcp_base_dir / ".env"
    
    success = run_server(server_name, secret_name, secret_description, env_file)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()