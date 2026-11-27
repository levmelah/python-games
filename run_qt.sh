#!/usr/bin/env bash
# Run a PyQt app from the VS Code (snap) terminal without the GLib/GTK crash.
# The snap injects GSETTINGS_SCHEMA_DIR / GTK_* / GIO_* pointing at its own
# bundled schemas, which makes Qt abort with:
#   GLib-GIO-ERROR: Settings schema '...xsettings' does not contain a key named 'antialiasing'
# Stripping those vars makes Qt use the system schemas again.
#
# Usage: ./run_qt.sh ארקנוייד_מיוחד.py
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec env -u GSETTINGS_SCHEMA_DIR -u GIO_MODULE_DIR -u GTK_PATH -u GTK_EXE_PREFIX \
         -u GDK_PIXBUF_MODULE_FILE -u GDK_PIXBUF_MODULEDIR -u GTK_IM_MODULE_FILE \
         -u LOCPATH -u SNAP -u SNAP_NAME -u XDG_DATA_DIRS \
    "$HERE/.venv-bpy/bin/python" "$@"
