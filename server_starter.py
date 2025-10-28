import http.server
import socketserver
import webbrowser
import os
import sys
import threading
import time

# --- Configuration ---
PORT = 8000
DIRECTORY = os.getcwd()
FILENAME = "index.html"
URL = f"http://localhost:{PORT}/{FILENAME}"

def create_index_html(filepath):
    """Creates a basic index.html file."""
    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Local Server Test - Python</title>
    <style>
        body {{ font-family: sans-serif; text-align: center; padding: 50px; background-color: #f4f4f9; }}
        h1 {{ color: #333; }}
        p {{ color: #555; }}
        .note {{ margin-top: 20px; color: #a00; font-weight: bold; }}
    </style>
</head>
<body>
    <h1>Local Server is Running Successfully!</h1>
    <p>This file was automatically generated and served by a Python script.</p>
    <div class="note">Close this terminal window (Ctrl+C) to stop the server.</div>
</body>
</html>
"""
    try:
        with open(filepath, "w") as f:
            f.write(html_content)
        print(f"[{time.strftime('%H:%M:%S')}] Successfully created: {filepath}")
    except IOError as e:
        print(f"Error creating HTML file: {e}")
        sys.exit(1)

def start_server():
    """Starts the simple HTTP server."""
    # Set the handler to serve files from the current directory
    Handler = http.server.SimpleHTTPRequestHandler
    
    # Use socketserver for easier threading setup
    try:
        with socketserver.TCPServer(("", PORT), Handler) as httpd:
            print(f"[{time.strftime('%H:%M:%S')}] Serving directory: {DIRECTORY}")
            print(f"[{time.strftime('%H:%M:%S')}] Server started at: {URL}")
            
            # Start the browser *after* the server is confirmed running
            webbrowser.open(URL)
            
            # Keep the server running until manually stopped
            httpd.serve_forever()
            
    except OSError as e:
        if "Address already in use" in str(e):
            print(f"[{time.strftime('%H:%M:%S')}] Error: Port {PORT} is already in use.")
            print("Try changing the PORT variable in the script.")
        else:
            print(f"[{time.strftime('%H:%M:%S')}] An unexpected server error occurred: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print(f"\n[{time.strftime('%H:%M:%S')}] Server stopped by user.")
        sys.exit(0)


if __name__ == "__main__":
    filepath = os.path.join(DIRECTORY, FILENAME)
    
    # 1. Create index.html
    create_index_html(filepath)
    
    # 2. Start the server
    start_server()