"""Lightweight HTTP server for controlling the fireplace remotely.

Uses Python's stdlib http.server - no additional dependencies required.
"""

import json
import logging
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any

from fireplace.controller import Fireplace

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

# Global fireplace instance
fireplace = Fireplace()


class FireplaceHandler(BaseHTTPRequestHandler):
    """HTTP request handler for fireplace control."""

    def _send_json_response(self, status_code: int, data: dict[str, Any]):
        """Send a JSON response."""
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def _read_json_body(self) -> dict[str, Any]:
        """Read and parse JSON request body."""
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length == 0:
            return {}
        body = self.rfile.read(content_length)
        return json.loads(body.decode())

    def do_GET(self):
        """Handle GET requests."""
        if self.path == "/status":
            self._send_json_response(
                200,
                {
                    "running": fireplace.is_running,
                    "remaining_seconds": fireplace.remaining_seconds,
                    "volume": fireplace.volume,
                },
            )
        elif self.path == "/health":
            self._send_json_response(200, {"status": "ok"})
        else:
            self._send_json_response(404, {"error": "Not found"})

    def do_POST(self):
        """Handle POST requests."""
        if self.path == "/start":
            self._handle_start()
        elif self.path == "/stop":
            self._handle_stop()
        elif self.path == "/volume":
            self._handle_volume()
        else:
            self._send_json_response(404, {"error": "Not found"})

    def _handle_start(self):
        """Handle POST /start request."""
        try:
            body = self._read_json_body()
            duration_minutes = body.get("duration_minutes", 30)
            fade_out_minutes = body.get("fade_out_minutes", 10)

            # Validate duration
            if not isinstance(duration_minutes, (int, float)) or duration_minutes <= 0:
                self._send_json_response(
                    400, {"error": "duration_minutes must be a positive number"}
                )
                return
            if duration_minutes > 480:
                self._send_json_response(
                    400, {"error": "duration_minutes must be <= 480 (8 hours)"}
                )
                return

            # Validate fade_out
            if not isinstance(fade_out_minutes, (int, float)) or fade_out_minutes < 0:
                self._send_json_response(
                    400, {"error": "fade_out_minutes must be a non-negative number"}
                )
                return

            was_running = fireplace.is_running
            fireplace.start(
                duration_minutes=duration_minutes,
                fade_out_minutes=fade_out_minutes,
            )

            action = "updated" if was_running else "started"
            self._send_json_response(
                200,
                {
                    "message": f"Fireplace {action} for {duration_minutes} minutes",
                    "fade_out_minutes": fade_out_minutes,
                },
            )

        except json.JSONDecodeError:
            self._send_json_response(400, {"error": "Invalid JSON"})

    def _handle_stop(self):
        """Handle POST /stop request."""
        success = fireplace.stop()
        if not success:
            self._send_json_response(409, {"error": "Fireplace is not running"})
            return
        self._send_json_response(200, {"message": "Fireplace stopped"})

    def _handle_volume(self):
        """Handle POST /volume request."""
        try:
            body = self._read_json_body()
            volume = body.get("volume")

            if volume is None:
                self._send_json_response(400, {"error": "volume is required"})
                return
            if not isinstance(volume, (int, float)):
                self._send_json_response(400, {"error": "volume must be a number"})
                return
            if volume < 0 or volume > 100:
                self._send_json_response(
                    400, {"error": "volume must be between 0 and 100"}
                )
                return

            success = fireplace.set_volume(int(volume))
            if not success:
                self._send_json_response(409, {"error": "Fireplace is not running"})
                return

            self._send_json_response(
                200, {"message": f"Volume set to {int(volume)}%", "volume": int(volume)}
            )

        except json.JSONDecodeError:
            self._send_json_response(400, {"error": "Invalid JSON"})

    def log_message(self, format: str, *args):
        """Override to use our logger."""
        logger.info("%s - %s", self.address_string(), format % args)


def run_server(host: str = "0.0.0.0", port: int = 8000):
    """Run the HTTP server."""
    server_address = (host, port)
    httpd = HTTPServer(server_address, FireplaceHandler)
    logger.info(f"Fireplace API server running on http://{host}:{port}")
    logger.info(
        "Endpoints: POST /start, POST /stop, POST /volume, GET /status, GET /health"
    )
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down server...")
        if fireplace.is_running:
            fireplace.stop()
        httpd.shutdown()


if __name__ == "__main__":
    run_server()
