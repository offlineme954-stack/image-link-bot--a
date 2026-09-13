import os
import logging
import asyncio
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

BOT_TOKEN = os.environ.get("BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "আসসালামু আলাইকুম!\n\n"
        "আপনি যে ছবির লিংক তৈরি করতে চান, সেই ছবিটি আমাকে পাঠান।"
    )
    await update.message.reply_text(welcome_text)

async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status_message = await update.message.reply_text(
        "⏳ আপনার ছবিটি গ্রহণ করা হয়েছে...\n"
        "🔄 প্রসেসিং শুরু হচ্ছে, অনুগ্রহ করে কিছুক্ষণ অপেক্ষা করুন ░░░░░░░░░░ 0%"
    )

    try:
        await asyncio.sleep(1)
        await status_message.edit_text(
            "⏳ লিঙ্ক তৈরির কাজ চলতেছে, খুব তাড়াতাড়ি হয়ে যাবে...\n"
            "🔄 প্রসেসিং হচ্ছে ▓▓▓▓▓░░░░░ 50%"
        )

        photo_file = await update.message.photo[-1].get_file()
        file_path = await photo_file.download_to_drive()

        await asyncio.sleep(1)
        await status_message.edit_text(
            "⚡ ডাইরেক্ট লিঙ্ক জেনারেট করা হচ্ছে...\n"
            "🔄 প্রায় শেষ ▓▓▓▓▓▓▓▓▓░ 90%"
        )

        with open(file_path, 'rb') as f:
            response = requests.post(
                'https://telegra.ph/upload',
                files={'file': ('image.jpg', f, 'image/jpeg')}
            )
            data = response.json()

        if os.path.exists(file_path):
            os.remove(file_path)

        if isinstance(data, list) and 'src' in data[0]:
            direct_link = f"https://telegra.ph{data[0]['src']}"

            final_text = (
                "✅ **আপনার ছবির ডাইরেক্ট লিঙ্ক তৈরি সম্পন্ন হয়েছে!**\n\n"
                f"🔗 **ডাইরেক্ট লিঙ্ক:**\n`{direct_link}`\n\n"
                "🌐 **ব্যবহারের ক্ষেত্র:**\n"
                "এটি একটি সরাসরি (Direct Image Link)। আপনি এই লিঙ্কটি আপনার যেকোনো ওয়েবসাইট, অ্যাপ, HTML ট্যাগ (`<img src=\"...\">`) বা অন্য যেকোনো কাজের ক্ষেত্রে সরাসরি ব্যবহার করতে পারবেন।"
            )
            await status_message.edit_text(final_text, parse_mode='Markdown')
        else:
            await status_message.edit_text("❌ দুঃখিত! লিঙ্ক তৈরি করতে একটি সমস্যা হয়েছে। আবার চেষ্টা করুন।")

    except Exception as e:
        logging.error(f"Error handling image: {e}")
        await status_message.edit_text("❌ লিঙ্ক তৈরি করার সময় কোনো একটি ত্রুটি ঘটেছে। অনুগ্রহ করে আবার চেষ্টা করুন।")

def main():
    if not BOT_TOKEN:
        print("Error: BOT_TOKEN environment variable not set.")
        return

    application = ApplicationBuilder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.PHOTO, handle_image))

    print("Bot is running...")
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
    
