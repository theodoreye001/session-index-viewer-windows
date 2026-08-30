import json
import threading
import unittest
from http.server import ThreadingHTTPServer
from urllib.request import urlopen

from siv.http_app import Handler
from siv.version import __version__, read_version


class VersionTests(unittest.TestCase):
    def test_runtime_version_matches_version_file(self):
        self.assertEqual(__version__, read_version())
        self.assertRegex(__version__, r"^\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?$")

    def test_version_endpoint(self):
        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            host, port = server.server_address
            with urlopen(f"http://{host}:{port}/api/version") as response:
                self.assertEqual(response.status, 200)
                payload = json.loads(response.read().decode("utf-8"))
                self.assertEqual(payload, {"version": __version__})
                self.assertEqual(response.headers.get("Cache-Control"), "no-store")
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)


if __name__ == "__main__":
    unittest.main()
