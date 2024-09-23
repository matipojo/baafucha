"""
Created by: Ori Halevi
GitHub: https://github.com/ori-halevi

Description: This script toggles the ColorPrevalence setting in the Windows registry when a keyboard language change
is detected, and refreshes the taskbar to apply the change and thus causes the color of the taskbar to change when
the language changes.
"""

import platform
from core.tray import load_config

class Taskbar:
    def start_language_monitor(self):
        raise NotImplementedError

    def stop_language_monitor(self):
        raise NotImplementedError

    def on_config_change(self, new_config):
        raise NotImplementedError

if platform.system() == "Windows":
    import ctypes
    import threading
    import time
    import winreg

    class WindowsTaskbar(Taskbar):
        def __init__(self):
            self.user32 = ctypes.windll.user32
            self.kernel32 = ctypes.windll.kernel32
            self.taskbar_handle = self.user32.FindWindowW("Shell_TrayWnd", None)
            self.WM_SETTINGCHANGE = 0x001A
            self.REGISTRY_PATH = r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
            self.VALUE_NAME = "ColorPrevalence"
            self.language_monitor_thread = None
            self.language_monitor_stop_event = None

        def get_set_color_prevalence(self, set_value=None):
            try:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.REGISTRY_PATH, 0, winreg.KEY_READ | winreg.KEY_WRITE) as key:
                    if set_value is None:
                        value, _ = winreg.QueryValueEx(key, self.VALUE_NAME)
                        return value
                    else:
                        winreg.SetValueEx(key, self.VALUE_NAME, 0, winreg.REG_DWORD, set_value)
                        return set_value
            except Exception as e:
                print(f"An error occurred with ColorPrevalence: {e}")
                return None

        def refresh_taskbar(self):
            self.user32.SendMessageW(self.taskbar_handle, self.WM_SETTINGCHANGE, 0, "ImmersiveColorSet")

        def set_color_prevalence(self, value):
            self.get_set_color_prevalence(value)
            self.refresh_taskbar()

        def get_current_input_language(self):
            hwnd = self.user32.GetForegroundWindow()
            thread_id = self.user32.GetWindowThreadProcessId(hwnd, 0)
            layout_id = self.user32.GetKeyboardLayout(thread_id)
            language_id = layout_id & 0xFFFF
            return language_id

        def start_language_monitor(self):
            config = load_config()
            if config.get("taskbar_color", False):
                self.language_monitor_stop_event = threading.Event()
                self.language_monitor_thread = threading.Thread(target=self.monitor_language, args=(self.language_monitor_stop_event,))
                self.language_monitor_thread.start()

        def stop_language_monitor(self):
            if self.language_monitor_thread:
                self.set_color_prevalence(0)
                self.language_monitor_stop_event.set()
                self.language_monitor_thread.join()
                self.language_monitor_thread = None
                self.language_monitor_stop_event.clear()

        def on_config_change(self, new_config):
            self.stop_language_monitor()
            if new_config.get("taskbar_color", False):
                if not self.language_monitor_thread:
                    self.start_language_monitor()

        def monitor_language(self, stop_event):
            last_layout_id = self.get_current_input_language()
            new_value = 0 if last_layout_id == self.kernel32.GetUserDefaultUILanguage() else 1
            self.set_color_prevalence(new_value)
            while not stop_event.is_set():
                layout_id = self.get_current_input_language()
                if layout_id != last_layout_id:
                    last_layout_id = layout_id
                    if layout_id == self.kernel32.GetUserDefaultUILanguage():
                        self.set_color_prevalence(0)
                    else:
                        self.set_color_prevalence(1)
                    print("Language change detected to language ID:", layout_id)
                time.sleep(0.2)

elif platform.system() == "Darwin":
    import subprocess

    class MacTaskbar(Taskbar):
        def start_language_monitor(self):
            pass  # Implement Mac-specific logic if needed

        def stop_language_monitor(self):
            pass  # Implement Mac-specific logic if needed

        def on_config_change(self, new_config):
            pass  # Implement Mac-specific logic if needed

def get_taskbar():
    if platform.system() == "Windows":
        return WindowsTaskbar()
    elif platform.system() == "Darwin":
        return MacTaskbar()
    else:
        raise NotImplementedError("Unsupported platform")

taskbar = get_taskbar()

def start_language_monitor():
    taskbar.start_language_monitor()

def stop_language_monitor():
    taskbar.stop_language_monitor()

def on_config_change(new_config):
    taskbar.on_config_change(new_config)
