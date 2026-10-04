# Copyright (c) 2019-2026 Five Squared Interactive
# SPDX-License-Identifier: MIT

"""Fetching a Node runtime for the bundled world builder.

The add-on carries the world builder but not a runtime to run it with: the
runtime is tens of megabytes per platform, and shipping one would mean a
release artifact per platform and a signature on each. So the add-on finds
Node if it is already there, and otherwise offers to fetch the official
build — on a press, never on its own. A download nobody asked for is the
behaviour this deliberately does not have.

What arrives is verified before it is unpacked. The expected digest for each
platform is pinned below, so a truncated transfer or a substituted file is
refused rather than extracted, and nothing is left behind when it is.

This module is free of `bpy` so it can be exercised without Blender.
"""
import hashlib
import os
import platform
import shutil
import sys
import tarfile
import tempfile
import zipfile

#: The pinned release. Bumping it means replacing every digest below with the
#: ones nodejs.org publishes for the new version in `SHASUMS256.txt`;
#: `tools/node_pin_check.py` compares this table against that file.
NODE_VERSION = "24.21.0"

BASE_URL = "https://nodejs.org/dist/v{version}/{archive}"

#: Per platform: the archive nodejs.org publishes, and its SHA-256. The key is
#: what `platform_key` returns. A platform absent from this table is one the
#: add-on cannot fetch for, and the interface says so rather than guessing.
ARCHIVES = {
    "win-x64": (
        "node-v{version}-win-x64.zip",
        "158f7685b44de51f6c0df1d153526cbcd3e1bc739a8dfc607721cef75de9e541",
    ),
    "darwin-arm64": (
        "node-v{version}-darwin-arm64.tar.gz",
        "bed7eea5325e1108f32ce5228ddd6a5f0f08a499ee42aa7442aea583702f6057",
    ),
    "darwin-x64": (
        "node-v{version}-darwin-x64.tar.gz",
        "1462cb3b3046b815cf8ea436d3da450ec1a9f11dac7e5a46b0ada5305d7e8097",
    ),
    "linux-x64": (
        "node-v{version}-linux-x64.tar.xz",
        "fd8e59d5a511510f6a298afb548f18c7d2b1be404d8b4a27d94fbe49f56cb2d6",
    ),
}

#: Overrides for a mirror, and for this package's own checks: a URL or local
#: path to take the archive from, and the digest to expect from it. Both must
#: be set together — the pinned digest cannot vouch for someone else's build,
#: and fetching without a digest to check is the thing this module refuses to
#: do.
ARCHIVE_VAR = "VEML_NODE_ARCHIVE"
ARCHIVE_SHA_VAR = "VEML_NODE_ARCHIVE_SHA256"

#: The directory name the archive unpacks into, under the destination.
INSTALL_DIRNAME = "node"


def cpu_name(machine=None, env=None, sixty_four=None):
    """What CPU this is, as a lowercase string, or "" when nothing says.

    `platform.machine()` reads `PROCESSOR_ARCHITECTURE` on Windows and returns
    an EMPTY string when that variable is not in the environment — which is
    how a service account can run on an ordinary x64 box and report no
    architecture at all. Falling straight to "no build for this platform"
    there tells someone with a perfectly standard machine to go and install
    Node themselves.

    So the environment is asked directly, and a 64-bit interpreter is the last
    resort. Windows on ARM still answers ARM64 through one of those variables,
    which is why they are consulted before the word size: the word size alone
    cannot tell the two apart.
    """
    env = os.environ if env is None else env
    named = (machine if machine is not None else platform.machine()) or ""
    if not named:
        named = (env.get("PROCESSOR_ARCHITEW6432") or env.get("PROCESSOR_ARCHITECTURE") or "")
    if not named:
        wide = (sys.maxsize > 2**32) if sixty_four is None else sixty_four
        named = "x86_64" if wide else ""
    return named.lower()


def platform_key(system=None, machine=None, env=None, sixty_four=None):
    """Which entry of `ARCHIVES` this machine needs, or None.

    None is not an error here. It means "no official build this code knows
    how to place", which the caller turns into a sentence rather than a
    failed download — a 32-bit Linux or a Windows on ARM should be told to
    install Node itself, not handed a binary that cannot run.
    """
    system = (system or platform.system()).lower()
    machine = cpu_name(machine, env, sixty_four)
    arm = machine in ("arm64", "aarch64")
    x64 = machine in ("x86_64", "amd64", "x64")
    if system == "windows" and x64:
        return "win-x64"
    if system == "darwin" and arm:
        return "darwin-arm64"
    if system == "darwin" and x64:
        return "darwin-x64"
    if system == "linux" and x64:
        return "linux-x64"
    return None


