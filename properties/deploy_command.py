# Copyright (c) 2019-2026 Five Squared Interactive. All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# "Save as My World" (#119) command construction — deliberately bpy-free so
# CI pins it without a Blender install (the entry_point.py precedent, #115).
#
# The operator invokes `<ingest cmd> <blend> --deploy <dir> [--title <t>]`,
# the same bare invocation corpus/README.md records. `command` may itself be
# several shell tokens (the addon-preferences default "veml-ingest", or the
# monorepo-verbatim "node packages/ingest/dist/cli.js") — only the COMMAND
# string is tokenized (shlex, no shell spawned); `blend_path` and
# `deploy_dir` ride as single argv items VERBATIM, so a path containing
# spaces or shell metacharacters is never reinterpreted.
#
# Publishing (#257 story 3) rides the same invocation: `--publish <url>` and,
# once a world exists, `--world-id <id>`. The TOKEN never appears here —
# see publish_env.

import base64
import json
import os
import re
import shlex
import shutil
import time
from urllib.parse import quote, urlsplit, urlunsplit

DEFAULT_INGEST_COMMAND = "veml-ingest"

#: A viewer to open worlds in, for someone running a local shell. Empty by
#: default (#367): a published world opens at its OWN address, which the
#: service that serves it answers with the shell, so the add-on points a
#: first press at nobody's server and no shared link names a viewer.
DEFAULT_VIEWER_URL = ""

#: The environment variable veml-ingest reads its publish credential from.
PUBLISH_TOKEN_VAR = "VEML_PUBLISH_TOKEN"

#: Where a token came from, as the panel says it. These are shown to a
#: person, not compared by machines, so they read like English.
TOKEN_FROM_ENV = PUBLISH_TOKEN_VAR + " in the environment"
TOKEN_FROM_PREFS = "the add-on preferences"

# The two lines `veml-ingest --publish` prints on success. This is a parsing
# contract with packages/ingest/src/cli.ts, which carries the same note: the
# Blender addon reads these back to show the link and to remember the world.
_WORLD_URL = re.compile(r"^\s*world:\s*(\S+)\s*$", re.MULTILINE)
_WORLD_ID = re.compile(r"^\s*id\s+(\S+)\s", re.MULTILINE)


def validate_view_inputs(viewer_url, world_url):
    """Return an error string, or None when the world can actually be opened.

    Two independent causes, two sentences — the panel shows whichever
    applies, and the operator's poll() rejects on it too (the
    validate_deploy_inputs precedent).

    The `http`/`https` requirement is not fussiness. The viewer FETCHES the
    world document, so a `file://` path, a bare Windows path or a relative
    one all produce a tab onto a blank screen with nothing in the console
    worth reading. Refusing here, with a sentence naming what is needed,
    beats opening a browser that cannot succeed.
    """
    # No viewer is not a fault (#367): the world's own address opens it.
    world = (world_url or "").strip()
    if not world:
        return "No world address yet — publish the world, or paste the address it is served at."
    if not (world.startswith("http://") or world.startswith("https://")):
        return "The world address must be an http:// or https:// URL — the viewer fetches it over the network."
    return None


def viewer_world_url(viewer_url, world_url):
    """The address that opens `world_url` in the viewer at `viewer_url`.

    `<viewer>/#world-url=<percent-encoded world address>`.

    The encoding is the whole job, and it is why this is a function rather
    than a format string in the operator. A world address contains `:` and
    `/` and may contain `?` or `#`; concatenated raw into a fragment it
    silently TRUNCATES at the first `?`, and the viewer then fetches a
    shortened address — an empty world with no error anywhere. `safe=""`
    encodes every reserved character, including the ones that look harmless.

    Returns None when the inputs are unusable, so a caller cannot build a
    doomed address by skipping the validation.

    With no viewer configured (#367) the address is the world's own: the
    document's folder, without the file name, the query or a trailing
    slash - `https://worlds.example/w/abc/index.veml` opens at
    `https://worlds.example/w/abc`. The service serving the world answers
    that with the shell; a configured viewer still wins.
    """
    if validate_view_inputs(viewer_url, world_url) is not None:
        return None
    if not (viewer_url or "").strip():
        return world_own_address(world_url)
    # One slash, however the viewer was typed — a bare origin, a trailing
    # slash, or a path the viewer is served under, which is kept.
    base = viewer_url.strip().rstrip("/")
    return f"{base}/#world-url={quote(world_url.strip(), safe='')}"


