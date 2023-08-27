import pyWinhook as pyHook
import pythoncom
import requests
import pyautogui

current_input = ""


def on_keyboard_event(event):
    global current_input

    if event.Ascii > 0 and "Return" not in event.Key:
        current_input += chr(event.Ascii)
    elif event.Key == "Return":
        if current_input.startswith("SCAN;"):
            uuid_value = current_input[5:]
            response = requests.post(
                f'http://192.168.0.106:5000/scan_qr/{uuid_value}')
            print(response.json())
        current_input = ""
    return True


hook_manager = pyHook.HookManager()
hook_manager.KeyDown = on_keyboard_event
hook_manager.HookKeyboard()

pyautogui.hotkey('alt', 'shift')

pythoncom.PumpMessages()
