# Copyright (c) 2019-2026 Five Squared Interactive
# SPDX-License-Identifier: MIT

#
#
# Signing in from Blender: a loopback code
# flow (RFC 8252 + RFC 7636), with nothing of Blender in it so every rule is
# checked on plain Python (tools/sign_in_flow_check.py).
#
# The shape. This process mints a PKCE verifier and its S256 challenge and a
# path nonce, listens on 127.0.0.1:<free port>/<nonce>, and sends the browser
# to the configured sign-in page carrying the challenge and that loopback
# address. The page forwards the challenge to the identity provider; the
# provider redirects the browser back to the loopback with a single-use
# code; this process redeems the code — outbound, with the verifier — at the
# configured token endpoint. A code is worthless to anyone without the
# verifier, and the verifier never leaves this process. That is why a code,
# and never a token, crosses the loopback.
#
# This add-on names no identity service and hardcodes no host. The sign-in
# page, the token endpoint and the API key are preferences (a packaged build
# may carry defaults, a source checkout carries none), so the same button
# works against any provider that speaks this exact grant — a code redeemed by
# POST <token endpoint>?grant_type=pkce with {auth_code, code_verifier} and an
# `apikey` header, which is one provider family's shape, not generic OIDC —
# or against none, which is what keeps a world from needing anyone's
# permission to exist.

import base64
import hashlib
import json
import secrets
import threading
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer
from queue import Empty, Queue
from urllib.parse import parse_qs, urlencode, urlsplit, urlunsplit

#: RFC 7636 §4.1 — the unreserved characters a verifier is made of.
_VERIFIER_ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~"

#: The one method a challenge is made with. The provider is told the same.
CHALLENGE_METHOD = "s256"

#: The listener's answer to a browser that brought the code. Plain words,
#: no service names — this file is in the open add-on.
CALLBACK_PAGE = (
    "<!doctype html><meta charset=\"utf-8\"><title>Signed in</title>"
    "<body style=\"font-family:sans-serif;padding:2em\">"
    "<h1>Signed in</h1><p>You can close this tab and go back to Blender.</p></body>"
)


class SignInError(Exception):
    """A sign-in that could not finish, with the sentence a person reads."""


def _b64url(raw):
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def make_pkce():
    """Return (verifier, challenge): 64 unreserved characters and its S256 challenge."""
    verifier = "".join(secrets.choice(_VERIFIER_ALPHABET) for _ in range(64))
    challenge = _b64url(hashlib.sha256(verifier.encode("ascii")).digest())
    return verifier, challenge


def make_nonce():
    """The path segment only this process knows; the listener answers nothing else."""
    return secrets.token_urlsafe(24)


def loopback_redirect(port, nonce):
    """The address the browser is sent back to. 127.0.0.1, never `localhost` (RFC 8252 §8.3)."""
    return "http://127.0.0.1:%d/%s" % (port, nonce)


def build_sign_in_url(sign_in_url, challenge, redirect_to):
    """The configured sign-in page, carrying the challenge and the loopback. An existing query is kept."""
    parts = urlsplit(sign_in_url.strip())
    query = parse_qs(parts.query, keep_blank_values=True)
    query["code_challenge"] = [challenge]
    query["code_challenge_method"] = [CHALLENGE_METHOD]
    query["redirect_to"] = [redirect_to]
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query, doseq=True), parts.fragment))


def parse_callback(path, nonce):
    """The code from a callback request path, or None: exactly /<nonce>?code=<something>, nothing else."""
    parts = urlsplit(path)
    if parts.path != "/" + nonce:
        return None
    codes = parse_qs(parts.query).get("code")
    if not codes or not codes[0]:
        return None
    return codes[0]


def validate_sign_in_flow(sign_in_url, token_endpoint, api_key, env_token):
    """Return an error string, or None when the flow may start.

    Three addresses have to be there before a browser is opened, and the
    third refusal is the reason this exists at all: signing in writes the
    preference, and an environment token beats the preference, so a sign-in
    that would change nothing is refused before it wastes the person's time.
    """
    url = (sign_in_url or "").strip()
    if not url:
        return (
            "No sign-in address. Put your identity provider's sign-in page in the "
            "add-on preferences - this add-on does not assume one."
        )
    if not url.lower().startswith(("http://", "https://")):
        return "The sign-in address must start with http:// or https:// - it is a web page your browser opens."
    endpoint = (token_endpoint or "").strip()
    if not endpoint:
        return "No token endpoint. Put your identity provider's token endpoint in the add-on preferences."
    if not endpoint.lower().startswith(("http://", "https://")):
        return "The token endpoint must start with http:// or https://."
    if not (api_key or "").strip():
        return "No API key. Put your identity provider's publishable API key in the add-on preferences."
    if (env_token or "").strip():
        return (
            "A publish token is set in the environment, and it beats the preference "
            "signing in would write - unset it first, or signing in changes nothing."
        )
    return None


def _post_json(url, headers, body):
    """The one outbound request. Returns (status, bytes); an HTTP error is a status, not an exception."""
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as res:
            return res.status, res.read()
    except urllib.error.HTTPError as err:
        return err.code, err.read()


class SignInUnreachable(SignInError):
    """The token endpoint could not be reached at all (DNS, refused, timeout).

    Distinct from a refusal on purpose: a refusal means the
    session is over and both tokens go; unreachable means nothing is known,
    so both tokens stay and the caller tries again later.
    """


#: Renew this many seconds before the access token's end, so a publish never
#: starts with a token that dies mid-upload.
REFRESH_MARGIN_S = 300


