

# OPENAI_API_SecretKey = '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'

# bot = telebot.TeleBot('8014429586:AAE01nELk-N3VN_R9pcUxt0VK4uAfP3ImfA')

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
from openai import OpenAI

# Инициализация OpenAI клиента
client = OpenAI(api_key="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")

# Обработчик команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я бот ChatGPT. Напиши мне что-нибудь.")

# Обработчик всех текстовых сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text

    # Отправляем запрос к ChatGPT
    completion = client.chat.completions.create(
        model="gpt-4o-mini",  # или gpt-3.5-turbo
        messages=[
            {"role": "system", "content": "Ты дружелюбный ассистент."},
            {"role": "user", "content": user_message}
        ]
    )

    reply_text = completion.choices[0].message.content

    # Отправляем ответ пользователю
    await update.message.reply_text(reply_text)

# Основной запуск бота
if __name__ == '__main__':
    app = ApplicationBuilder().token("8014429586:AAE01nELk-N3VN_R9pcUxt0VK4uAfP3ImfA").build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Бот запущен...")
    app.run_polling()
