import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from aiohttp import web

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Get environment variables
BOT_TOKEN = os.environ.get("BOT_TOKEN")
PORT = int(os.environ.get("PORT", "8080"))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello! Send me an image and I will convert it into a link.")

async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Image handling logic here
    await update.message.reply_text("Processing image...")

async def handle_web(request):
    return web.Response(text="Bot is running!")

def main():
    if not BOT_TOKEN:
        print("Error: BOT_TOKEN environment variable not set.")
        return

    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.PHOTO, handle_image))

    print("Bot started successfully!")
    application.run_polling()

if __name__ == "__main__":
    main()
  