def archive_for(key, env=None):
    """`(source, sha256, filename)` for a platform key.

    `source` is a URL unless the override names a local path, which is how
    this package's own checks exercise the whole path without a download.
    """
    env = os.environ if env is None else env
    template, digest = ARCHIVES[key]
    filename = template.format(version=NODE_VERSION)
    override = (env.get(ARCHIVE_VAR) or "").strip()
    override_sha = (env.get(ARCHIVE_SHA_VAR) or "").strip()
    if override and override_sha:
        return override, override_sha.lower(), os.path.basename(override) or filename
    return BASE_URL.format(version=NODE_VERSION, archive=filename), digest, filename


def sha256_of(path, chunk=1 << 20):
    """The file's digest, read a megabyte at a time rather than all at once."""
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        while True:
            block = handle.read(chunk)
            if not block:
                break
            digest.update(block)
    return digest.hexdigest()


def archive_root(filename):
    """The single directory the archive unpacks into.

    Every official archive contains exactly one top-level directory named
    after the build, so the extracted runtime can be found without walking
    the tree.
    """
    for suffix in (".zip", ".tar.gz", ".tar.xz"):
        if filename.endswith(suffix):
            return filename[: -len(suffix)]
    return filename


def node_exe_in(root, key):
    """Where `node` sits inside an extracted archive."""
    if key.startswith("win"):
        return os.path.join(root, "node.exe")
    return os.path.join(root, "bin", "node")


def extract(archive_path, dest):
    """Unpack the archive into `dest`, and return the directory it made."""
    before = set(os.listdir(dest)) if os.path.isdir(dest) else set()
    if archive_path.endswith(".zip"):
        with zipfile.ZipFile(archive_path) as zf:
            zf.extractall(dest)
    else:
        with tarfile.open(archive_path) as tf:
            # `filter="data"` refuses member names that would escape the
            # destination. The digest has already been checked, so the archive
            # is the one nodejs.org published; this is the belt to that braces,
            # and it is skipped only on interpreters too old to offer it.
            try:
                tf.extractall(dest, filter="data")
            except TypeError:
                tf.extractall(dest)
    made = [name for name in os.listdir(dest) if name not in before]
    if len(made) != 1:
        raise ValueError("expected one directory in the archive, got " + repr(sorted(made)))
    return os.path.join(dest, made[0])


def installed_node(dest, key=None):
    """The managed Node under `dest`, or None.

    Looked up by walking one level rather than by remembering a version, so a
    runtime placed by an older release of the add-on is still found after the
    pin moves.
    """
    key = key or platform_key()
    if not key:
        return None
    home = os.path.join(dest, INSTALL_DIRNAME)
    if not os.path.isdir(home):
        return None
    for name in sorted(os.listdir(home)):
        candidate = node_exe_in(os.path.join(home, name), key)
        if os.path.isfile(candidate):
            return candidate
    return None


def install(dest, fetch, key=None, env=None, progress=None):
    """Fetch, verify and unpack the runtime. Returns the `node` path.

    `fetch(source, out_path, progress)` does the transfer, so the caller
    chooses how — this module does not reach the network itself, which is
    what lets the whole sequence be checked offline.

    Nothing is written where it would be found until the digest matches: the
    archive lands in a temporary directory and a mismatch raises with that
    directory already gone. A half-written runtime that `installed_node`
    would then happily return is worse than no runtime at all.
    """
    key = key or platform_key()
    if not key:
        raise ValueError("no official Node build for this platform")
    source, expected, filename = archive_for(key, env)
    work = tempfile.mkdtemp(prefix="veml-node-")
    try:
        archive_path = os.path.join(work, filename)
        fetch(source, archive_path, progress)
        actual = sha256_of(archive_path)
        if actual != expected:
            raise ValueError(
                "the downloaded runtime does not match its published checksum "
                "(expected " + expected + ", got " + actual + ")"
            )
        staged = extract(archive_path, work)
        exe = node_exe_in(staged, key)
        if not os.path.isfile(exe):
            raise ValueError("the archive contained no node executable at " + exe)
        home = os.path.join(dest, INSTALL_DIRNAME)
        os.makedirs(home, exist_ok=True)
        final = os.path.join(home, os.path.basename(staged))
        if os.path.isdir(final):
            shutil.rmtree(final, ignore_errors=True)
        shutil.move(staged, final)
        placed = node_exe_in(final, key)
        if not key.startswith("win"):
            os.chmod(placed, 0o755)
        return placed
    finally:
        shutil.rmtree(work, ignore_errors=True)