def world_own_address(world_url):
    """The folder a world document lives in, as an address: no file, no query, no trailing slash."""
    parts = urlsplit(world_url.strip())
    path = parts.path.rstrip("/")
    last = path.rsplit("/", 1)[-1]
    if "." in last:  # a document name: index.veml, or whatever the world's is
        path = path[: -len(last)].rstrip("/")
    return urlunsplit((parts.scheme, parts.netloc, path, "", ""))


#: Where the built ingest CLI sits relative to the add-on's own directory in
#: a monorepo checkout: Blender-VEML/ -> blender-ingest/ -> packages/.
#: Where the built CLI sits relative to the add-on, in the two situations
#: that exist. The CHECKOUT case (#297): the add-on was loaded from the
#: monorepo and the CLI is two levels up in `packages/ingest`. The INSTALLED
#: case (#308): the add-on came from its zip, which carries the bundled
#: ingest beside its own modules — which is what lets someone who cloned
#: nothing press the button.
_INGEST_CLI_CANDIDATES = (
    ("ingest", "dist", "cli.js"),
    ("..", "..", "ingest", "dist", "cli.js"),
)


def default_world_dir(blend_path):
    """Where the ingest writes a world when nobody told it otherwise (#297).

    Beside the .blend and named for it. This is not a choice this module
    makes - it is packages/ingest's own default since #295, restated here so
    the panel can SAY where a blank field ends up and the report can name the
    folder the panel promised.

    An unsaved file returns "" rather than a relative path: a path relative
    to wherever Blender was launched from is how a deploy ended up trying to
    write into C:/Program Files.
    """
    if not blend_path:
        return ""
    stem = os.path.splitext(os.path.basename(blend_path))[0]
    if not stem:
        return ""
    return os.path.join(os.path.dirname(blend_path), f"{stem}-world")


def effective_world_dir(deploy_dir, blend_path):
    """The directory the world will actually end up in.

    A directory the user typed always wins. The default is a fallback, never
    an override - someone who chose where their world goes keeps it there.
    """
    if deploy_dir:
        return deploy_dir
    return default_world_dir(blend_path)


def should_open_after_publish(enabled, viewer_url, world_url):
    """Whether the press should end in the world rather than with a link.

    "Install it, press it, be there" was the ask; a status bar holding an
    address someone then selects and pastes is the step that was left. So a
    successful publish opens the viewer, unless:

      - the person unticked it, or
      - nothing was published (a local deploy has no address), or
      - `validate_view_inputs` refuses - no viewer configured, or a world
        address the viewer could not fetch. A browser onto a blank screen is
        worse than no browser, and the Open in Browser button already
        declines for exactly these reasons. Auto-open does not get to route
        around a rule the manual press obeys.
    """
    if not enabled:
        return False
    return validate_view_inputs(viewer_url, world_url) is None


def deploy_message(world_dir, entry_line, url):
    """The one sentence the press leaves behind.

    A status bar shows ONE operator report, and a successful publish used to
    replace the deploy line outright - so the entry point, the single thing
    that says where a visitor arrives, was printed on every press that failed
    to publish and on none that succeeded. The founder went looking for it
    and found nothing.

    So: the address when there is one, the folder when there is not, and the
    entry point either way. `entry_line` is the ingest's own line, already
    reading "entry point: ...", or None when it said nothing - which is not
    an empty pair of brackets.
    """
    message = f"Published: {url}" if url else f"Deployed to {world_dir}"
    if entry_line:
        message += f" ({entry_line})"
    return message


#: What the export prints (#396). A parsing contract with packages/ingest:
#: ingest.ts's entry-point bounds warning and cli.ts's DEAD references line.
_ENTRY_OUTSIDE = re.compile(r"entry point \([^)]*\) lies OUTSIDE the model bounds")
_DEAD_REFERENCES = re.compile(r"^\s*DEAD references \([^)]*\):\s*(.+?)\s*$", re.MULTILINE)


def plain_warnings(stdout, stderr):
    """The export's warnings that matter to a person, as instructions (#396).

    Order is importance: where a visitor arrives comes first (a world entered
    from outside is grey space), then what will look wrong. Everything else
    the export warns about is still reported line by line; these are the ones
    the last status-bar line can carry.
    """
    out = []
    if _ENTRY_OUTSIDE.search(stderr or "") or _ENTRY_OUTSIDE.search(stdout or ""):
        out.append(
            "Visitors will start outside the model. Put a camera inside it and tick "
            "VEML Entry Point on it (Object tab, VEML Entity panel)."
        )
    dead = _DEAD_REFERENCES.search(stdout or "")
    if dead:
        n = len([p for p in dead.group(1).split(",") if p.strip()])
        noun = "texture file is" if n == 1 else "texture files are"
        out.append(
            f"{n} {noun} missing, so some materials show pink. "
            "In Blender: File > External Data > Find Missing Files."
        )
    return out