def _token_grant(token_endpoint, api_key, grant, body_fields, what, post, now):
    """One POST to <endpoint>?grant_type=<grant>; returns (access, refresh, expires_at).

    expires_at is seconds since the epoch, or None when the reply did not
    say. The tokens are opaque here: stored and sent, never cracked.
    """
    url = token_endpoint.strip().rstrip("/") + "?grant_type=" + grant
    headers = {"apikey": api_key.strip(), "Content-Type": "application/json", "Accept": "application/json"}
    body = json.dumps(body_fields).encode("utf-8")
    try:
        status, raw = post(url, headers, body)
    except Exception as err:  # network down, DNS, refused
        raise SignInUnreachable("Could not reach the token endpoint: %s" % err)
    try:
        data = json.loads(raw.decode("utf-8")) if raw else {}
    except Exception:
        data = {}
    if status < 200 or status >= 300:
        reason = ""
        if isinstance(data, dict):
            for key in ("error_description", "msg", "message", "error"):
                if isinstance(data.get(key), str) and data[key]:
                    reason = data[key]
                    break
        raise SignInError("The token endpoint refused the %s (%d)%s" % (what, status, ": " + reason if reason else ""))
    token = data.get("access_token") if isinstance(data, dict) else None
    if not isinstance(token, str) or not token:
        raise SignInError("The token endpoint answered without an access token.")
    refresh = data.get("refresh_token")
    refresh = refresh if isinstance(refresh, str) else ""
    expires_in = data.get("expires_in")
    expires_at = None
    if isinstance(expires_in, (int, float)) and not isinstance(expires_in, bool):
        expires_at = int((time.time() if now is None else now()) + expires_in)
    return token, refresh, expires_at


def exchange_code(token_endpoint, api_key, code, verifier, post=_post_json, now=None):
    """Redeem the code: POST <endpoint>?grant_type=pkce with {auth_code, code_verifier} -> (access, refresh, expires_at)."""
    return _token_grant(token_endpoint, api_key, "pkce", {"auth_code": code, "code_verifier": verifier}, "code", post, now)


def refresh_access(token_endpoint, api_key, refresh_token, post=_post_json, now=None):
    """Renew without a browser: POST <endpoint>?grant_type=refresh_token with {refresh_token} -> (access, refresh, expires_at)."""
    return _token_grant(token_endpoint, api_key, "refresh_token", {"refresh_token": refresh_token}, "refresh", post, now)


def needs_refresh(expires_at, now=None, margin=REFRESH_MARGIN_S):
    """True when the access token is within margin seconds of its end, or past it.

    A token that never said when it expires is never refreshed on a guess:
    the add-on works against an issuer that mints opaque tokens, or none.
    """
    if expires_at is None:
        return False
    return (time.time() if now is None else now) >= expires_at - margin


def resolve_session(stored, token_endpoint, api_key, now=None, refresh=None):
    """Decide what publishes, from what is stored, renewing when it can.

    stored is {"access", "refresh", "expires_at"}. Returns a dict with "state"
    in {"live", "renewed", "signed_out", "unreachable"} and the tokens to
    keep. A refused refresh clears both tokens: the reason travels in
    "reason", and the caller offers Sign In. An endpoint that could not be
    reached keeps both. Pure apart from the injected refresh.
    """
    access = (stored.get("access") or "").strip()
    refresh_token = (stored.get("refresh") or "").strip()
    expires_at = stored.get("expires_at")
    if not access and not refresh_token:
        return {"state": "signed_out", "access": "", "refresh": "", "expires_at": None, "reason": "no token"}
    if access and not needs_refresh(expires_at, now=now):
        return {"state": "live", "access": access, "refresh": refresh_token, "expires_at": expires_at}
    if not refresh_token:
        return {"state": "signed_out", "access": "", "refresh": "", "expires_at": None, "reason": "the token expired"}
    if refresh is None:
        def refresh(endpoint, key, rt):
            return refresh_access(endpoint, key, rt, now=(lambda: now) if now is not None else None)
    try:
        new_access, new_refresh, new_expires = refresh(token_endpoint, api_key, refresh_token)
    except SignInUnreachable as err:
        # Nothing is known, so nothing is discarded: the stale token and the
        # refresh token stay for the next attempt.
        return {"state": "unreachable", "access": access, "refresh": refresh_token, "expires_at": expires_at, "reason": str(err)}
    except SignInError as err:
        return {"state": "signed_out", "access": "", "refresh": "", "expires_at": None, "reason": str(err)}
    return {"state": "renewed", "access": new_access, "refresh": new_refresh or refresh_token, "expires_at": new_expires}


class _Listener:
    """A one-shot HTTP listener on the loopback. Yields the first good code, refuses everything else."""

    def __init__(self, nonce):
        self._codes = Queue()
        listener = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                code = parse_callback(self.path, nonce)
                if code is None:
                    self.send_response(404)
                    self.send_header("Content-Type", "text/plain; charset=utf-8")
                    self.end_headers()
                    self.wfile.write(b"not found")
                    return
                # Recorded BEFORE the reply goes out: a caller that polls the
                # moment the browser is answered must find the code there.
                listener._codes.put(code)
                page = CALLBACK_PAGE.encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(page)))
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(page)

            def log_message(self, *args):  # quiet: Blender's console is a person's
                pass

        self._server = HTTPServer(("127.0.0.1", 0), Handler)
        self.port = self._server.server_address[1]
        self._thread = threading.Thread(target=self._server.serve_forever, kwargs={"poll_interval": 0.1}, daemon=True)
        self._thread.start()

    def wait(self, timeout):
        """The code, or None if none arrived within `timeout` seconds. Does not block Blender's UI: poll it."""
        try:
            return self._codes.get(timeout=timeout)
        except Empty:
            return None

    def close(self):
        self._server.shutdown()
        self._server.server_close()


def start_listener(nonce):
    """Bind a free loopback port and answer exactly one good callback for `nonce`."""
    return _Listener(nonce)
