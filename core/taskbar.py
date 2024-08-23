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
import winreg
import threading
from core.tray import load_config

# Loading the library user32.dll
user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

# Gets the handle of the taskbar
taskbar_handle = user32.FindWindowW("Shell_TrayWnd", None)

# Setting constants
WM_SETTINGCHANGE = 0x001A

import winreg

REGISTRY_PATH = r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
VALUE_NAME = "ColorPrevalence"

def get_set_color_prevalence(set_value=None):
    """
    Gets or sets the ColorPrevalence value in the registry.
    If set_value is None, it returns the current value.
    If set_value is provided, it sets the new value and returns it.
    """

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

def refresh_taskbar():
    """
    Refreshes the taskbar by sending a settings change notification to the taskbar.
    """
    user32.SendMessageW(taskbar_handle, WM_SETTINGCHANGE, 0, "ImmersiveColorSet")

def set_color_prevalence(value):
    """
    Sets the ColorPrevalence value in the registry and refreshes the taskbar.
    """
    get_set_color_prevalence(value)
    refresh_taskbar()

def get_current_input_language():
    # Get the foreground window
    hwnd = user32.GetForegroundWindow()

    # Get the thread of the foreground window
    thread_id = user32.GetWindowThreadProcessId(hwnd, 0)

    # Get the keyboard layout of the thread
    layout_id = user32.GetKeyboardLayout(thread_id)

    # Extract the language ID from the keyboard layout
    language_id = layout_id & 0xFFFF

    return language_id

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

# The main process of the program
def monitor_language(stop_event):
    # Stores the last language ID
    last_layout_id = get_current_input_language()

    # Set the initial color value
    new_value = 0 if last_layout_id == kernel32.GetUserDefaultUILanguage() else 1
    set_color_prevalence( new_value )

    # Main loop to check language changes
    while not stop_event.is_set():
        layout_id = get_current_input_language()

        # If a language change is detected, changes the color value and refreshes the taskbar
        if layout_id != last_layout_id:
            last_layout_id = layout_id

            if layout_id == kernel32.GetUserDefaultUILanguage():
                set_color_prevalence(0)
            else:
                set_color_prevalence(1)
            print("Language change detected to language ID:", layout_id)

        # Waits 0.2 seconds before next test
        time.sleep(0.2)

# Running the main program
if __name__ == "__main__":
    main()