def final_report(world_dir, entry_line, url, warnings):
    """(kind, text) for the LAST report of a press - the one the status bar shows (#396).

    Blender's status bar shows one report, the latest. A warning reported
    before a success line was covered by it, so a world that publishes with
    a problem ends on a WARNING carrying both the address and what to fix,
    and says how many more are in the Info log.
    """
    message = deploy_message(world_dir, entry_line, url)
    if not warnings:
        return "INFO", message
    first = warnings[0]
    text = f"{message} — but {first[:1].lower()}{first[1:]}"
    if len(warnings) > 1:
        more = len(warnings) - 1
        text += f" ({more} more in the Info log)"
    return "WARNING", text


def addon_dir_from(module_file):
    """The add-on's own directory, given a file one level inside it.

    REALPATH, not abspath. An add-on is enabled by its directory under
    Blender's scripts/addons, and the way to run a checkout's copy is to
    point that directory at the checkout - a junction on Windows, a symlink
    elsewhere. abspath leaves the link unresolved, so walking up from
    `__file__` lands in Blender's configuration directory, where there is no
    checkout and no built CLI: detection would find nothing, silently.
    """
    return os.path.dirname(os.path.dirname(os.path.realpath(module_file)))


def bundled_ingest_cli(addon_dir, exists=os.path.exists):
    """The built ingest CLI this add-on can reach, or "".

    Two places, in order: the one the zip CARRIED (#308), then the one in a
    monorepo checkout (#297). The carried copy comes first because an
    installed add-on that also happens to sit inside a checkout should use
    what it shipped with rather than whatever state that checkout is in.

    `exists` is injected so the rule is checkable without either layout
    arranged around the test.
    """
    if not addon_dir:
        return ""
    for parts in _INGEST_CLI_CANDIDATES:
        candidate = os.path.normpath(os.path.join(addon_dir, *parts))
        if exists(candidate):
            return candidate
    return ""


#: Where Node was found, remembered for the session. `None` means "looked and
#: found nothing"; the sentinel below means "not looked yet", because a machine
#: with no Node must remember the absence too or it pays the full PATH walk on
#: every redraw.
_NOT_LOOKED = object()
_node_cache = _NOT_LOOKED


def reset_node_cache():
    """Forget the remembered Node. A testing seam, and the only way to re-look."""
    global _node_cache
    _node_cache = _NOT_LOOKED


def node_executable(env=None, which=None):
    """Where Node is, or None.

    Looked up rather than configured — asking someone to find their own
    `node` is the kind of step an installable add-on exists to remove.
    `VEML_NODE` wins for anyone with several.

    The add-on does not SHIP Node. The runtime is 86 MB, 33 MB compressed,
    and needs a build per platform plus code signing to avoid tripping every
    OS's download warnings — a release-pipeline problem rather than a
    packaging one. So it is found, and when it is absent the interface says
    what to install instead of failing obscurely at spawn time.
    """
    env = os.environ if env is None else env
    # The variable is read every time, deliberately: someone who sets it
    # expects it to take effect, and reading one environment key is free.
    explicit = (env.get("VEML_NODE") or "").strip()
    if explicit:
        return explicit

    # PATH is walked ONCE per session (#368 review). `veml_scene_panel.py`
    # calls this from draw(), which fires on every interface event - mouse-move
    # over the panel, viewport orbit, any property edit - and `shutil.which`
    # stats every directory on PATH. I added that draw-time call in #308 for a
    # label naming which ingest is in use; the label is worth having, a
    # filesystem scan per frame is not.
    #
    # Same shape as `resolvedPython` in packages/ingest/src/validate/xsd.ts,
    # which caches for the same reason and offers the same reset seam.
    global _node_cache
    if _node_cache is not _NOT_LOOKED:
        return _node_cache
    finder = shutil.which if which is None else which
    for name in ("node", "node.exe"):
        found = finder(name)
        if found:
            _node_cache = found
            return found
    _node_cache = None
    return None


