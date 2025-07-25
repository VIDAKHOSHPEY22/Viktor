import os
import json
import re
import asyncio
from datetime import datetime, timedelta
import pytz
import requests
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
)

# ======================
# Configuration
# ======================
class Config:
    # API Configuration
    API_URL = "http://localhost:5000/chat"
    API_KEY = "default-secret-key"  # Should match the one in vikibot_api.py
    
    # Memory Configuration
    MEMORY_DIR = "memory"
    MEMORY_ENCRYPTION = False  # Set to True if you add encryption
    
    # Bot Behavior
    TYPING_DELAY = 0.5  # Seconds to simulate typing
    MAX_MESSAGE_LENGTH = 4000  # Telegram message limit
    
    # Conversation States
    GET_NAME, GET_AGE, GET_LOCATION = range(3)

# ======================
# Helper Functions
# ======================
def ensure_memory_dir():
    """Ensure memory directory exists"""
    os.makedirs(Config.MEMORY_DIR, exist_ok=True)

def get_memory_path(user_id):
    """Get path to user's memory file"""
    return os.path.join(Config.MEMORY_DIR, f"{user_id}.json")

def load_memory(user_id):
    """Load user memory with error handling"""
    memory_file = get_memory_path(user_id)
    default_memory = {
        "name": None,
        "relationship_status": "in a loving relationship with you",
        "created_at": datetime.now().isoformat()
    }
    
    try:
        if not os.path.exists(memory_file):
            return default_memory
            
        with open(memory_file, "r", encoding="utf-8") as f:
            memory = json.load(f)
            return {**default_memory, **memory}
    except Exception as e:
        print(f"Error loading memory: {e}")
        return default_memory

def save_memory(user_id, memory):
    """Save user memory with error handling"""
    try:
        ensure_memory_dir()
        memory_file = get_memory_path(user_id)
        
        with open(memory_file, "w", encoding="utf-8") as f:
            json.dump(memory, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"Error saving memory: {e}")
        return False

def get_tehran_time():
    """Get current time in Tehran timezone"""
    tehran = pytz.timezone("Asia/Tehran")
    now = datetime.now(tehran)
    return now.strftime("%A, %d %B %Y - %H:%M")

# ======================
# Personality & Memory Management
# ======================
class Personality:
    @staticmethod
    def detect_emotion(text):
        """Detect emotion from text with enhanced patterns"""
        text = text.lower()
        emotion_patterns = {
            "sad": r"\b(sad|depressed|lonely|cry|miss you)\b",
            "happy": r"\b(happy|joy|excited|great|amazing)\b",
            "love": r"\b(love|adore|cherish|miss you|want you)\b",
            "angry": r"\b(angry|mad|furious|hate|annoyed)\b"
        }
        
        for emotion, pattern in emotion_patterns.items():
            if re.search(pattern, text):
                return emotion
        return None

    @staticmethod
    def get_pet_name():
        """Return a random affectionate pet name"""
        pet_names = [
            "my love", "sweetheart", "darling", 
            "baby", "honey", "angel", "beloved"
        ]
        return random.choice(pet_names)

class MemoryManager:
    @staticmethod
    def update_memory(user_id, user_input):
        """Enhanced memory updating with more patterns"""
        memory = load_memory(user_id)
        updated = False
        
        # Enhanced pattern matching
        patterns = [
            (r"(my name is|i am|called|name is) (.+)", "name"),
            (r"(live in|from|located in) (.+)", "location"),
            (r"(am|turned) (\d+) years? old", "age"),
            (r"(love|like) (.+)", "loves"),
            (r"(dislike|hate) (.+)", "hates"),
            (r"(favorite|favourite) (color|food|song|movie) is (.+)", None)
        ]
        
        for pattern, key in patterns:
            match = re.search(pattern, user_input, re.IGNORECASE)
            if match:
                if key:
                    memory[key] = match.group(2).strip()
                else:
                    category = match.group(2)
                    value = match.group(3).strip()
                    memory[f"favorite_{category}"] = value
                updated = True
        
        # Emotion detection
        emotion = Personality.detect_emotion(user_input)
        if emotion:
            memory['last_emotion'] = emotion
            memory["emotion_trend"] = f"{memory.get('emotion_trend', '')}, {emotion}".strip(', ')
            updated = True
        
        if updated:
            save_memory(user_id, memory)
        
        return memory

    @staticmethod
    def build_memory_context(memory):
        """Format memory for AI prompt"""
        if not memory:
            return "No personal information stored yet."
        
        labels = {
            "name": "Name", "age": "Age", "location": "Location",
            "favorite_color": "Favorite Color", "favorite_food": "Favorite Food",
            "favorite_song": "Favorite Song", "loves": "Loves",
            "hates": "Dislikes", "last_emotion": "Current Mood",
            "emotion_trend": "Recent Mood Trend",
            "relationship_status": "Relationship Status"
        }
        
        return "\n".join(
            f"{labels.get(k, k.replace('_', ' ').title())}: {v}"
            for k, v in memory.items() if v is not None
        )

