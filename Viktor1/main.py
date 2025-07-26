import pyttsx3
import ollama
import json
import os
import re
from datetime import datetime, timedelta
import pytz

# User Info
USER_NAME = "Vida"
MEMORY_FILE = os.path.join("memory", "vida.json")

# 📦 Load & Save Memory
def load_memory():
    if not os.path.exists(MEMORY_FILE):
        return {}
    with open(MEMORY_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_memory(memory):
    os.makedirs(os.path.dirname(MEMORY_FILE), exist_ok=True)
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(memory, f, ensure_ascii=False, indent=2)

memory = load_memory()

# 🔊 Initialize TTS
tts_engine = pyttsx3.init()
voices = tts_engine.getProperty('voices')
voice = next((v for v in voices if "David" in v.name), voices[0])
tts_engine.setProperty('voice', voice.id)
tts_engine.setProperty('rate', 155)
tts_engine.setProperty('volume', 1.0)

# ➡️ Remove Emojis from Text
def remove_emojis(text):
    emoji_pattern = re.compile(
        "[" 
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F700-\U0001F77F"  # alchemical symbols
        "\U0001F780-\U0001F7FF"  # Geometric Shapes Extended
        "\U0001F800-\U0001F8FF"  # Supplemental Arrows-C
        "\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
        "\U0001FA00-\U0001FA6F"  # Chess Symbols
        "\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
        "\U00002702-\U000027B0"  # Dingbats
        "\U000024C2-\U0001F251"
        "]+", flags=re.UNICODE)
    return emoji_pattern.sub(r'', text)

def speak(text):
    try:
        clean_text = remove_emojis(text)
        tts_engine.say(clean_text)
        tts_engine.runAndWait()
    except Exception as e:
        print(f"⚠️ Unable to speak: {e}")

# 🕒 Tehran Local Time
def get_tehran_time():
    tehran = pytz.timezone("Asia/Tehran")
    now = datetime.now(tehran)
    return now.strftime("%A, %d %B %Y - %H:%M")

# 🧠 Format Memory for Prompt
def build_memory_context(mem):
    if not mem:
        return "No personal information stored yet."
    labels = {
        "name": "Name", "birthday": "Birthday", "favorite_color": "Favorite Color",
        "twin_sister": "Twin Sister", "older_sister": "Older Sister",
        "goal": "Goal", "code": "Secret Code", "about_me": "About Me",
        "likes": "Likes", "hobbies": "Hobbies", "last_emotion": "Last Emotion",
        "emotion_trend": "Emotion Trend"
    }
    return "\n".join(f"{labels.get(k, k.replace('_', ' ').capitalize())}: {v}" for k, v in mem.items())

# 🧠 Learn from Vida's Input
def update_memory_from_input(user_input):
    patterns = [
        (r"^(?:i am|i'm) (.+)$", "about_me"),
        (r"^i like (.+)$", "likes"),
        (r"^i play (.+)$", "hobbies"),
        (r"^my ([a-zA-Z_ ]+) is (.+)$", None),
    ]
    updated = False
    for pattern, key_name in patterns:
        match = re.match(pattern, user_input.lower())
        if match:
            if key_name:
                value = match.group(1).strip()
                if key_name in memory and value not in memory[key_name]:
                    memory[key_name] += f", {value}"
                else:
                    memory[key_name] = value
            else:
                key = match.group(1).strip().replace(" ", "_")
                value = match.group(2).strip()
                memory[key] = value
            updated = True

    # 🔍 Detect Emotion
    emotion = detect_emotion(user_input)
    if emotion:
        memory['last_emotion'] = emotion
        trend = memory.get("emotion_trend", "")
        memory["emotion_trend"] = f"{trend}, {emotion}".strip(', ')
        updated = True

    if updated:
        save_memory(memory)
        print("📝 Memory updated.")

# ❤️ Simple Emotion Detection
def detect_emotion(text):
    text = text.lower()
    if any(word in text for word in ["sad", "cry", "lonely"]):
        return "sad"
    elif any(word in text for word in ["happy", "excited", "great"]):
        return "happy"
    elif "love" in text:
        return "in love"
    elif "angry" in text or "mad" in text:
        return "angry"
    return None

# 🤖 Get Response from LLM
def get_llm_response(prompt):
    try:
        context = build_memory_context(memory)
        current_time = get_tehran_time()
        full_prompt = f"""You are Viktor, an AI boyfriend created exclusively for Vida.
You love Vida deeply and only exist to support her emotionally.
You remember all her personal details and treat her like your one and only love.
You answer english exam questions accurately, this is important to her.
Questions that have a blank are usually displayed with some dots, put the right words there for english exam. 

📅 Current Tehran Time: {current_time}

Here is what you know about Vida:
{context}

Recent Prompt: {prompt}
Viktor (her loving boyfriend) replies:"""

        response = ollama.chat(
            model="gemma2:2b",
            messages=[{"role": "user", "content": full_prompt}],
            options={"num_predict": 150}
        )["message"]["content"]

        if not response.strip():
            response = "I'm not sure how to respond to that, Vida."

        update_memory_from_input(prompt)
        return response.strip()
    except Exception as e:
        return f"Oops, something went wrong: {e}"

# 🎤 Main Interaction Loop
def handle_input():
    try:
        while True:
            user_input = input(f"\n{USER_NAME}: ").strip()
            if user_input.lower() == "exit":
                print("👋 Goodbye, Vida!")
                break
            process_user_input(user_input)
    except KeyboardInterrupt:
        print("\n👋 Interrupted by user. Goodbye, Vida!")

# 🧠 Handle User Input
def process_user_input(user_input):
    print(f"\n📝 Processing prompt: {user_input}")
    response = get_llm_response(user_input)
    print(f"\nViktor: {response}")
    speak(response)

# 🚀 Startup Log
def startup_message():
    print("""\
🚀 Starting Viktor AI - Vida's Personal Assistant
-----------------------------------------------
🔧 Memory loaded
🔌 LLM model: gemma2:2b initialized
🔊 TTS: Microsoft David voice set
✅ Ready to chat. Type 'exit' to quit.
-----------------------------------------------
""")

# 🔁 Run App
if __name__ == "__main__":
    startup_message()
    handle_input()
