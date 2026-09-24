"""One-time helper: log in to Spotify and print a refresh token for update_tracks.py.

Add http://127.0.0.1:8888/callback as a Redirect URI in your Spotify app settings first.
"""
import base64
import json
import secrets
import urllib.parse
import urllib.request
import webbrowser
from getpass import getpass
from http.server import BaseHTTPRequestHandler, HTTPServer

REDIRECT = "http://127.0.0.1:8888/callback"
SCOPE = "user-top-read"


def main():
    client_id = input("client id: ").strip()
    client_secret = getpass("client secret (hidden while typing): ").strip()
    state = secrets.token_urlsafe(16)
    result = {}

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            url = urllib.parse.urlparse(self.path)
            if url.path != "/callback":
                self.send_error(404)
                return
            result.update({k: v[0] for k, v in urllib.parse.parse_qs(url.query).items()})
            body = b"done, you can close this tab."
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            pass

    server = HTTPServer(("127.0.0.1", 8888), Handler)
    login = "https://accounts.spotify.com/authorize?" + urllib.parse.urlencode({
        "client_id": client_id,
        "response_type": "code",
        "redirect_uri": REDIRECT,
        "scope": SCOPE,
        "state": state,
    })
    print("opening Spotify login. if nothing opens, visit:\n" + login)
    webbrowser.open(login)

    while "code" not in result and "error" not in result:
        server.handle_request()
    server.server_close()

    if "error" in result:
        raise SystemExit("spotify said: " + result["error"])
    if result.get("state") != state:
        raise SystemExit("state mismatch, try again")

    auth = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    req = urllib.request.Request(
        "https://accounts.spotify.com/api/token",
        data=urllib.parse.urlencode({
            "grant_type": "authorization_code",
            "code": result["code"],
            "redirect_uri": REDIRECT,
        }).encode(),
        headers={
            "Authorization": "Basic " + auth,
            "Content-Type": "application/x-www-form-urlencoded",
        },
    )
    with urllib.request.urlopen(req, timeout=20) as res:
        token = json.load(res)

    print("\nrefresh token (save as SPOTIFY_REFRESH_TOKEN, don't share it):\n")
    print(token["refresh_token"])


if __name__ == "__main__":
    main()
