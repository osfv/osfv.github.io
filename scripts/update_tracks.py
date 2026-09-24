"""Pull top tracks from Spotify and rewrite the "on repeat" list in now.html.

Needs SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET and SPOTIFY_REFRESH_TOKEN in the environment.
"""
import base64
import html
import json
import os
import re
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAGE = ROOT / "now.html"
COVERS = ROOT / "assets" / "albums"
LIMIT = 3
# short_term is roughly the last 4 weeks; medium_term ~6 months; long_term ~1 year
TIME_RANGE = "short_term"
START, END = "<!-- tracks:start -->", "<!-- tracks:end -->"


def fetch(url, data=None, headers=None):
    req = urllib.request.Request(url, data=data, headers=headers or {})
    with urllib.request.urlopen(req, timeout=20) as res:
        return res.read()


def access_token():
    auth = base64.b64encode(
        f"{os.environ['SPOTIFY_CLIENT_ID']}:{os.environ['SPOTIFY_CLIENT_SECRET']}".encode()
    ).decode()
    body = urllib.parse.urlencode({
        "grant_type": "refresh_token",
        "refresh_token": os.environ["SPOTIFY_REFRESH_TOKEN"],
    }).encode()
    res = fetch("https://accounts.spotify.com/api/token", body, {
        "Authorization": "Basic " + auth,
        "Content-Type": "application/x-www-form-urlencoded",
    })
    return json.loads(res)["access_token"]


def top_tracks(token):
    query = urllib.parse.urlencode({"time_range": TIME_RANGE, "limit": LIMIT})
    res = fetch(
        "https://api.spotify.com/v1/me/top/tracks?" + query,
        headers={"Authorization": "Bearer " + token},
    )
    return json.loads(res)["items"]


def save_cover(track):
    images = sorted(track["album"]["images"], key=lambda i: i.get("width") or 0)
    image = next((i for i in images if (i.get("width") or 0) >= 66), images[-1])
    name = track["id"] + ".jpg"
    path = COVERS / name
    if not path.exists():
        path.write_bytes(fetch(image["url"]))
    return name


def clean_title(name, artists):
    """Drop "(with X)" / "(feat. X)" when X is already on the artist line."""
    guests = [a.lower() for a in artists[1:]]

    def drop(m):
        return "" if any(g in m.group(0).lower() for g in guests) else m.group(0)

    return re.sub(r"\s*[(\[](?:with|feat\.?|ft\.?)\s[^)\]]*[)\]]", drop, name, flags=re.I).strip()


def row(track, cover):
    names = [a["name"] for a in track["artists"]]
    title = html.escape(clean_title(track["name"], names))
    artist = html.escape(", ".join(names))
    link = html.escape(track["external_urls"]["spotify"])
    minutes, seconds = divmod(round(track["duration_ms"] / 1000), 60)
    return (
        f'      <li data-time="{minutes}:{seconds:02}">\n'
        f'        <img src="/assets/albums/{cover}" alt="" width="66" height="66" />\n'
        f'        <a class="song" href="{link}" target="_blank" rel="noopener">{title}</a>\n'
        f'        <span class="artist">{artist}</span>\n'
        f'      </li>'
    )


def main():
    tracks = top_tracks(access_token())
    if not tracks:
        raise SystemExit("spotify returned no top tracks, leaving the page alone")

    COVERS.mkdir(parents=True, exist_ok=True)
    covers = [save_cover(t) for t in tracks]
    rows = "\n".join(row(t, c) for t, c in zip(tracks, covers))

    page = PAGE.read_text(encoding="utf-8")
    block = re.compile(re.escape(START) + ".*?" + re.escape(END), re.S)
    if not block.search(page):
        raise SystemExit(f"couldn't find {START} / {END} in now.html")
    PAGE.write_text(
        block.sub(lambda _: f"{START}\n{rows}\n      {END}", page, count=1),
        encoding="utf-8",
    )

    for old in COVERS.glob("*.jpg"):
        if old.name not in covers:
            old.unlink()

    for t in tracks:
        print(f"{t['name']} - {', '.join(a['name'] for a in t['artists'])}")


if __name__ == "__main__":
    main()