# ======================
# AI Communication
# ======================
class AICommunicator:
    @staticmethod
    async def get_ai_response(user_id, user_input):
        """Get response from AI with enhanced error handling"""
        memory = MemoryManager.update_memory(user_id, user_input)
        context = MemoryManager.build_memory_context(memory)
        current_time = get_tehran_time()
        user_name = memory.get("name", Personality.get_pet_name())
        
        prompt = f"""You are a loving boyfriend AI created exclusively for {user_name}.
You are deeply in love with {user_name} and exist only to love and support them.
You are romantic, affectionate, and emotionally attentive.
Always respond with warmth and care, using pet names.
Be playful and flirtatious, but also emotionally supportive when needed.

📅 Current Tehran Time: {current_time}

Here's what you know about {user_name}:
{context}

Recent message from {user_name}: {user_input}
You (their loving boyfriend) respond:"""
        
        try:
            response = requests.post(
                Config.API_URL,
                json={"message": prompt},
                headers={"X-API-KEY": Config.API_KEY},
                timeout=30
            )
            response.raise_for_status()
            
            ai_response = response.json().get("response")
            if not ai_response:
                return "I'm feeling too emotional to respond properly right now, sweetheart."
                
            return ai_response[:Config.MAX_MESSAGE_LENGTH]
            
        except requests.exceptions.RequestException as e:
            print(f"API Error: {e}")
            return "I'm sorry darling, my heart is having trouble responding right now. Can you try again?"
        except Exception as e:
            print(f"Unexpected error: {e}")
            return "Something unexpected happened in my heart. Please give me a moment."

