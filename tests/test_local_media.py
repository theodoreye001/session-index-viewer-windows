import os
import tempfile
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import urlopen
from unittest.mock import patch

from siv.http_app import Handler
from siv.local_media import (
    LocalMediaError,
    resolve_codex_visualization,
    rewrite_codex_visualization_urls,
)
from http.server import ThreadingHTTPServer


class RewriteVisualizationTests(unittest.TestCase):
    def test_rewrites_windows_codex_visualization(self):
        text = (
            "![plot](file:///C:/Users/64658/.codex/visualizations/"
            "run%201/pressure.png)"
        )
        self.assertEqual(
            rewrite_codex_visualization_urls(text),
            "![plot](/api/codex-visualization?path=run%201/pressure.png)",
        )

    def test_rewrites_raw_html_image_url(self):
        text = (
            '<img src="file:///C:/Users/64658/.codex/visualizations/a/b.webp">'
        )
        self.assertEqual(
            rewrite_codex_visualization_urls(text),
            '<img src="/api/codex-visualization?path=a/b.webp">',
        )

    def test_leaves_other_file_urls_unchanged(self):
        text = "[file](file:///C:/Users/64658/Documents/report.pdf)"
        self.assertEqual(rewrite_codex_visualization_urls(text), text)


class ResolveVisualizationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = os.path.realpath(self.tmp.name)
        os.makedirs(os.path.join(self.root, "nested"), exist_ok=True)
        self.image = os.path.join(self.root, "nested", "plot.png")
        with open(self.image, "wb") as f:
            f.write(b"png-data")
        self.root_patch = patch(
            "siv.local_media.CODEX_VISUALIZATIONS_ROOT", self.root
        )
        self.root_patch.start()

    def tearDown(self):
        self.root_patch.stop()
        self.tmp.cleanup()

    def test_resolves_png_below_allowed_root(self):
        path, content_type = resolve_codex_visualization("nested/plot.png")
        self.assertEqual(path, self.image)
        self.assertEqual(content_type, "image/png")

    def test_accepts_backslash_relative_path(self):
        path, content_type = resolve_codex_visualization(r"nested\plot.png")
        self.assertEqual(path, self.image)
        self.assertEqual(content_type, "image/png")

    def test_rejects_parent_traversal(self):
        with self.assertRaises(LocalMediaError):
            resolve_codex_visualization("../secret.png")

    def test_rejects_absolute_windows_path(self):
        with self.assertRaises(LocalMediaError):
            resolve_codex_visualization(r"C:\Users\64658\secret.png")

    def test_rejects_svg(self):
        svg = os.path.join(self.root, "diagram.svg")
        with open(svg, "wb") as f:
            f.write(b"<svg></svg>")
        with self.assertRaises(LocalMediaError):
            resolve_codex_visualization("diagram.svg")

    def test_rejects_oversized_image(self):
        with patch("siv.local_media.MAX_LOCAL_IMAGE_BYTES", 3):
            with self.assertRaises(LocalMediaError):
                resolve_codex_visualization("nested/plot.png")

    def test_missing_image_raises_file_not_found(self):
        with self.assertRaises(FileNotFoundError):
            resolve_codex_visualization("missing.png")

    def test_http_endpoint_serves_image_with_security_headers(self):
        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            host, port = server.server_address
            with urlopen(
                f"http://{host}:{port}/api/codex-visualization?path=nested/plot.png"
            ) as response:
                self.assertEqual(response.status, 200)
                self.assertEqual(response.headers.get_content_type(), "image/png")
                self.assertEqual(
                    response.headers.get("X-Content-Type-Options"), "nosniff"
                )
                self.assertEqual(
                    response.headers.get("Cross-Origin-Resource-Policy"),
                    "same-origin",
                )
                self.assertEqual(response.read(), b"png-data")
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

    def test_http_endpoint_rejects_traversal(self):
        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            host, port = server.server_address
            with self.assertRaises(HTTPError) as ctx:
                urlopen(
                    f"http://{host}:{port}/api/codex-visualization?path=../secret.png"
                )
            self.assertEqual(ctx.exception.code, 404)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)


if __name__ == "__main__":
    unittest.main()
