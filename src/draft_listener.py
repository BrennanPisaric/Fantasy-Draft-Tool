import os
import json
from http.server import BaseHTTPRequestHandler, HTTPServer

FILE_PATH = os.path.join(os.path.dirname(__file__), 'drafted_players.txt')

class DraftListenerHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200, "ok")
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode('utf-8')
        
        try:
            data = json.loads(post_data)
            text = data.get('text', '')
            if text:
                with open(FILE_PATH, 'a', encoding='utf-8') as f:
                    f.write(text + '\n')
                print(f"Scraped from browser: {text}")
                
            self.send_response(200)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'status': 'success'}).encode('utf-8'))
        except Exception as e:
            self.send_response(400)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))

    def log_message(self, format, *args):
        # Suppress standard HTTP logging to keep console clean
        pass

def run(server_class=HTTPServer, handler_class=DraftListenerHandler, port=8000):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f"✅ Draft Listener running on http://localhost:{port}")
    print("Waiting for data from your browser...")
    
    # Clear the file on startup so it's fresh for a new draft
    with open(FILE_PATH, 'w', encoding='utf-8') as f:
        f.write("")
        
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    print("Listener stopped.")

if __name__ == '__main__':
    run()
