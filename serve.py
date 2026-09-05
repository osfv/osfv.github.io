"""Local preview. Maps /now -> now.html, matching GitHub Pages."""
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent


class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        raw = self.path.split("?", 1)[0].split("#", 1)[0]
        if raw != "/" and not raw.endswith("/"):
            name = raw.lstrip("/")
            if "." not in Path(name).name:
                html = ROOT / f"{name}.html"
                if html.exists():
                    self.path = f"/{name}.html" + self.path[len(raw):]
        return super().do_GET()

    def send_error(self, code, message=None, explain=None):
        page = ROOT / "404.html"
        if code == 404 and page.is_file():
            body = page.read_bytes()
            self.send_response(404, message)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            if self.command != "HEAD":
                self.wfile.write(body)
            return
        return super().send_error(code, message, explain)


if __name__ == "__main__":
    ThreadingHTTPServer(("127.0.0.1", 8765), Handler).serve_forever()
