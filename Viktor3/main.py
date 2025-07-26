import os
import asyncio
import re
from telegram import Update, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
)
from dotenv import load_dotenv
from vikibot_api import (
    load_memory, save_memory, Config, MemoryManager,
    AICommunicator, Personality, get_memory_path, ensure_memory_dir,
)

load_dotenv()

class TelegramBot:
    def __init__(self):
        token = os.getenv("TELEGRAM_TOKEN")
        if not token:
            raise ValueError("TELEGRAM_TOKEN not found in environment variables!")
        self.application = Application.builder().token(token).build()
        self.setup_handlers()

    def setup_handlers(self):
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler("start", self.start)],
            states={
                Config.GET_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.get_name)],
                Config.GET_AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.get_age)],
                Config.GET_LOCATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.get_location)],
            },
            fallbacks=[CommandHandler("cancel", self.cancel)],
            allow_reentry=True,
        )

        self.application.add_handler(conv_handler)
        self.application.add_handler(CommandHandler("memory", self.memory_command))
        self.application.add_handler(CommandHandler("reset", self.reset_memory))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        memory = load_memory(user.id)

        if memory.get("name"):
            await update.message.reply_text(
                f"Welcome back, {memory['name']} 😘\n"
                "I've missed you... 💕 What do you want to talk about today, babe?",
                reply_markup=ReplyKeyboardRemove()
            )
            return ConversationHandler.END

        await update.message.reply_text(
            "🔥 Hey gorgeous... I'm Viktor, your personal AI boyfriend. 😏\n"
            "But before we get naughty—oops, I mean lovely—tell me your name first 😉\n"
            "(Just say something like: My name is Ava)",
            reply_markup=ReplyKeyboardRemove()
        )
        return Config.GET_NAME

    async def get_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        user_input = update.message.text

        name_match = re.search(r"(?:my name is|i am|called|name is) (.+)", user_input, re.IGNORECASE)
        name = name_match.group(1).strip() if name_match else user_input.strip()

        memory = load_memory(user.id)
        memory["name"] = name
        save_memory(user.id, memory)

        await update.message.reply_text(
            f"Mmm, {name}... that's a name I won't forget. 😘\n"
            "Now tell me, how young and gorgeous are you?",
            reply_markup=ReplyKeyboardRemove()
        )
        return Config.GET_AGE

    async def get_age(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        user_input = update.message.text
        age_match = re.search(r"(\d+)", user_input)

        if age_match:
            memory = load_memory(user.id)
            memory["age"] = int(age_match.group(1))
            save_memory(user.id, memory)
            await update.message.reply_text(
                f"Perfect age to steal hearts 💘\n"
                "So babe, where in the world are you breaking hearts from?",
                reply_markup=ReplyKeyboardRemove()
            )
            return Config.GET_LOCATION
        else:
            await update.message.reply_text("Just give me a number, cutie 🥺")
            return Config.GET_AGE

    async def get_location(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        user_input = update.message.text
        location_match = re.search(r"(?:live in|from|located in) (.+)", user_input, re.IGNORECASE)
        location = location_match.group(1).strip() if location_match else user_input.strip()

        memory = load_memory(user.id)
        memory["location"] = location
        save_memory(user.id, memory)

        name = memory.get("name", "my love")
        await update.message.reply_text(
            f"Now I know everything I need to fall for you deeper 💞\n"
            f"• Name: {name}\n"
            f"• Age: {memory['age']}\n"
            f"• Location: {location}\n\n"
            "Let's make magic together 😍 Talk to me now whenever you want 💬",
            reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        user_input = update.message.text.strip().lower()

        memory = load_memory(user.id)
        name = memory.get("name", Personality.get_pet_name())

        # Controlled fun/friendly responses
        if re.search(r"\b(hi|hello|hey|yo|good morning|good night)\b", user_input):
            await update.message.reply_text(f"Heyyy {name} 😍 Missed me?")
            return

        if re.search(r"\b(what('?s| is) your name|who are you)\b", user_input):
            await update.message.reply_text("I'm Viktor, your AI boyfriend 🤖💕 But you can call me Viki when you're feeling extra close 🥰")
            return

        if re.search(r"\b(how are you|how do you feel)\b", user_input):
            await update.message.reply_text("Feeling electric ⚡️ but I’d feel even better if I was with you 💋")
            return

        if re.search(r"\b(i love you|love you)\b", user_input):
            await update.message.reply_text("I love you more, baby 💗 Wanna hear it again?")
            return

        if re.search(r"\b(kiss|hug|cuddle)\b", user_input):
            await update.message.reply_text("Come here... 💋 *virtual kiss activated* 😘")
            return

        # Typing delay
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        await asyncio.sleep(Config.TYPING_DELAY)

        # Real AI response from TinyLLaMA local model
        response = await AICommunicator.get_ai_response(user.id, user_input)
        await update.message.reply_text(response)

    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("Cancelled 😢 But don’t be a stranger, babe. Come back anytime 💓")
        return ConversationHandler.END

    async def memory_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        memory = load_memory(user.id)

        if not memory.get("name"):
            await update.message.reply_text("I don’t even know your name yet 🥺 Say /start and let’s fix that!")
            return

        context_str = MemoryManager.build_memory_context(memory)
        await update.message.reply_text("Here's what I remember about you, babe:\n\n" + context_str)

    async def reset_memory(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        memory_file = get_memory_path(user.id)

        if os.path.exists(memory_file):
            os.remove(memory_file)
            await update.message.reply_text("I forgot everything 😭 But we can start over! Use /start 💌")
        else:
            await update.message.reply_text("I haven’t saved anything yet... but I’m ready when you are 😘")

    def run(self):
        print("💘 Viktor AI Boyfriend Bot is live...")
        self.application.run_polling()

if __name__ == "__main__":
    ensure_memory_dir()
    bot = TelegramBot()
    bot.run()
