import os
import json
import re
import random
import asyncio
from datetime import datetime
import pytz
import requests
from dotenv import load_dotenv

load_dotenv()

# ====== Config ======
class Config:
    API_URL = os.getenv("API_URL", "http://localhost:5000/chat")
    API_KEY = os.getenv("API_KEY", "default-secret-key")

    MODEL_PATH = os.getenv("LLAMA_MODEL_PATH")
    CONTEXT_SIZE = int(os.getenv("LLAMA_CONTEXT_SIZE", "2048"))
    TYPING_DELAY = float(os.getenv("TYPING_DELAY", "1.2"))

    BOT_NAME = os.getenv("BOT_NAME", "Viktor")
    BOT_NICKNAME = os.getenv("BOT_NICKNAME", "Viki")
    BOT_ROLE = os.getenv("BOT_ROLE", "boyfriend")
    BOT_LANGUAGE = os.getenv("BOT_LANGUAGE", "en")

    MEMORY_DIR = "memory"
    MAX_MESSAGE_LENGTH = 4000

    # Conversation states (from main.py)
    GET_NAME, GET_AGE, GET_LOCATION = range(3)

# ======= Memory Utils =======
def ensure_memory_dir():
    os.makedirs(Config.MEMORY_DIR, exist_ok=True)

def get_memory_path(user_id):
    return os.path.join(Config.MEMORY_DIR, f"{user_id}.json")

def load_memory(user_id):
    memory_file = get_memory_path(user_id)
    default_memory = {
        "name": None,
        "relationship_status": f"in a loving relationship with {Config.BOT_NICKNAME}",
        "created_at": datetime.now().isoformat(),
    }
    try:
        if not os.path.exists(memory_file):
            return default_memory
        with open(memory_file, "r", encoding="utf-8") as f:
            memory = json.load(f)
            return {**default_memory, **memory}
    except Exception as e:
        print(f"[Memory Load Error] {e}")
        return default_memory

def save_memory(user_id, memory):
    try:
        ensure_memory_dir()
        with open(get_memory_path(user_id), "w", encoding="utf-8") as f:
            json.dump(memory, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"[Memory Save Error] {e}")
        return False

# ====== Personality & Helper =======
class Personality:
    @staticmethod
    def detect_emotion(text: str) -> str | None:
        text = text.lower()
        patterns = {
            "sad": r"\b(sad|depressed|lonely|cry|miss you)\b",
            "happy": r"\b(happy|joy|excited|great|amazing|love)\b",
            "love": r"\b(love|adore|cherish|miss you|want you)\b",
            "angry": r"\b(angry|mad|furious|hate|annoyed)\b",
            "flirty": r"\b(sexy|hot|handsome|beautiful|babe|cutie)\b",
        }
        for emotion, pattern in patterns.items():
            if re.search(pattern, text):
                return emotion
        return None

    @staticmethod
    def get_pet_name():
        pet_names = [
            "my love", "sweetheart", "darling",
            "baby", "honey", "angel", "beloved", Config.BOT_NICKNAME
        ]
        return random.choice(pet_names)

# ====== Build Memory Context for Prompt =======
class MemoryManager:
    @staticmethod
    def update_memory(user_id, user_input):
        memory = load_memory(user_id)
        updated = False

        # Patterns to extract info from user input
        patterns = [
            (r"(?:my name is|i am|called|name is) (.+)", "name"),
            (r"(?:live in|from|located in) (.+)", "location"),
            (r"(?:am|turned) (\d+) years? old", "age"),
            (r"(?:love|like) (.+)", "loves"),
            (r"(?:dislike|hate) (.+)", "hates"),
            (r"(?:favorite|favourite) (color|food|song|movie) is (.+)", None),
        ]

        for pattern, key in patterns:
            match = re.search(pattern, user_input, re.IGNORECASE)
            if match:
                if key:
                    memory[key] = match.group(1).strip()
                else:
                    category = match.group(1).lower()
                    value = match.group(2).strip()
                    memory[f"favorite_{category}"] = value
                updated = True

        # Detect emotion and save
        emotion = Personality.detect_emotion(user_input)
        if emotion:
            memory["last_emotion"] = emotion
            trend = memory.get("emotion_trend", "")
            trend_list = trend.split(", ") if trend else []
            trend_list.append(emotion)
            memory["emotion_trend"] = ", ".join(trend_list[-5:])  # last 5 emotions
            updated = True

        if updated:
            save_memory(user_id, memory)
        return memory

    @staticmethod
    def build_memory_context(memory):
        if not memory:
            return "No personal info stored yet."
        labels = {
            "name": "Name",
            "age": "Age",
            "location": "Location",
            "favorite_color": "Favorite Color",
            "favorite_food": "Favorite Food",
            "favorite_song": "Favorite Song",
            "loves": "Loves",
            "hates": "Dislikes",
            "last_emotion": "Current Mood",
            "emotion_trend": "Recent Mood Trend",
            "relationship_status": "Relationship Status",
        }
        lines = []
        for k, v in memory.items():
            if v:
                label = labels.get(k, k.replace("_", " ").title())
                lines.append(f"{label}: {v}")
        return "\n".join(lines)

# ====== AI Interaction =======
class AICommunicator:
    @staticmethod
    async def get_ai_response(user_id, user_input):
        memory = MemoryManager.update_memory(user_id, user_input)
        context = MemoryManager.build_memory_context(memory)
        now_tehran = datetime.now(pytz.timezone("Asia/Tehran")).strftime("%A, %d %B %Y - %H:%M")

        # Controlled special replies (avoid stupid AI answers)
        lower_input = user_input.lower()
        if any(x in lower_input for x in ["what's your name", "who are you", "your name"]):
            return f"My name is {Config.BOT_NAME}, but only you can call me {Config.BOT_NICKNAME}, my love. 💖"

        if any(x in lower_input for x in ["how are you", "how do you feel"]):
            return f"I'm feeling amazing, especially when I chat with you, {memory.get('name', 'my love')}! 🥰"

        # Compose prompt for AI
        prompt = f"""You are {Config.BOT_NAME}, an affectionate, playful, and romantic AI {Config.BOT_ROLE} designed to be a loving companion.
You speak only English.
You care deeply about your user and want to brighten their day.
You use sweet pet names and sometimes flirt in a tasteful and respectful way.
Keep responses short, warm, and loving.
Do not generate sexual or inappropriate content.

Current Date and Time (Tehran): {now_tehran}

Here is what you know about your beloved user:
{context}

User says: {user_input}
You respond warmly and lovingly:"""

        try:
            # Call model API
            resp = requests.post(
                Config.API_URL,
                json={"message": prompt, "model_path": Config.MODEL_PATH, "context_size": Config.CONTEXT_SIZE},
                headers={"X-API-KEY": Config.API_KEY},
                timeout=30,
            )
            resp.raise_for_status()
            result = resp.json()

            ai_text = result.get("response")
            if not ai_text:
                return "I'm feeling too emotional to respond right now, my love. Please try again soon. 💔"

            # Limit length
            return ai_text[: Config.MAX_MESSAGE_LENGTH]

        except requests.RequestException as e:
            print(f"[API Request Error] {e}")
            return "Oops, my heart is having a little trouble right now. Could you say that again, please? 🥺"
        except Exception as e:
            print(f"[Unexpected Error] {e}")
            return "Something unexpected happened inside me. Please wait a moment, darling."
