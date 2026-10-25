# Copyright (c) 2019-2026 Five Squared Interactive
# SPDX-License-Identifier: MIT

#
#
# Signing in from Blender: an OAuth 2.1 public client on the loopback
# (RFC 6749 + RFC 7636 + RFC 8252), with nothing of Blender in it so every
# rule is checked on plain Python (tools/sign_in_flow_check.py).
#
# The shape. This process mints a PKCE verifier and its S256 challenge and a
# state, listens on http://127.0.0.1:<port>/callback, and sends the browser to
# the provider's authorize endpoint with its client id, that redirect URI, the
# state and the challenge. The person signs in there by whatever method the
# provider offers; the provider sends the browser back to the loopback with a
# single-use code and the same state; this process redeems the code -
# outbound, with the verifier - at the provider's token endpoint. A code is
# worthless to anyone without the verifier, and the verifier never leaves this
# process. A return whose state is not this press's is refused unread.
#
# The port. A provider that honours RFC 8252 section 7.3 accepts any port on
# the loopback, and with no ports configured this listens on any free one.
# Many providers match redirect URIs exactly instead, so a list of ports may be
# configured, each registered with the provider: the first free one is used.
#
# This add-on names no identity service and hardcodes no host. The authorize
# and token addresses, the client id and the ports are preferences (a
# packaged build may carry defaults, a source checkout carries none), so the
# same button works against any OAuth 2.1 provider - or against none, which
# is what keeps a world from needing anyone's permission to exist.

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

#: RFC 7636 section 4.1: the unreserved characters a verifier is made of.
_VERIFIER_ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~"

#: The one method a challenge is made with. The provider is told the same.
CHALLENGE_METHOD = "S256"

#: What is asked for: an identity and the person's email and name.
SCOPE = "openid email profile"

#: The one path the listener answers. Fixed, because providers that match
#: redirect URIs exactly register the whole address.
CALLBACK_PATH = "/callback"

#: The listener's answer to a browser that came back. Plain words, no
#: service names: this file is in the open add-on.
CALLBACK_PAGE = (
    "<!doctype html><meta charset=\"utf-8\"><title>Signed in</title>"
    "<body style=\"font-family:sans-serif;padding:2em\">"
    "<h1>Signed in</h1><p>You can close this tab and go back to Blender.</p></body>"
)
CANCELLED_PAGE = (
    "<!doctype html><meta charset=\"utf-8\"><title>Not signed in</title>"
    "<body style=\"font-family:sans-serif;padding:2em\">"
    "<h1>Not signed in</h1><p>The sign-in was cancelled. You can close this tab.</p></body>"
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


def make_state():
    """The value only this press knows; a return that does not carry it is refused."""
    return secrets.token_urlsafe(24)


def loopback_redirect(port):
    """The address the browser is sent back to. 127.0.0.1, never `localhost` (RFC 8252 section 8.3)."""
    return "http://127.0.0.1:%d%s" % (port, CALLBACK_PATH)


def parse_ports(raw):
    """The configured ports in order, [] for none (any free port), or None when malformed."""
    text = (raw or "").strip()
    if not text:
        return []
    ports = []
    for part in text.split(","):
        part = part.strip()
        if not part.isdigit() or not (1 <= int(part) <= 65535):
            return None
        ports.append(int(part))
    return ports


def build_authorize_url(authorize_url, client_id, challenge, redirect_uri, state):
    """The provider's authorize endpoint, carrying the request. An existing query is kept."""
    parts = urlsplit(authorize_url.strip())
    query = parse_qs(parts.query, keep_blank_values=True)
    query["response_type"] = ["code"]
    query["client_id"] = [client_id.strip()]
    query["redirect_uri"] = [redirect_uri]
    query["state"] = [state]
    query["code_challenge"] = [challenge]
    query["code_challenge_method"] = [CHALLENGE_METHOD]
    query["scope"] = [SCOPE]
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query, doseq=True), parts.fragment))


def parse_callback(path, state):
    """What a callback request brought, or None.

    ("code", <code>) for exactly /callback with this press's state and a code;
    ("error", <reason>) for /callback with this press's state and an error (a
    cancel at the provider); None for anything else, including another state.
    """
    parts = urlsplit(path)
    if parts.path != CALLBACK_PATH:
        return None
    query = parse_qs(parts.query)
    if query.get("state") != [state]:
        return None
    errors = query.get("error")
    if errors and errors[0]:
        description = (query.get("error_description") or [""])[0]
        return ("error", description or errors[0])
    codes = query.get("code")
    if not codes or not codes[0]:
        return None
    return ("code", codes[0])


def validate_sign_in_flow(authorize_url, token_url, client_id, ports, env_token):
    """Return an error sentence, or None when the flow may start.

    The provider has to be configured before a browser is opened, and the last
    refusal is the reason this exists at all: signing in writes the
    preference, and an environment token beats the preference, so a sign-in
    that would change nothing is refused before it wastes the person's time.
    """
    url = (authorize_url or "").strip()
    if not url:
        return (
            "No authorize address. Put your identity provider's OAuth authorize address in "
            "the add-on preferences - this add-on does not assume one."
        )
    if not url.lower().startswith(("http://", "https://")):
        return "The authorize address must start with http:// or https:// - it is a web page your browser opens."
    endpoint = (token_url or "").strip()
    if not endpoint:
        return "No token address. Put your identity provider's OAuth token address in the add-on preferences."
    if not endpoint.lower().startswith(("http://", "https://")):
        return "The token address must start with http:// or https://."
    if not (client_id or "").strip():
        return "No client id. Put the client id your identity provider gave this add-on in the add-on preferences."
    if parse_ports(ports) is None:
        return "The loopback ports must be a comma-separated list of port numbers, or empty for any free port."
    if (env_token or "").strip():
        return (
            "A publish token is set in the environment, and it beats the preference "
            "signing in would write - unset it first, or signing in changes nothing."
        )
    return None


