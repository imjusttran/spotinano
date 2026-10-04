"""Keep Qt's bundled ICU libraries ahead of Windows' system ICU."""

import os
import sys


if sys.platform == "win32":
    _PYSIDE_DIR = os.path.join(sys._MEIPASS, "PySide6")
    _PYSIDE_DLL_DIRECTORY = os.add_dll_directory(_PYSIDE_DIR)
    os.environ["PATH"] = _PYSIDE_DIR + os.pathsep + os.environ.get("PATH", "")
