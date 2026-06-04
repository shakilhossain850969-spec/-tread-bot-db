import http.server
import socketserver
import json

PORT = 8000

class MockHandler(http.server.SimpleHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200, "ok")
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header("Access-Control-Allow-Headers", "X-Requested-With, Content-type, Authorization")
        self.end_headers()

    def do_GET(self):
        self._send_mock_response()

    def do_POST(self):
        self._send_mock_response()

    def _send_mock_response(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        # Determine basic mock response based on path
        response_data = {"status": "success", "message": "Mock data"}
        if "market" in self.path:
            response_data = {"data": []}
        elif "signals" in self.path:
            response_data = {"signals": []}
        elif "auth" in self.path:
            response_data = {"access_token": "mock_jwt_token_123", "token_type": "bearer"}
        
        self.wfile.write(json.dumps(response_data).encode())

with socketserver.TCPServer(("", PORT), MockHandler) as httpd:
    print(f"Mock server running on port {PORT}")
    httpd.serve_forever()
