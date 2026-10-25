# Copyright (c) 2019-2026 Five Squared Interactive
# SPDX-License-Identifier: MIT

#
#
# Addresses a BUILD supplies, not addresses this source knows.
#
# The goal is that someone installs the add-on and presses a button without
# typing a server address. The obstacle is the perimeter rule: nothing in
# this tree may name a Five Squared service, and CI greps every TRACKED file
# under `packages/blender-ingest` for it.
#
# Both hold at once if the address arrives at package time. `tools/
# build-addon-zip.mjs --publish <url> --viewer <url>` writes `site.py` into
# the zip; it is never committed, so the grep sees nothing, and the shipped
# add-on comes pointed somewhere real. A build with no flags produces no
# `site.py` and every field is empty, which is the open-source default and
# exactly what a self-hoster wants.
#
# So this file is the seam, and it names nothing.

try:  # pragma: no cover - present only in a packaged build
    from . import site as _site
except ImportError:  # running from a source checkout
    _site = None


def _value(name):
    raw = getattr(_site, name, "") if _site is not None else ""
    return raw.strip() if isinstance(raw, str) else ""


def default_publish_endpoint():
    """The publish service a packaged build points at, or ""."""
    return _value("PUBLISH_ENDPOINT")


def default_viewer_url():
    """The viewer a packaged build opens worlds in, or ""."""
    return _value("VIEWER_URL")


def default_authorize_url():
    """The identity provider's OAuth authorize address a packaged build signs in at, or ""."""
    return _value("AUTHORIZE_URL")


def default_oauth_token_url():
    """The identity provider's OAuth token address a packaged build redeems codes at, or ""."""
    return _value("OAUTH_TOKEN_URL")


def default_oauth_client_id():
    """The client id the identity provider gave a packaged build, or ""."""
    return _value("OAUTH_CLIENT_ID")


def default_loopback_ports():
    """The loopback ports a packaged build's client is registered with, comma-separated, or ""."""
    return _value("LOOPBACK_PORTS")


def default_sync_address():
    """The rendezvous a packaged build makes worlds meet at, or ""."""
    return _value("SYNC_ADDRESS")
