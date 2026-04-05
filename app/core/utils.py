import os
import sys

def get_resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        # Use the directory of this file as the base, then go up to the project root
        # utils.py is in app/core/, so project root is two levels up
        base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    return os.path.normpath(os.path.join(base_path, relative_path))

def get_asset_path(filename):
    """ Standardized helper for assets """
    return get_resource_path(os.path.join("assets", filename))

def get_legal_path(filename):
    """ Standardized helper for legal docs """
    return get_resource_path(os.path.join("legal", filename))
