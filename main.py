import os
import json
from groq import Groq
from dotenv import load_dotenv
from audio_engine import speak, take_command, wait_for_wake_word
import web_ops
import os_ops

load_dotenv()

# ==========================================
# SECTION 1: CONFIGURATION & MEMORY SETUP
# ==========================================
GROQ_API_KEY = os.getenv("MY_API_KEY")

if not GROQ_API_KEY:
    print("CRITICAL ERROR: API Key not found! Please check your .env file.")
    exit()

client = Groq(api_key=GROQ_API_KEY)
MEMORY_FILE = "chat_memory.txt"


def update_memory(user_msg, ai_msg):
    """Saves chat history to maintain conversation context."""
    with open(MEMORY_FILE, "a", encoding="utf-8") as f:
        f.write(f"User: {user_msg}\n")
        f.write(f"Jarvis: {ai_msg}\n")


def get_memory():
    """Retrieves the last 4 interactions for context."""
    try:
        if not os.path.exists(MEMORY_FILE):
            return "No previous memory."
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()
            return "".join(lines[-4:])
    except Exception:
        return "No previous memory."


# ==========================================
# SECTION 2: AI TOOLS SCHEMA
# ==========================================
jarvis_tools = [
    {
        "type": "function",
        "function": {
            "name": "empty_recycle_bin",
            "description": "Empties the Windows recycle bin.",
        },
    },
    {
        "type": "function",
        "function": {
            "name": "explain_screen",
            "description": "Takes a screenshot of the user's current screen and explains what is visible using AI Vision.",
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_active_window",
            "description": "Reads the text from the currently opened document, website, or file on the screen.",
        },
    },
    {
        "type": "function",
        "function": {
            "name": "control_system_hardware",
            "description": "Controls system volume, brightness, or opens settings.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": [
                            "volume_up",
                            "volume_down",
                            "mute",
                            "brightness",
                            "open_settings",
                        ],
                    },
                    "level": {
                        "type": "integer",
                        "description": "Brightness level (0-100). Required if action is brightness.",
                    },
                },
                "required": ["action"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_system_file",
            "description": "Searches for and deletes a specified file from the system.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_name": {
                        "type": "string",
                        "description": "Name of the file to delete",
                    }
                },
                "required": ["file_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "edit_word_doc",
            "description": "Edits an existing Word document by adding new AI-generated content to it.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_name": {
                        "type": "string",
                        "description": "The name of the existing word document",
                    },
                    "new_instruction": {
                        "type": "string",
                        "description": "What new content should be added to the document",
                    },
                },
                "required": ["file_name", "new_instruction"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_word_doc",
            "description": "Generates an academic assignment on a topic and saves it as a Word document.",
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {
                        "type": "string",
                        "description": "The topic of the assignment",
                    },
                    "filename": {
                        "type": "string",
                        "description": "The name of the file to save",
                    },
                },
                "required": ["topic", "filename"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file_content",
            "description": "Searches for a text or word document by name and reads its text content aloud.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_name": {
                        "type": "string",
                        "description": "The name of the file to search and read",
                    }
                },
                "required": ["file_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "send_whatsapp_message",
            "description": "Sends a WhatsApp message to a target.",
            "parameters": {
                "type": "object",
                "properties": {
                    "target": {
                        "type": "string",
                        "description": "Phone number or contact name",
                    },
                    "message": {"type": "string", "description": "The message body"},
                    "is_group": {
                        "type": "boolean",
                        "description": "True if sending to a group",
                    },
                },
                "required": ["target", "message"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "play_youtube_song",
            "description": "Plays a specific song or video on YouTube.",
            "parameters": {
                "type": "object",
                "properties": {
                    "song_name": {
                        "type": "string",
                        "description": "The name of the song to play",
                    }
                },
                "required": ["song_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "open_application",
            "description": "Opens an application installed on the PC.",
            "parameters": {
                "type": "object",
                "properties": {
                    "app_name": {
                        "type": "string",
                        "description": "Name of the application to open",
                    }
                },
                "required": ["app_name"],
            },
        },
    },
]


# ==========================================
# SECTION 3: THE AUTONOMOUS BRAIN (AGENTIC AI)
# ==========================================
def chat_with_jarvis_cloud(prompt):
    """Handles LLM interactions and tool execution."""
    print("Processing request...")
    try:
        past_context = get_memory()

        response = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": f"""You are Jarvis, a highly advanced, professional AI assistant.
                    Strict Rules:
                    1. Reply STRICTLY in proper, natural English.
                    2. Keep responses highly concise (strictly 1 or 2 sentences).
                    3. Maintain a professional tone (use 'Sir').
                    4. NEVER use emojis or markdown formatting.
                    5. If the user asks you to perform a system action, USE THE PROVIDED TOOLS.
                    Context:\n{past_context}""",
                },
                {"role": "user", "content": prompt},
            ],
            model="llama-3.1-8b-instant",
            tools=jarvis_tools,
            tool_choice="auto",
        )

        message = response.choices[0].message
        ai_reply_text = ""

        if message.tool_calls:
            for tool_call in message.tool_calls:
                func_name = tool_call.function.name
                args = json.loads(tool_call.function.arguments)

                res = "Action completed."

                if func_name == "empty_recycle_bin":
                    res = os_ops.empty_recycle_bin()
                elif func_name == "control_system_hardware":
                    res = os_ops.control_system_hardware(
                        args.get("action"), args.get("level")
                    )
                elif func_name == "create_word_doc":
                    res = os_ops.create_word_doc(
                        args.get("topic"), args.get("filename"), client
                    )
                elif func_name == "send_whatsapp_message":
                    res = web_ops.send_whatsapp_message(
                        args.get("target"),
                        args.get("message"),
                        args.get("is_group", False),
                    )
                elif func_name == "open_application":
                    res = os_ops.open_application(args.get("app_name"))
                elif func_name == "play_youtube_song":
                    res = web_ops.play_youtube_song(args.get("song_name"))
                elif func_name == "read_file_content":
                    res = os_ops.read_file_content(args.get("file_name"))
                elif func_name == "delete_system_file":
                    res = os_ops.delete_system_file(args.get("file_name"))
                elif func_name == "edit_word_doc":
                    res = os_ops.edit_word_doc(
                        args.get("file_name"), args.get("new_instruction"), client
                    )
                elif func_name == "explain_screen":
                    speak("Accessing optics. Let me analyze your screen, Sir.")
                    base64_img = os_ops.capture_screen_for_vision()
                    if base64_img:
                        vision_response = client.chat.completions.create(
                            model="llama-3.2-11b-vision-preview",
                            messages=[
                                {
                                    "role": "user",
                                    "content": [
                                        {
                                            "type": "text",
                                            "text": "Briefly and professionally explain what is happening on this screen in 2 sentences.",
                                        },
                                        {
                                            "type": "image_url",
                                            "image_url": {
                                                "url": f"data:image/jpeg;base64,{base64_img}"
                                            },
                                        },
                                    ],
                                }
                            ],
                            max_tokens=150,
                        )
                        res = vision_response.choices[0].message.content
                    else:
                        res = "I am unable to capture the screen at this moment."
                elif func_name == "read_active_window":
                    res = os_ops.read_active_window()

                speak(res)
                ai_reply_text = res

        else:
            ai_reply = message.content
            clean_reply = (
                ai_reply.replace("*", "")
                .replace("#", "")
                .encode("ascii", "ignore")
                .decode("ascii")
            )
            speak(clean_reply.strip())
            ai_reply_text = clean_reply.strip()

        update_memory(prompt, ai_reply_text)

    except Exception as e:
        print(f"Cloud Error: {e}")
        speak("Sir, I am currently facing a server connection issue.")


# ==========================================
# SECTION 4: MAIN APPLICATION LOOP
# ==========================================
if __name__ == "__main__":
    speak("System diagnostics complete. I am online and listening, Sir.")

    current_mode = "voice"
    is_awake = False

    while True:
        if current_mode == "voice":
            if not is_awake:
                wake_status = wait_for_wake_word()
                if wake_status:
                    speak("Yes sir, I am listening.")
                    is_awake = True

            if is_awake:
                query = take_command()

                if query == "none" or query.strip() == "":
                    speak("Going to standby mode, Sir.")
                    is_awake = False
                    continue

                if "text mode" in query or "enable text mode" in query:
                    speak("Switching to text input mode.")
                    current_mode = "text"
                    is_awake = False
                    continue

                if "sleep" in query or "exit" in query or "quit" in query:
                    speak("Powering down the systems. Best of luck, Sir.")
                    break

                chat_with_jarvis_cloud(query)

        elif current_mode == "text":
            print("\n" + "=" * 50)
            print("⌨️  TEXT MODE ACTIVE (Type 'voice mode' to switch back to Mic)")
            user_text = input("Jarvis >> ")
            query = user_text.lower()

            if query.strip() == "voice mode":
                speak("Switching back to voice mode.")
                current_mode = "voice"
                continue

            if query == "none" or query.strip() == "":
                continue
            if "sleep" in query or "exit" in query or "quit" in query:
                speak("Powering down the systems.")
                break

            chat_with_jarvis_cloud(query)
