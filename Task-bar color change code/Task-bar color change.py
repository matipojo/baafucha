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

# Loading the library user32.dll
user32 = ctypes.windll.user32

# Gets the handle of the taskbar
taskbar_handle = user32.FindWindowW("Shell_TrayWnd", None)

# Setting constants
WM_SETTINGCHANGE = 0x001A

def toggle_color_prevalence():
    """
    Changes the ColorPrevalence value in the system registry to turn the color on the taskbar on or off.
    """
    registry_path = r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
    value_name = "ColorPrevalence"

    try:
        # Opens the registry key
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, registry_path, 0, winreg.KEY_READ | winreg.KEY_WRITE) as key:
            # reads the current value
            current_value = winreg.QueryValueEx(key, value_name)[0]

            # Changes the current value to the opposite value
            new_value = 0 if current_value == 1 else 1

            # Sets the new value
            winreg.SetValueEx(key, value_name, 0, winreg.REG_DWORD, new_value)

            print(f"Changed ColorPrevalence from {current_value} to {new_value}")
    except FileNotFoundError:
        print("Registry path or value not found.")
    except Exception as e:
        print(f"An error occurred: {e}")

def refresh_taskbar():
    """
    Refreshes the taskbar by sending a settings change notification to the taskbar.
    """
    user32.SendMessageW(taskbar_handle, WM_SETTINGCHANGE, 0, "ImmersiveColorSet")

def get_current_input_language():
    """
    Gets the current keyboard layout code.
    """
    layout_id = ctypes.windll.user32.GetKeyboardLayout(0)
    return layout_id

def worker(queue):
    """
    A separate process that gets the current keyboard layout code and sends it to a queue.
    """
    layout_id = get_current_input_language()
    queue.put(layout_id)  # Sends the result back to the main process

def get_keyboard_layout_process():
    """
    Runs a separate process to get the current keyboard layout code and returns the result.
    """
    # Creates a queue for communication between processes
    queue = multiprocessing.Queue()

    # Activates a new process to receive the language
    process = multiprocessing.Process(target=worker, args=(queue,))
    process.start()

    # Waiting for the end of the process and receiving the result
    process.join()

    return queue.get()

# The main process of the program
def main():
    # Stores the last language ID
    last_layout_id = get_keyboard_layout_process()

    # Main loop to check language changes
    while True:
        layout_id = get_keyboard_layout_process()

        # If a language change is detected, changes the color value and refreshes the taskbar
        if layout_id != last_layout_id:
            last_layout_id = layout_id
            toggle_color_prevalence()
            refresh_taskbar()
            print("Language change detected")

        # Waits 0.2 seconds before next test
        time.sleep(0.2)

# Running the main program
if __name__ == "__main__":
    main()
