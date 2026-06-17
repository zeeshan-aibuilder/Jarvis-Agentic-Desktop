import speech_recognition as sr
import edge_tts
import asyncio
import pygame
import os

pygame.mixer.init()


def speak(text):
    print(f"Jarvis: {text}")
    try:
        communicate = edge_tts.Communicate(text, "en-GB-RyanNeural")
        asyncio.run(communicate.save("response.mp3"))
        pygame.mixer.music.load("response.mp3")
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
        pygame.mixer.music.unload()
        os.remove("response.mp3")
    except Exception as e:
        print(f"Audio Error: {e}")


def take_command():
    """Active Command Mic"""
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("\n[🎙️ Listening for command...]")
        r.pause_threshold = 1.2
        r.adjust_for_ambient_noise(source, duration=0.5)
        try:
            audio = r.listen(source, timeout=5, phrase_time_limit=10)
        except sr.WaitTimeoutError:
            return "none"

    try:
        print("Recognizing...")
        query = r.recognize_google(audio, language="en-US")
        print(f"You said: {query}\n")
    except Exception:
        return "none"
    return query.lower()


def wait_for_wake_word():
    """Background Sleep Mode - Optimized for continuous listening"""
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("\n[💤 Sleeping... Say 'Jarvis' to wake me up]")
        r.pause_threshold = 0.5  # Saans lene ka gap kam kar diya taake foran react kare
        r.adjust_for_ambient_noise(source, duration=0.5)

        while True:
            try:
                # timeout=None kar diya taake mic baar baar cut na ho
                audio = r.listen(source, timeout=None, phrase_time_limit=3)
                query = r.recognize_google(audio, language="en-US").lower()

                # Google aksar desi accent mein spelling mistake karta hai, humne sab options daal diye
                wake_words = ["jarvis", "javis", "travis", "service", "charles"]

                if any(word in query for word in wake_words):
                    return True
            except Exception:
                continue
