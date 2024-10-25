import keyboard
import pyperclip
from pynput import keyboard as pynput_keyboard
import time
from PIL import Image
import threading
import os
from core.tray import SystemTrayApp
from core.taskbar import start_language_monitor
from core.taskbar import stop_language_monitor
from core.taskbar import on_config_change
import platform

# Determine the modifier key based on the operating system
MODIFIER_KEY = pynput_keyboard.Key.ctrl if platform.system() == "Windows" else pynput_keyboard.Key.cmd

# Keyboard mapping for English to Hebrew and vice versa
en_to_he = {
    'q': '/', 'w': "'", 'e': 'ק', 'r': 'ר', 't': 'א', 'y': 'ט', 'u': 'ו', 'i': 'ן', 'o': 'ם', 'p': 'פ',
    'a': 'ש', 's': 'ד', 'd': 'ג', 'f': 'כ', 'g': 'ע', 'h': 'י', 'j': 'ח', 'k': 'ל', 'l': 'ך',
    'z': 'ז', 'x': 'ס', 'c': 'ב', 'v': 'ה', 'b': 'נ', 'n': 'מ', 'm': 'צ',
    ',': 'ת', '.': 'ץ', ';': 'ף'
}
he_to_en = {v: k for k, v in en_to_he.items()}

def is_hebrew(text):
    """Check if the text contains Hebrew characters."""
    return any('\u0590' <= c <= '\u05FF' for c in text)

def convert_text(text, mapping):
    """Convert text using the provided mapping."""
    return ''.join(mapping.get(char.lower(), char) for char in text)

def auto_convert(select_all=False):
    """Automatically detect and convert text between English and Hebrew."""
    # Save original clipboard content
    original_clipboard = pyperclip.paste()

    if select_all:
        keyboard_controller.press(MODIFIER_KEY)
        keyboard_controller.press('a')
        keyboard_controller.release('a')
        keyboard_controller.release(MODIFIER_KEY)
        time.sleep(0.1)

    # Try to copy selected text
    keyboard_controller.press(MODIFIER_KEY)
    keyboard_controller.press('c')
    keyboard_controller.release('c')
    keyboard_controller.release(MODIFIER_KEY)
    time.sleep(0.1)
    selected_text = pyperclip.paste()

    # Check if text was selected
    text_was_selected = selected_text != original_clipboard

    # If no text was selected and select_all is False, do nothing
    if not text_was_selected and not select_all:
        pyperclip.copy(original_clipboard)
        return

    # Choose appropriate mapping based on text language
    if is_hebrew(selected_text):
        converted_text = convert_text(selected_text, he_to_en)
    else:
        converted_text = convert_text(selected_text, en_to_he)

    # Copy converted text to clipboard and paste
    pyperclip.copy(converted_text)
    keyboard_controller.press(MODIFIER_KEY)
    keyboard_controller.press('v')
    keyboard_controller.release('v')
    keyboard_controller.release(MODIFIER_KEY)

    # Restore original clipboard content
    time.sleep(0.1)
    pyperclip.copy(original_clipboard)

def on_key_press(key):
    """Handle key press events."""
    try:
        if key == pynput_keyboard.Key.f8:
            # Check if shift is pressed
            if keyboard.is_pressed('control'):
                auto_convert(select_all=True)
            else:
                auto_convert(select_all=False)
    except AttributeError:
        pass

# Create keyboard listener
listener = pynput_keyboard.Listener(on_press=on_key_press)
keyboard_controller = pynput_keyboard.Controller()

def stop_listener():
    """Stop the keyboard listener."""
    listener.stop()
    stop_language_monitor()

if __name__ == "__main__":
    # Start keyboard listener in a separate thread
    listener_thread = threading.Thread(target=listener.run)
    listener_thread.start()

    print("Baafucha is running.")
    print("Press F8 to convert selected text between English and Hebrew.")
    print("Press Ctrl+F8 to select all text and convert it.")

    start_language_monitor()
    
    # Run system tray icon
    tray = SystemTrayApp(stop_listener, config_callback=on_config_change)
    tray.run()
