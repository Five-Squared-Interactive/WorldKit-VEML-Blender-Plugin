# Copyright (c) 2019-2026 Five Squared Interactive. All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Addresses a BUILD supplies, not addresses this source knows (#308).
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


def default_sign_in_url():
    """The sign-in page a packaged build points at, or ""."""
    return _value("SIGN_IN_URL")


def default_token_endpoint():
    """The identity provider's token endpoint a packaged build redeems codes at, or ""."""
    return _value("TOKEN_ENDPOINT")


def default_identity_api_key():
    """The identity provider's publishable API key a packaged build sends, or ""."""
    return _value("IDENTITY_API_KEY")
