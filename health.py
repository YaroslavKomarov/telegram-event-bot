"""
Простой health check для мониторинга Railway
"""
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import json
import logging

logger = logging.getLogger(__name__)

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            response = {
                'status': 'healthy',
                'service': 'telegram-bot',
                'version': '1.0.0'
            }
            
            self.wfile.write(json.dumps(response).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        # Отключаем стандартные логи HTTP сервера
        pass

def start_health_server(port=8080):
    """Запуск health check сервера в отдельном потоке"""
    def run_server():
        try:
            server = HTTPServer(('0.0.0.0', port), HealthHandler)
            logger.info(f"✅ Health check server started on port {port}")
            server.serve_forever()
        except Exception as e:
            logger.error(f"❌ Error starting health server: {e}")
    
    thread = threading.Thread(target=run_server, daemon=True)
    thread.start()
    return thread 