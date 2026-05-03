#!/usr/bin/env python3
"""
J.A.R.V.I.S — Serveur HTTP avec accès par token secret dans l'URL
Accès : http://frvill.duckdns.org:8080/?t=MONSECRET

- Repo GitHub peut rester public (le secret n'est jamais dans le code)
- Token dans l'URL → cookie de session signé (HMAC-SHA256)
- Sans token ET sans cookie valide → 403 silencieux
"""

import hashlib
import hmac
import os
import secrets
import time
from http.server import SimpleHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

# ── Configuration ──────────────────────────────────────────────────────────
PORT         = 8080
SECRET_TOKEN = "MONSECRET"           # ← changer ici (URL d'accès)
SESSION_KEY  = secrets.token_hex(32) # Clé de signature des cookies (générée au démarrage)
SESSION_TTL  = 60 * 60 * 24 * 7     # Durée session : 7 jours (en secondes)

SERVE_DIR = os.path.dirname(os.path.abspath(__file__))
# ──────────────────────────────────────────────────────────────────────────


def make_session_cookie() -> str:
    """Génère un cookie signé HMAC avec timestamp."""
    ts = str(int(time.time()))
    sig = hmac.new(SESSION_KEY.encode(), ts.encode(), hashlib.sha256).hexdigest()
    return f"{ts}.{sig}"


def verify_session_cookie(cookie_value: str) -> bool:
    """Vérifie la signature et l'expiration du cookie."""
    try:
        ts_str, sig = cookie_value.split(".", 1)
        ts = int(ts_str)
        expected = hmac.new(SESSION_KEY.encode(), ts_str.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expected):
            return False
        if time.time() - ts > SESSION_TTL:
            return False
        return True
    except Exception:
        return False


def get_cookie(headers, name: str):
    """Extrait un cookie par nom depuis les headers."""
    raw = headers.get("Cookie", "")
    for part in raw.split(";"):
        k, _, v = part.strip().partition("=")
        if k.strip() == name:
            return v.strip()
    return None


class SecretHandler(SimpleHTTPRequestHandler):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=SERVE_DIR, **kwargs)

    def do_GET(self):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)

        # 1. Token valide dans l'URL → poser le cookie et rediriger proprement
        if params.get("t", [None])[0] == SECRET_TOKEN:
            cookie = make_session_cookie()
            self.send_response(302)
            self.send_header("Location", parsed.path or "/")
            self.send_header(
                "Set-Cookie",
                f"jarvis_session={cookie}; Path=/; HttpOnly; SameSite=Strict; Max-Age={SESSION_TTL}"
            )
            self.end_headers()
            return

        # 2. Cookie de session valide → servir normalement
        session = get_cookie(self.headers, "jarvis_session")
        if session and verify_session_cookie(session):
            super().do_GET()
            return

        # 3. Aucune autorisation → 403 silencieux (pas d'indice)
        self._deny()

    def do_HEAD(self):
        session = get_cookie(self.headers, "jarvis_session")
        if session and verify_session_cookie(session):
            super().do_HEAD()
        else:
            self._deny()

    def _deny(self):
        self.send_response(403)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(b"""<!DOCTYPE html>
<html><head><title>403</title></head>
<body style="background:#050508;color:#4ca8e8;font-family:sans-serif;
display:flex;align-items:center;justify-content:center;height:100vh;margin:0">
<div style="text-align:center;opacity:0.3">
  <div style="font-size:48px;letter-spacing:8px">J.A.R.V.I.S</div>
</div></body></html>""")

    def log_message(self, fmt, *args):
        print(f"[HTTP] {self.address_string()} — {fmt % args}")


if __name__ == "__main__":
    os.chdir(SERVE_DIR)
    server = HTTPServer(("0.0.0.0", PORT), SecretHandler)
    print(f"[JARVIS] Serveur démarré")
    print(f"[JARVIS] Lien d'accès : http://frvill.duckdns.org:{PORT}/?t={SECRET_TOKEN}")
    print(f"[JARVIS] Dossier servi : {SERVE_DIR}")
    print("Ctrl+C pour arrêter.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[JARVIS] Arrêté.")
