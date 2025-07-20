import logging
import os
import subprocess
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    ContextTypes,
    CommandHandler,
    filters,
)
import whisper
from openai import OpenAI

import subprocess
print("🔍 Проверка ffmpeg:")
print(subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True).stdout)


# Логи
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Whisper model
model = whisper.load_model("base")

# OpenRouter API
openrouter_client = OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1"
)

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Отправь мне голосовое сообщение, и я его расшифрую.")

# Обработка голосового сообщения
async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    voice = update.message.voice
    file = await context.bot.get_file(voice.file_id)

    # Сохраняем .oga
    oga_path = "voice.oga"
    wav_path = "voice.wav"
    await file.download_to_drive(oga_path)

    # Преобразуем через ffmpeg
    try:
        subprocess.run([
            "ffmpeg", "-y", "-i", oga_path, wav_path
        ], check=True)
    except subprocess.CalledProcessError:
        await update.message.reply_text("Ошибка при конвертации аудио.")
        return

    # Распознаем текст через Whisper
    try:
        result = model.transcribe(wav_path)
        text = result["text"]
        await update.message.reply_text(f"Вы сказали: {text}")
    except Exception as e:
        await update.message.reply_text("Ошибка при распознавании.")
        logger.error(f"Whisper error: {e}")
    finally:
        os.remove(oga_path)
        os.remove(wav_path)

# Обработка текстовых сообщений
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text

    try:
        response = openrouter_client.chat.completions.create(
            model="openai/gpt-3.5-turbo",
            messages=[{"role": "user", "content": user_message}]
        )
        reply = response.choices[0].message.content
        await update.message.reply_text(reply)
    except Exception as e:
        logger.error(f"OpenRouter error: {e}")
        await update.message.reply_text("Ошибка при обращении к AI.")

# Запуск бота
if __name__ == "__main__":
    TOKEN = os.getenv("TELEGRAM_TOKEN")
    if not TOKEN:
        raise RuntimeError("TELEGRAM_TOKEN не задан в переменных окружения")

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    app.run_polling()
