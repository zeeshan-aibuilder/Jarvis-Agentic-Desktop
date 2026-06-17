import os
import time
import urllib.parse
import pyautogui
import pywhatkit
import webbrowser


def send_whatsapp_message(target, message, is_group=False):
    """Sends a WhatsApp message using Desktop URI or UI Automation."""
    try:
        target_str = str(target).strip()
        is_number = any(char.isdigit() for char in target_str)

        if is_number:
            target_str = target_str.replace(" ", "")
            if target_str.startswith("03") and len(target_str) == 11:
                target_str = "+92" + target_str[1:]
            elif not target_str.startswith("+"):
                target_str = "+92" + target_str

            encoded_message = urllib.parse.quote(message)
            os.system(
                f'start "" "whatsapp://send?phone={target_str}&text={encoded_message}"'
            )

            # Generous timing to allow Windows OS to launch the app properly
            time.sleep(8)
            pyautogui.press("enter")
            time.sleep(1)
            pyautogui.press("enter")

            return f"Message dispatched to number {target_str}."

        else:
            os.system("start whatsapp:")

            # Wait for app to launch
            time.sleep(6)

            # Focus search bar
            pyautogui.hotkey("ctrl", "f")
            time.sleep(2)

            # Type contact name
            pyautogui.write(target_str)
            time.sleep(3)

            # Select contact
            pyautogui.press("enter")
            time.sleep(2)

            # Type and send message
            pyautogui.write(message)
            time.sleep(1)
            pyautogui.press("enter")

            return f"Message dispatched successfully to {target_str}."

    except Exception as e:
        return f"Failed to send message: {e}"


def play_youtube_song(song_name):
    """Searches and plays a specific song or video on YouTube."""
    try:
        pywhatkit.playonyt(song_name)
        return f"Playing {song_name} on YouTube, sir."
    except Exception as e:
        return f"Could not play the song: {e}"