#: What `resolve_ingest_command` returns when it found the world builder but
#: not the runtime it needs. Distinct from "" so the caller can tell the two
#: apart: nothing to run at all, versus something to run and no way to run it.
NODE_MISSING = "node-missing"

NODE_MISSING_MESSAGE = (
    "This add-on ships its own world builder, but it needs Node.js to run it "
    "and Node was not found. Install the LTS build from nodejs.org, restart "
    "Blender, and press again. There is nothing else to configure."
)


def resolve_ingest_command(preference, addon_dir, exists=os.path.exists, env=None, which=None):
    """The command the button actually runs (#297).

    A preference the user CHANGED always wins: auto-detection fills a blank,
    it never overrules a decision. Only the untouched default is replaced,
    and only when a built CLI is actually sitting in the checkout the add-on
    was loaded from - `veml-ingest` is not on PATH in a monorepo, so the
    default's only outcome there is `could not run 'veml-ingest'`.

    The CLI path is quoted because it routinely contains a space on Windows
    and the result goes through shlex.split in build_deploy_argv.
    """
    command = (preference or "").strip()
    if command and command != DEFAULT_INGEST_COMMAND:
        return command
    cli = bundled_ingest_cli(addon_dir, exists)
    if cli:
        node = node_executable(env, which)
        # A bare `node` here produced "could not run 'node'" at spawn time on
        # a machine without it, which reads as the add-on being broken. Say
        # which of the two things is missing.
        return f'"{node}" "{cli}"' if node else NODE_MISSING
    return DEFAULT_INGEST_COMMAND


def validate_deploy_inputs(blend_path, deploy_dir):
    """Return an error string, or None when the inputs are usable.

    Distinct messages for the independent ways the button stays disabled -
    the panel shows whichever applies, and the operator's poll() rejects on
    it too.

    An EMPTY deploy directory is not an error any more (#297): it means the
    world goes beside the .blend. What is an error is aiming --deploy at that
    same folder, because the ingest refuses a deploy target equal to its own
    output ("the world is already there") - a true refusal with a message
    that makes no sense until you know what --deploy is for. Caught here, in
    the panel, with a sentence that says what to do about it.
    """
    if not blend_path:
        return "Save the .blend file before using Save as My World."
    if deploy_dir and _same_path(deploy_dir, default_world_dir(blend_path)):
        return (
            "The deploy directory is the same folder the ingest writes the world "
            "into. Leave it empty to write the world there, or point it at the "
            "location you serve worlds from."
        )
    return None


def failure_reason(stdout, stderr, lines=12):
    """What to SHOW a person when the ingest exits non-zero.

    Not a tail. The ingest prints its whole report and then the reason,
    last - and Blender truncates a long operator report, so a tail of
    successful-looking output pushes the one actionable sentence off the
    end. Measured in real Blender with a stale token: the person saw
    "deploy failed (exit 1)" followed by "realized 0 ... baked 0 ... entry
    point: bounds framing" and nothing about the token at all.

    So: the `error:` lines and their indented continuations, which is
    exactly the part the ingest wrote to be read. Only when there are none
    does this fall back to the tail, because a crash has no error: line and
    losing a traceback would be worse.
    """
    text = "\n".join(t for t in (stdout, stderr) if t)
    all_lines = text.splitlines()

    reason = []
    collecting = False
    for line in all_lines:
        if line.lstrip().lower().startswith("error:"):
            collecting = True
            # Blender already prefixes the report with "Error: ", so the
            # ingest's own marker would read "Error: error: ...".
            reason.append(line.strip()[len("error:"):].strip())
        elif collecting and line.startswith((" ", "\t")) and line.strip():
            # An indented continuation belongs to the error above it - the
            # ingest uses one to say where the world folder is, which is
            # the other half of what a person needs.
            reason.append(line.strip())
        elif collecting:
            collecting = False
    if reason:
        return "\n".join(reason)

    tail = [line for line in all_lines if line.strip()][-lines:]
    if tail:
        return "\n".join(tail)
    return "the ingest failed and printed nothing; run it from a terminal to see why"


def _same_path(left, right):
    """Whether two paths name the same place, as far as the filesystem cares."""
    if not left or not right:
        return False
    return os.path.normcase(os.path.normpath(left)) == os.path.normcase(
        os.path.normpath(right)
    )


