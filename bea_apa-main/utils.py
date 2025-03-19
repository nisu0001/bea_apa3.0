import os
import sys

def resource_path(relative_path):
    """
    Get absolute path to resource, works for development and for PyInstaller EXEs.
    """
    if getattr(sys, 'frozen', False):
        # Running as a bundled executable (PyInstaller)
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)