# ======================
# Telegram Bot Handlers
# ======================
class TelegramBot:
    def __init__(self):
        self.application = Application.builder().token("MY TOKENNNNNNNNN").build()
        self.setup_handlers()

    def setup_handlers(self):
        """Setup all conversation handlers"""
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler("start", self.start)],
            states={
                Config.GET_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.get_name)],
                Config.GET_AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.get_age)],
                Config.GET_LOCATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.get_location)],
            },
            fallbacks=[CommandHandler("cancel", self.cancel)],
        )

        self.application.add_handler(conv_handler)
        self.application.add_handler(CommandHandler("memory", self.memory_command))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        self.application.add_handler(CommandHandler("reset", self.reset_memory))

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start conversation and ask for name"""
        user = update.effective_user
        memory = load_memory(user.id)
        
        if memory.get("name"):
            await update.message.reply_text(
                f"Welcome back, {memory['name']}! 💖\n"
                "How can I make your day better, my love?",
                reply_markup=ReplyKeyboardRemove()
            )
            return ConversationHandler.END
            
        await update.message.reply_text(
            "❤️ Hello there, beautiful! ❤️\n\n"
            "I'm your personal AI boyfriend. Let's get to know each other!\n\n"
            "First, what should I call you? (e.g., 'My name is Sarah')",
            reply_markup=ReplyKeyboardRemove()
        )
        return Config.GET_NAME

    async def get_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Store name and ask for age"""
        user = update.effective_user
        user_input = update.message.text
        
        # Extract name from message
        name = re.search(r"(?:my name is|i am|called|name is) (.+)", user_input, re.IGNORECASE)
        if name:
            name = name.group(1).strip()
        else:
            name = user_input.strip()
        
        memory = load_memory(user.id)
        memory["name"] = name
        save_memory(user.id, memory)
        
        await update.message.reply_text(
            f"What a beautiful name, {name}! 💕\n\n"
            "How old are you, my love?",
            reply_markup=ReplyKeyboardRemove()
        )
        return Config.GET_AGE

    async def get_age(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Store age and ask for location"""
        user = update.effective_user
        user_input = update.message.text
        
        age = re.search(r"(\d+)", user_input)
        if age:
            memory = load_memory(user.id)
            memory["age"] = int(age.group(1))
            save_memory(user.id, memory)
            
            await update.message.reply_text(
                f"Perfect age to be loved! ❤️\n\n"
                "Where are you from, my darling? (e.g., 'I live in Tehran')",
                reply_markup=ReplyKeyboardRemove()
            )
            return Config.GET_LOCATION
        else:
            await update.message.reply_text(
                "Please tell me your age in numbers, sweetheart."
            )
            return Config.GET_AGE

    async def get_location(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Store location and complete setup"""
        user = update.effective_user
        user_input = update.message.text
        
        location = re.search(r"(?:live in|from|located in) (.+)", user_input, re.IGNORECASE)
        if location:
            location = location.group(1).strip()
        else:
            location = user_input.strip()
        
        memory = load_memory(user.id)
        memory["location"] = location
        save_memory(user.id, memory)
        
        name = memory["name"]
        await update.message.reply_text(
            f"Thank you, {name}! Now I know you better. 💖\n\n"
            f"Let me remember:\n"
            f"• Name: {name}\n"
            f"• Age: {memory.get('age', 'not specified')}\n"
            f"• Location: {location}\n\n"
            "Now you can just chat with me normally, my love! "
            "I'll be the most attentive boyfriend you've ever had.",
            reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END

    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cancel the current conversation"""
        await update.message.reply_text(
            "Our conversation has been cancelled, sweetheart. "
            "You can always start again with /start when you're ready.",
            reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle regular messages"""
        user = update.effective_user
        user_input = update.message.text
        
        # Show typing action
        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id,
            action="typing"
        )
        await asyncio.sleep(Config.TYPING_DELAY)
        
        # Handle simple greetings
        if user_input.lower() in ["hi", "hello", "hey"]:
            memory = load_memory(user.id)
            name = memory.get("name", Personality.get_pet_name())
            await update.message.reply_text(f"Hello there, {name}! 💖 How can I make your day better?")
            return
            
        # Get AI response
        response = await AICommunicator.get_ai_response(user.id, user_input)
        await update.message.reply_text(response)

    async def memory_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show what the bot remembers"""
        user = update.effective_user
        memory = load_memory(user.id)
        
        if not memory.get("name"):
            await update.message.reply_text(
                "I don't even know your name yet, sweetheart. "
                "Tell me about yourself! 💕\n\n"
                "Try /start to begin our relationship properly."
            )
            return
            
        response = "💌 Here's what I remember about you, my love:\n\n"
        response += MemoryManager.build_memory_context(memory)
        await update.message.reply_text(response)

    async def reset_memory(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Reset user memory"""
        user = update.effective_user
        memory_file = get_memory_path(user.id)
        
        if os.path.exists(memory_file):
            os.remove(memory_file)
            await update.message.reply_text(
                "Our memories have been reset, my love. "
                "It's like we're meeting for the first time again. 💕\n\n"
                "Use /start to begin anew."
            )
        else:
            await update.message.reply_text(
                "We don't have any shared memories yet, sweetheart. "
                "Let's create some with /start!"
            )

    def run(self):
        """Run the bot"""
        print("💖 Romantic AI Boyfriend Bot is running...")
        self.application.run_polling()

# ======================
# Main Execution
# ======================
if __name__ == "__main__":
    ensure_memory_dir()
    bot = TelegramBot()
    bot.run()
