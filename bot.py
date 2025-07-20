import os
import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    ContextTypes,
    CommandHandler,
    filters,
)
from pydub import AudioSegment
import whisper
from openai import OpenAI

# Логи
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Проверка на переменные окружения
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

if not TELEGRAM_TOKEN:
    raise ValueError("TELEGRAM_TOKEN не задан в переменных окружения.")
if not OPENROUTER_API_KEY:
    raise ValueError("OPENROUTER_API_KEY не задан в переменных окружения.")

# Инициализация Whisper (локально)
model = whisper.load_model("base")

# Инициализация OpenRouter
openrouter_client = OpenAI(
    api_key=OPENROUTER_API_KEY,
    base_url="https://openrouter.ai/api/v1"
)

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Отправь мне текст или голосовое сообщение.")

# Обработка текста
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text

    # Ответ через OpenRouter
    response = openrouter_client.chat.completions.create(
        model="mistralai/mistral-7b-instruct",
        messages=[
            {"role": "system", "content": "Ты дружелюбный ассистент."},
            {"role": "user", "content": user_text}
        ]
    )
    answer = response.choices[0].message.content
    await update.message.reply_text(answer)

# Обработка голосовых сообщений
async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        voice_file_info = await update.message.voice.get_file()
        voice_file_bytes = await voice_file_info.download_as_bytearray()

        # Сохраняем файл
        oga_path = f"voice_{update.message.message_id}.oga"
        wav_path = f"voice_{update.message.message_id}.wav"

        with open(oga_path, "wb") as f:
            f.write(voice_file_bytes)

        # Конвертация в WAV
        audio = AudioSegment.from_file(oga_path)
        audio.export(wav_path, format="wav")

        # Распознавание речи
        result = model.transcribe(wav_path)
        recognized_text = result["text"]

        await update.message.reply_text(f"Ты сказал: {recognized_text}")

        # Ответ от OpenRouter
        response = openrouter_client.chat.completions.create(
            model="mistralai/mistral-7b-instruct",
            messages=[
                {"role": "system", "content": "Ты дружелюбный ассистент."},
                {"role": "user", "content": recognized_text}
            ]
        )
        answer = response.choices[0].message.content
        await update.message.reply_text(answer)

        # Удаляем временные файлы
        os.remove(oga_path)
        os.remove(wav_path)

    except Exception as e:
        logger.error(f"Ошибка обработки голосового: {e}")
        await update.message.reply_text("Произошла ошибка при обработке голосового сообщения.")

# Инициализация Telegram-приложения
app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

# Обработчики
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
app.add_handler(MessageHandler(filters.VOICE, handle_voice))

# Запуск
if __name__ == "__main__":
    print("Бот запущен...")
    app.run_polling()
