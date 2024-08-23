import sys
import os
import winreg
import pystray
from PIL import Image
import json

APP_NAME = "Baafucha"
CONFIG_DIR = os.path.join(os.path.expanduser('~'), '.baafucha')
CONFIG_FILE = os.path.join(CONFIG_DIR, 'config.json')

def get_startup_key():
    return winreg.OpenKey(
        winreg.HKEY_CURRENT_USER,
        r"Software\Microsoft\Windows\CurrentVersion\Run",
        0,
        winreg.KEY_ALL_ACCESS
    )

def is_startup_enabled():
    try:
        with get_startup_key() as key:
            winreg.QueryValueEx(key, APP_NAME)
        return True
    except WindowsError:
        return False

def load_config():
    if not os.path.exists(CONFIG_DIR):
        os.makedirs(CONFIG_DIR)
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print(f"Error reading config file. Using default settings.")
    return {"load_on_startup": True}  # Default to True if no config file exists

def toggle_taskbar_color_config(icon, item):
    config = load_config()
    config["taskbar_color"] = not config.get("taskbar_color", False)
    save_config(config)
    icon.update_menu()
    icon.config_callback(config)

def is_taskbar_color_enabled():
   config = load_config()
   return config.get("taskbar_color", False)

def save_config(config):
    if not os.path.exists(CONFIG_DIR):
        os.makedirs(CONFIG_DIR)
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f)

def enable_startup():
    try:
        with get_startup_key() as key:
            app_path = sys.executable
            winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, app_path)
    except WindowsError as e:
        print(f"Error enabling startup: {e}")

def disable_startup():
    try:
        with get_startup_key() as key:
            winreg.DeleteValue(key, APP_NAME)
    except WindowsError as e:
        print(f"Error disabling startup: {e}")

def toggle_startup(icon, item):
    config = load_config()
    if is_startup_enabled():
        disable_startup()
        config["load_on_startup"] = False
    else:
        enable_startup()
        config["load_on_startup"] = True
    save_config(config)
    icon.update_menu()

def on_quit(icon, stop_listener_func):
    stop_listener_func()
    icon.stop()

class SystemTrayApp:
    def __init__(self, stop_listener_func, config_callback):
        self.icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', 'icon.png')
        
        self.menu = pystray.Menu(
            pystray.MenuItem('Change taskbar color', toggle_taskbar_color_config, checked=lambda _: is_taskbar_color_enabled()),
            pystray.MenuItem('Load on startup', toggle_startup, checked=lambda _: is_startup_enabled()),
            pystray.MenuItem('Quit', lambda: on_quit(self.icon, stop_listener_func))
        )

        self.icon = pystray.Icon(
            APP_NAME,
            Image.open(self.icon_path),
            f"{APP_NAME} - Keyboard Layout Converter",
            self.menu
        )

        self.icon.config_callback = config_callback

        # Load config and set startup according to saved preference
        config = load_config()
        if config["load_on_startup"] and not is_startup_enabled():
            enable_startup()
        elif not config["load_on_startup"] and is_startup_enabled():
            disable_startup()

    def run(self):
        self.icon.run()