def validate_publish_inputs(publish_endpoint, publish_token, now=None):
    """Return an error string, or None when publishing can proceed.

    Publishing is OPTIONAL: no endpoint is not an error, it just means the
    world is written locally and goes no further. Every other refusal
    happens here, before anything is saved or shelled out, and each cause
    reads differently so the panel can say which one it is.

    now is injected so the expiry refusal is testable; it defaults to the
    real clock, which is what the panel and the operator both pass.
    """
    if not publish_endpoint:
        return None
    endpoint = publish_endpoint.strip()
    if not endpoint.lower().startswith(("http://", "https://")):
        return (
            "The publish address must start with http:// or https:// — "
            "a world is published to a web address, not a local path."
        )
    if not publish_token:
        return (
            "No publish token. Add one in the add-on preferences, or set "
            f"{PUBLISH_TOKEN_VAR} in the environment, before publishing."
        )
    # A 24-hour credential that ran out. Say so here rather than fifteen
    # seconds into an upload, and only when the token actually claims an
    # expiry - an opaque token is never refused for one it never made.
    expires = token_expiry(publish_token)
    if expires is not None and expires <= (time.time() if now is None else now):
        return (
            "The publish token has expired. Sign in again, or paste a current one "
            "into the add-on preferences."
        )
    return None


def build_deploy_argv(
    command,
    blend_path,
    deploy_dir,
    title="",
    publish_endpoint="",
    world_id="",
    no_lookdev_sky=False,
    sync_address="",
    sync_session="",
):
    """Build the argv list for the ingest CLI's --deploy invocation.

    An empty `deploy_dir` omits `--deploy`: see the note at the branch.

    Returns a list, never a shell string — the caller MUST subprocess it
    directly (shell=False) so no argument can be reinterpreted as a shell
    token. `title` is omitted entirely when empty/falsy: ingest's own
    default (the input filename stem) then applies.

    `sync_address` adds `--sync <address>` and, with it, `--session <name>`
    when one was given. Without an address nothing is declared.

    `no_lookdev_sky` adds `--no-lookdev-sky`, and is passed ONLY when asked:
    the flag opts OUT of a documented default, so sending it unasked would
    change what ships for everyone who never touched the checkbox.

    `publish_endpoint` adds `--publish`; `world_id` adds `--world-id`, and
    is ignored without an endpoint because it would mean nothing. There is
    deliberately NO token parameter: a credential in argv is a credential in
    the machine's process list. It goes through publish_env instead.
    """
    argv = shlex.split(command) + [blend_path]
    # `--deploy` is the atomic swap into a SERVING location, and the ingest
    # refuses a target equal to its own output folder ("the world is already
    # there"). An empty field therefore means no --deploy at all: the ingest
    # writes its world beside the .blend and that is the whole job. Passing
    # --deploy <the default output folder> is precisely the collision the CLI
    # rejects, which is how this was found - by running it (#297).
    if deploy_dir:
        argv += ["--deploy", deploy_dir]
    if title:
        argv += ["--title", title]
    if no_lookdev_sky:
        argv += ["--no-lookdev-sky"]
    # The room (#257 story 4). Only with an address: the CLI refuses a
    # --session with no --sync before any work, so the button never sends
    # one alone, and a world with no declaration stays fully static.
    if sync_address:
        argv += ["--sync", sync_address]
        if sync_session:
            argv += ["--session", sync_session]
    if publish_endpoint:
        argv += ["--publish", publish_endpoint]
        if world_id:
            argv += ["--world-id", world_id]
    return argv


def resolve_publish_token(env_token, pref_token):
    """Which token publishes, where it came from, and whether that is a trap.

    Returns (token, source, conflict).

    The environment variable WINS. That rule predates the sign-in button and
    is kept deliberately: someone who keeps credentials out of config files
    should not also have to remember to blank a preference field, and a
    scripted or CI-driven Blender depends on it.

    But the rule plus a "Sign in" button is a lie waiting to happen. The
    button writes the preference; the stale variable still publishes. So
    when both are set and they DIFFER, conflict is True and the interface
    says so. Both set and identical is not a conflict - that is just having
    signed in twice.
    """
    env_token = (env_token or "").strip()
    pref_token = (pref_token or "").strip()
    if env_token:
        return (env_token, TOKEN_FROM_ENV, bool(pref_token) and pref_token != env_token)
    if pref_token:
        return (pref_token, TOKEN_FROM_PREFS, False)
    return ("", "", False)


