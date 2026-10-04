# Copyright (c) 2019-2026 Five Squared Interactive
# SPDX-License-Identifier: MIT

"""Fetching the Node runtime the bundled world builder needs.

The add-on does not ship a runtime, so on a machine without one the panel
offers this instead of a dead end. It runs only when pressed: the transfer,
the checksum and the unpacking all happen behind this operator and nowhere
else, so nothing is ever downloaded by drawing a panel or loading a file.

The work happens on a worker thread and the operator reports from a timer,
because tens of megabytes on a slow connection is long enough that a frozen
window reads as a crash. The thread touches no Blender data — it writes to a
temporary directory and leaves a message behind; everything that touches
`bpy` happens in `modal`.
"""
import os
import threading
import urllib.request

import bpy

from ..utils import node_runtime
from ..properties import deploy_command

#: Where the runtime is kept: beside Blender's own user data rather than
#: inside the add-on, so reinstalling or upgrading the add-on does not throw
#: it away and a read-only add-on directory is not a problem.
DATA_SUBDIR = "veml"

#: Read in chunks so progress can be reported, and so a large archive is
#: never held in memory.
CHUNK = 1 << 18


def runtime_dir(create=False):
    """The directory the managed runtime lives under."""
    return bpy.utils.user_resource('DATAFILES', path=DATA_SUBDIR, create=create)


def managed_node():
    """The managed Node, or None. Safe to call when nothing was ever fetched."""
    try:
        base = runtime_dir()
    except Exception:
        return None
    if not base:
        return None
    return node_runtime.installed_node(base)


class _Progress:
    """What the worker has to say, read by the timer on the main thread."""

    def __init__(self):
        self.lock = threading.Lock()
        self.message = "Starting…"
        self.done = False
        self.error = None
        self.path = None

    def say(self, message):
        with self.lock:
            self.message = message

    def read(self):
        with self.lock:
            return self.message, self.done, self.error, self.path

    def finish(self, path=None, error=None):
        with self.lock:
            self.path, self.error, self.done = path, error, True


def _download(source, out_path, progress=None):
    """Fetch `source` to `out_path`. A local path is copied, not requested.

    The local case exists because the mirror override may name a file, which
    is how this package's checks drive the whole sequence without a transfer.
    """
    if os.path.isfile(source):
        import shutil

        shutil.copyfile(source, out_path)
        return
    request = urllib.request.Request(source, headers={"User-Agent": "veml-blender-addon"})
    with urllib.request.urlopen(request, timeout=60) as response:
        total = int(response.headers.get("Content-Length") or 0)
        seen = 0
        with open(out_path, "wb") as handle:
            while True:
                block = response.read(CHUNK)
                if not block:
                    break
                handle.write(block)
                seen += len(block)
                if progress is not None:
                    if total:
                        progress("Downloading Node… %d%%" % (seen * 100 // total))
                    else:
                        progress("Downloading Node… %d MB" % (seen >> 20))


def _work(progress, dest):
    try:
        placed = node_runtime.install(dest, _download, progress=progress.say)
    except Exception as err:
        progress.finish(error=str(err))
    else:
        progress.finish(path=placed)


class VEML_OT_get_node(bpy.types.Operator):
    """Download the Node.js runtime this add-on needs, and verify it"""

    bl_idname = "veml.get_node"
    bl_label = "Get Node.js"
    bl_options = {'REGISTER'}

    _timer = None
    _progress = None
    _thread = None

    @classmethod
    def poll(cls, context):
        # Offered only where it can work. A platform with no official build
        # gets a sentence in the panel instead of a button that would fail.
        return node_runtime.platform_key() is not None

    def _start(self, context):
        self._progress = _Progress()
        dest = runtime_dir(create=True)
        self._thread = threading.Thread(target=_work, args=(self._progress, dest), daemon=True)
        self._thread.start()

    def _settle(self, context, error, path):
        """Report, and make the new runtime visible to the rest of the add-on."""
        if error:
            self.report({'ERROR'}, "Could not install Node.js: " + error)
            return {'CANCELLED'}
        # The lookup caches where Node was found, including its absence, so
        # without this the panel keeps saying it is missing until a restart.
        deploy_command.reset_node_cache()
        self.report({'INFO'}, "Node.js installed. Press the button again.")
        return {'FINISHED'}

    def execute(self, context):
        # Background Blender runs no modal operators, and a script that calls
        # this expects it to have happened when it returns. Same work, waited
        # on rather than polled.
        self._start(context)
        self._thread.join()
        _message, _done, error, path = self._progress.read()
        return self._settle(context, error, path)

    def invoke(self, context, event):
        if bpy.app.background:
            return self.execute(context)
        self._start(context)
        window_manager = context.window_manager
        self._timer = window_manager.event_timer_add(0.25, window=context.window)
        window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        if event.type != 'TIMER':
            return {'PASS_THROUGH'}
        message, done, error, path = self._progress.read()
        context.workspace.status_text_set(message)
        if not done:
            return {'RUNNING_MODAL'}
        context.window_manager.event_timer_remove(self._timer)
        context.workspace.status_text_set(None)
        for area in context.screen.areas:
            area.tag_redraw()
        return self._settle(context, error, path)
