"""
Created by: Ori Halevi
GitHub: https://github.com/ori-halevi

Description: This script toggles the ColorPrevalence setting in the Windows registry when a keyboard language change
is detected, and refreshes the taskbar to apply the change and thus causes the color of the taskbar to change when
the language changes.
"""

import ctypes
import multiprocessing
import time
import threading
import platform
from core.tray import load_config

if platform.system() == "Windows":
    import winreg
    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32
    taskbar_handle = user32.FindWindowW("Shell_TrayWnd", None)
    WM_SETTINGCHANGE = 0x001A
    REGISTRY_PATH = r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
    VALUE_NAME = "ColorPrevalence"
elif platform.system() == "Darwin":
    from AppKit import NSApp, NSApplicationActivationPolicyRegular
    from Foundation import NSUserDefaults

def get_set_color_prevalence(set_value=None):
    """
    Gets or sets the ColorPrevalence value in the registry.
    If set_value is None, it returns the current value.
    If set_value is provided, it sets the new value and returns it.
    """
    if platform.system() == "Windows":
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REGISTRY_PATH, 0, winreg.KEY_READ | winreg.KEY_WRITE) as key:
                if set_value is None:
                    value, _ = winreg.QueryValueEx(key, VALUE_NAME)
                    return value
                else:
                    winreg.SetValueEx(key, VALUE_NAME, 0, winreg.REG_DWORD, set_value)
                    return set_value
        except Exception as e:
            print(f"An error occurred with ColorPrevalence: {e}")
            return None
    elif platform.system() == "Darwin":
        defaults = NSUserDefaults.standardUserDefaults()
        if set_value is None:
            return defaults.integerForKey("AppleInterfaceStyleSwitchesAutomatically")
        else:
            defaults.setInteger_forKey_(set_value, "AppleInterfaceStyleSwitchesAutomatically")
            return set_value

def refresh_taskbar():
    """
    Refreshes the taskbar by sending a settings change notification to the taskbar.
    """
    if platform.system() == "Windows":
        user32.SendMessageW(taskbar_handle, WM_SETTINGCHANGE, 0, "ImmersiveColorSet")
    elif platform.system() == "Darwin":
        app = NSApp()
        app.setActivationPolicy_(NSApplicationActivationPolicyRegular)
        app.activateIgnoringOtherApps_(True)

def set_color_prevalence(value):
    """
    Sets the ColorPrevalence value in the registry and refreshes the taskbar.
    """
    get_set_color_prevalence(value)
    refresh_taskbar()

def get_current_input_language():
    if platform.system() == "Windows":
        hwnd = user32.GetForegroundWindow()
        thread_id = user32.GetWindowThreadProcessId(hwnd, 0)
        layout_id = user32.GetKeyboardLayout(thread_id)
        language_id = layout_id & 0xFFFF
        return language_id
    elif platform.system() == "Darwin":
        return NSUserDefaults.standardUserDefaults().stringForKey_("AppleLanguages")[0]

language_monitor_thread = None
language_monitor_stop_event = None

def start_language_monitor():
    config = load_config()

    if config.get("taskbar_color", False):
        global language_monitor_thread
        global language_monitor_stop_event

        language_monitor_stop_event = threading.Event()
        language_monitor_thread = threading.Thread(target=monitor_language, args=(language_monitor_stop_event,))
        language_monitor_thread.start()

def stop_language_monitor():
    global language_monitor_thread
    if language_monitor_thread:
        global language_monitor_stop_event

        set_color_prevalence(0)

        language_monitor_stop_event.set()
        language_monitor_thread.join()
        language_monitor_thread = None
        language_monitor_stop_event.clear()

def on_config_change(new_config):
    stop_language_monitor()
    if new_config.get("taskbar_color", False):
        if not language_monitor_thread:
            start_language_monitor()

def monitor_language(stop_event):
    last_layout_id = get_current_input_language()
    new_value = 0 if last_layout_id == kernel32.GetUserDefaultUILanguage() else 1
    set_color_prevalence(new_value)

    while not stop_event.is_set():
        layout_id = get_current_input_language()
        if layout_id != last_layout_id:
            last_layout_id = layout_id
            if layout_id == kernel32.GetUserDefaultUILanguage():
                set_color_prevalence(0)
            else:
                set_color_prevalence(1)
            print("Language change detected to language ID:", layout_id)
        time.sleep(0.2)

if __name__ == "__main__":
    main()
