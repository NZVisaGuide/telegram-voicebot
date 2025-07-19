import logging
import os
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

# Инициализация Whisper (локально)
model = whisper.load_model("base")

# OpenRouter API
openrouter_client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key="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",
)

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Отправь мне текст или голосовое сообщение.")

# Текстовые сообщения
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text

    # Отправляем в OpenRouter
    response = openrouter_client.chat.completions.create(
        model = "mistralai/mistral-7b-instruct",
        messages=[
            {"role": "system", "content": "Ты дружелюбный ассистент."},
            {"role": "user", "content": user_text}
        ]
    )
    answer = response.choices[0].message.content

    await update.message.reply_text(answer)

# Голосовые сообщения
async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        voice_file_info = await update.message.voice.get_file()
        voice_file_bytes = await voice_file_info.download_as_bytearray()

        # Сохраняем в файл в текущей папке
        oga_path = f"voice_{update.message.message_id}.oga"
        wav_path = f"voice_{update.message.message_id}.wav"

        with open(oga_path, "wb") as f:
            f.write(voice_file_bytes)

        # Конвертация в WAV
        audio = AudioSegment.from_file(oga_path)
        audio.export(wav_path, format="wav")

        # Распознавание
        result = model.transcribe(wav_path)
        recognized_text = result["text"]

        await update.message.reply_text(f"Ты сказал: {recognized_text}")

        # Отправляем распознанное в OpenRouter
        response = openrouter_client.chat.completions.create(
            model="mistralai/mistral-7b-instruct",
            messages=[
                {"role": "system", "content": "Ты дружелюбный ассистент."},
                {"role": "user", "content": recognized_text}
            ]
        )
        answer = response.choices[0].message.content
        await update.message.reply_text(answer)

        # Удаляем файлы
        os.remove(oga_path)
        os.remove(wav_path)

    except Exception as e:
        logger.error(f"Ошибка обработки голосового: {e}")
        await update.message.reply_text("Произошла ошибка при обработке голосового сообщения.")

# Создаем приложение
app = ApplicationBuilder().token("8014429586:AAFWrcR2qfa3t-EPZDe_eut4L5U7S3cShe0").build()

# Обработчики
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
app.add_handler(MessageHandler(filters.VOICE, handle_voice))

# Запуск
if __name__ == "__main__":
    print("Бот запущен...")
    app.run_polling()