def token_needs_sign_in(publish_token, now=None):
    """True when there is no token, or the token says it has expired (#366).

    The panel offers Sign In on exactly these; an opaque token that claims
    no expiry is never refused for one it never made.
    """
    if not (publish_token or "").strip():
        return True
    expires = token_expiry(publish_token)
    return expires is not None and expires <= (time.time() if now is None else now)


def token_expiry(publish_token):
    """When this token expires, in seconds since the epoch, or None.

    Reads the exp claim out of a JWT payload WITHOUT verifying the
    signature. That is a presentation decision, not a security one - the
    publish service verifies, and nothing here is trusted by anything.

    A token that is not a JWT simply does not say, and None means exactly
    that: unknown. The add-on must work against an issuer that mints opaque
    tokens, or none at all, so a guess here would be worse than silence.
    Every malformed input returns None rather than raising: the panel calls
    this on every redraw.
    """
    if not publish_token:
        return None
    parts = publish_token.split(".")
    if len(parts) != 3:
        return None
    payload = parts[1]
    try:
        padded = payload + "=" * (-len(payload) % 4)
        claims = json.loads(base64.urlsafe_b64decode(padded.encode("ascii")).decode("utf-8"))
    except Exception:
        return None
    if not isinstance(claims, dict):
        return None
    exp = claims.get("exp")
    # True is an int in Python, and a token claiming "exp": true is not
    # claiming a time. Numbers only, and real ones.
    if isinstance(exp, bool) or not isinstance(exp, (int, float)):
        return None
    return exp


def _plain_duration(seconds):
    """A rough duration a person reads at a glance, never a countdown."""
    seconds = int(abs(seconds))
    if seconds >= 7200:
        return str(seconds // 3600) + " hours"
    if seconds >= 3600:
        return "1 hour"
    if seconds >= 120:
        return str(seconds // 60) + " minutes"
    return "under a minute"


def describe_publish_token(publish_token, source, now=None):
    """The one line the panel shows about the credential it would use.

    Names the source always, and the time left only when the token actually
    says. Empty string when there is no token - the panel has a separate,
    louder line for that.
    """
    if not publish_token:
        return ""
    expires = token_expiry(publish_token)
    if expires is None:
        return "Publishing as the token from " + source + "."
    remaining = expires - (time.time() if now is None else now)
    if remaining <= 0:
        return "The token from " + source + " expired " + _plain_duration(remaining) + " ago."
    return (
        "Publishing as the token from " + source
        + ", good for another " + _plain_duration(remaining) + "."
    )


def validate_sign_in(sign_in_url, env_token):
    """Return an error string, or None when the browser may be opened.

    The add-on hardcodes no issuer. The address is a preference, empty by
    default, so this add-on names no service and works against any OIDC
    issuer or none - which is the perimeter rule, and the thesis behind it.

    The third refusal is the reason this function exists. Signing in writes
    the preference, and the environment variable beats the preference. We
    refuse BEFORE opening a browser rather than after taking someone
    through a sign-in that would have changed nothing.
    """
    url = (sign_in_url or "").strip()
    if not url:
        return (
            "No sign-in address. Put your identity provider's sign-in URL in the "
            "add-on preferences - this add-on does not assume one."
        )
    if not url.lower().startswith(("http://", "https://")):
        return (
            "The sign-in address must start with http:// or https:// - "
            "it is a web page your browser opens."
        )
    if (env_token or "").strip():
        return (
            PUBLISH_TOKEN_VAR + " is set in the environment, and it beats the token "
            "signing in would store - so signing in would change nothing. Unset "
            + PUBLISH_TOKEN_VAR + " first, or just keep using it."
        )
    return None


def publish_env(base_env, publish_token):
    """The child process's environment, carrying the token and nothing else.

    Returns a NEW dict — the caller's environment is never mutated, so a
    token cannot leak into anything else this Blender session spawns. An
    empty token sets no variable at all, rather than an empty one that would
    look configured and fail further away.
    """
    env = dict(base_env)
    if publish_token:
        env[PUBLISH_TOKEN_VAR] = publish_token
    return env


def parse_publish_result(stdout):
    """Read the world's URL and id back out of the ingest's output.

    Returns `(url, world_id)`, either of which is None when the run did not
    publish or did not finish printing. Both must be present to count: half
    a result would put a wrong id in the scene, and the next press would
    then overwrite the wrong world — or fail against one that is not there.
    """
    url_match = _WORLD_URL.search(stdout or "")
    id_match = _WORLD_ID.search(stdout or "")
    if not url_match or not id_match:
        return (None, None)
    return (url_match.group(1), id_match.group(1))