def _post_form(url, headers, body):
    """The one outbound request. Returns (status, bytes); an HTTP error is a status, not an exception."""
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as res:
            return res.status, res.read()
    except urllib.error.HTTPError as err:
        return err.code, err.read()


class SignInUnreachable(SignInError):
    """The token endpoint could not be reached at all (DNS, refused, timeout).

    Distinct from a refusal on purpose: a refusal means the session is over and
    both tokens go; unreachable means nothing is known, so both tokens stay and
    the caller tries again later.
    """


#: Renew this many seconds before the access token's end, so a publish never
#: starts with a token that dies mid-upload.
REFRESH_MARGIN_S = 300


def _token_grant(token_url, fields, what, post, now):
    """One form POST to the token endpoint; returns (access, refresh, expires_at).

    expires_at is seconds since the epoch, or None when the reply did not say.
    The tokens are opaque here: stored and sent, never cracked.
    """
    headers = {"Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json"}
    body = urlencode(fields).encode("ascii")
    try:
        status, raw = post(token_url.strip(), headers, body)
    except Exception as err:  # network down, DNS, refused
        raise SignInUnreachable("Could not reach the token address: %s" % err)
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
        raise SignInError("The token address refused the %s (%d)%s" % (what, status, ": " + reason if reason else ""))
    token = data.get("access_token") if isinstance(data, dict) else None
    if not isinstance(token, str) or not token:
        raise SignInError("The token address answered without an access token.")
    refresh = data.get("refresh_token")
    refresh = refresh if isinstance(refresh, str) else ""
    expires_in = data.get("expires_in")
    expires_at = None
    if isinstance(expires_in, (int, float)) and not isinstance(expires_in, bool):
        expires_at = int((time.time() if now is None else now()) + expires_in)
    return token, refresh, expires_at


def exchange_code(token_url, client_id, code, verifier, redirect_uri, post=_post_form, now=None):
    """Redeem the code with the authorization_code grant -> (access, refresh, expires_at)."""
    fields = {
        "grant_type": "authorization_code",
        "code": code,
        "client_id": client_id.strip(),
        "redirect_uri": redirect_uri,
        "code_verifier": verifier,
    }
    return _token_grant(token_url, fields, "code", post, now)


def refresh_access(token_url, client_id, refresh_token, post=_post_form, now=None):
    """Renew without a browser, with the refresh_token grant -> (access, refresh, expires_at)."""
    fields = {"grant_type": "refresh_token", "refresh_token": refresh_token, "client_id": client_id.strip()}
    return _token_grant(token_url, fields, "refresh", post, now)


def needs_refresh(expires_at, now=None, margin=REFRESH_MARGIN_S):
    """True when the access token is within margin seconds of its end, or past it.

    A token that never said when it expires is never refreshed on a guess:
    the add-on works against an issuer that mints opaque tokens, or none.
    """
    if expires_at is None:
        return False
    return (time.time() if now is None else now) >= expires_at - margin


def resolve_session(stored, token_url, client_id, now=None, refresh=None):
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
        def refresh(url, client, rt):
            return refresh_access(url, client, rt, now=(lambda: now) if now is not None else None)
    try:
        new_access, new_refresh, new_expires = refresh(token_url, client_id, refresh_token)
    except SignInUnreachable as err:
        # Nothing is known, so nothing is discarded: the stale token and the
        # refresh token stay for the next attempt.
        return {"state": "unreachable", "access": access, "refresh": refresh_token, "expires_at": expires_at, "reason": str(err)}
    except SignInError as err:
        return {"state": "signed_out", "access": "", "refresh": "", "expires_at": None, "reason": str(err)}
    return {"state": "renewed", "access": new_access, "refresh": new_refresh or refresh_token, "expires_at": new_expires}


class _Listener:
    """A one-shot HTTP listener on the loopback. Yields the first good return, refuses everything else."""

    def __init__(self, state, ports):
        self._results = Queue()
        listener = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                result = parse_callback(self.path, state)
                if result is None:
                    self.send_response(404)
                    self.send_header("Content-Type", "text/plain; charset=utf-8")
                    self.end_headers()
                    self.wfile.write(b"not found")
                    return
                # Recorded BEFORE the reply goes out: a caller that polls the
                # moment the browser is answered must find it there.
                listener._results.put(result)
                page = (CALLBACK_PAGE if result[0] == "code" else CANCELLED_PAGE).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(page)))
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(page)

            def log_message(self, *args):  # quiet: Blender's console is a person's
                pass

        self._server = _bind(Handler, ports)
        self.port = self._server.server_address[1]
        self._thread = threading.Thread(target=self._server.serve_forever, kwargs={"poll_interval": 0.1}, daemon=True)
        self._thread.start()

    def wait(self, timeout):
        """("code", c) or ("error", reason), or None if nothing came within `timeout` seconds. Poll it."""
        try:
            return self._results.get(timeout=timeout)
        except Empty:
            return None

    def close(self):
        self._server.shutdown()
        self._server.server_close()


def _bind(handler, ports):
    """The first listed port that is free, or any free port when none are listed."""
    if not ports:
        return HTTPServer(("127.0.0.1", 0), handler)
    for port in ports:
        try:
            return HTTPServer(("127.0.0.1", port), handler)
        except OSError:
            continue
    raise OSError(
        "every loopback port the sign-in may use is taken (%s); close what is using them and try again"
        % ", ".join(str(p) for p in ports)
    )


def start_listener(state, ports=()):
    """Listen on the loopback and answer exactly one good return for `state`."""
    return _Listener(state, list(ports))
