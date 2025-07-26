# 💖 Viktor: Your AI Boyfriend Telegram Bot

Viktor is a charming, voice-assisted, memory-enabled AI boyfriend Telegram bot built with `python-telegram-bot` and powered by a local [TinyLLaMA](https://github.com/cmp-nct/tinyllama) model. He remembers your name, age, location—and flirts with personality. 😏

## ✨ Features

- 🧠 **Personal Memory** (name, age, location)
- 💌 **Custom Responses** for greetings, flirty jokes, and AI-style love
- 🧠 **Powered by a local TinyLLaMA GGUF model**
- 💬 **Conversational flow** with controlled prompts
- 🧑‍🤝‍🧑 Designed for a private, fun, romantic chatbot experience
- 🔐 **Secure .env-based token management**
- 📁 Modular codebase for easy extension

---

## 📁 Project Structure

``` text

viktor-bot/
├── main.py               # Telegram bot entry point
├── vikibot_api.py        # AI and memory handling module
├── .env                  # Secrets like your TELEGRAM_TOKEN
├── requirements.txt      # Required Python libraries
└── memory/               # Per-user memory storage (auto-created)

```

---

## ⚙️ Requirements

- Python 3.10+
- Local GGUF-compatible LLM running via an API server
- Telegram Bot Token

---

## 🛠️ Setup

1. **Clone the repository**  
   ```bash
   git clone https://github.com/VIDAKHOSHPEY22/Viktor.git
   cd Viktor

2. Install dependencies

pip install -r requirements.txt


3. Create a .env file in the root directory:

``` text
TELEGRAM_TOKEN=your_telegram_bot_token
AI_API_URL=http://localhost:11434/api/generate
AI_MODEL_NAME=tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf
```
``` AI_SYSTEM_PROMPT=You are Viktor, a charming and slightly flirtatious AI boyfriend... ```


4. Start your local model server
Use Ollama or any local LLM server that supports tinyllama GGUF.


5. Run the bot

``` bash python main.py ```




---

🧠 Memory & Persistence

Each user’s memory is stored in a separate .json file inside the memory/ folder. It includes:

name

age

location


The bot uses these to personalize every interaction.


---

❤️ Personality

Viktor responds to:

"What's your name?"

"How are you?"

"I miss you"

"Do you love me?"


And more—through controlled replies and flirty lines. You can expand vikibot_api.py with more personalized responses.


---

🔒 Security

Your Telegram token and other secrets are never hardcoded. Use .env for all sensitive data. The bot also avoids sending explicit content or violating Telegram's guidelines.


---

🤖 Sample Interaction

/start
❤️ Hello, beautiful! I'm Viktor. What's your name?

User: My name is Vida.
Viktor: What a beautiful name, Vida! How old are you?

User: I'm 23.
Viktor: Perfect age to be loved! Where are you from, my darling?

User: I'm from Iran.
Viktor: Thank you, Vida! I’ll remember you forever 💕


---

📌 Roadmap Ideas

Text-to-speech voice messages

Real-time emotional detection

Scheduled love messages 💌

Support for romantic games or quizzes



---

👩‍💻 Author

Vida Khoshpey
GitHub: @VIDAKHOSHPEY22
Twitter: @VidaTwin16133


---

⭐ Star if you like Viktor!

He might even send you a virtual kiss 😘

---
