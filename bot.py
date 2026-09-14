import os
import logging
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

# Logging Setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# ------------------------------------------------------------------
# Bot Credentials Configured
BOT_TOKEN = "8649227717:AAEj9lgvTmu87PRP8gStEPkrx0ZZODbPifs"
ADMIN_CHAT_ID = "8402780798"
# ------------------------------------------------------------------

# Dual API Direct Image Upload (Catbox + ImgBB Backup)
def upload_image_api(file_path):
    # API 1: Catbox.moe
    try:
        url = "https://catbox.moe/user/api.php"
        data = {"reqtype": "fileupload"}
        with open(file_path, "rb") as f:
            files = {"fileToUpload": f}
            res = requests.post(url, data=data, files=files, timeout=25)
        if res.status_code == 200 and res.text.startswith("http"):
            return res.text.strip()
    except Exception as e:
        logging.error(f"Catbox Upload Failed: {e}")

    # API 2: ImgBB Alternative Endpoint (Fallback)
    try:
        url = "https://api.imgbb.com/1/upload"
        params = {"key": "6d002710c72170e58042323c4355d042"} # Public high-speed key
        with open(file_path, "rb") as f:
            files = {"image": f}
            res = requests.post(url, params=params, files=files, timeout=25)
        if res.status_code == 200:
            json_data = res.json()
            return json_data["data"]["url"]
    except Exception as e:
        logging.error(f"ImgBB Upload Failed: {e}")

    return None

# Command: /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name

    welcome_text = (
        f"✨ *Welcome, {user_name}!*\n\n"
        f"🤖 *Atikul Image-to-Link Bot*-এ আপনাকে স্বাগতম!\n\n"
        f"📸 *আপনার ছবিটি এখনই সেন্ড করুন* (Photo অথবা File/Document হিসেবে)।\n"
        f"আমি নিমেষেই একটি আল্ট্রা-ফাস্ট ডাইরেক্ট লিঙ্ক (Direct URL) তৈরি করে দেব!"
    )

    keyboard = [
        [InlineKeyboardButton("📤 Upload Image Now", callback_query_data="prompt_upload")],
        [InlineKeyboardButton("🌐 Developer & Support", url="https://t.me/atqul_services_bot")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(welcome_text, parse_mode="Markdown", reply_markup=reply_markup)

# Button Callbacks
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "prompt_upload":
        await query.edit_message_text(
            "📥 *অনুগ্রহ করে আপনার ছবিটি এখনই চ্যাটে সেন্ড করুন...*\n\n"
            "⚡ _সরাসরি ফটো অথবা ফাইল যেকোনোভাবে পাঠাতে পারেন।_",
            parse_mode="Markdown"
        )

# Image Handler
async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    user = update.effective_user

    # Initial Animated Status
    status_msg = await message.reply_text("⚡ *Processing Image...* [▓░░░░░░░░░] 10%", parse_mode="Markdown")

    try:
        # Get File ID
        if message.photo:
            file_id = message.photo[-1].file_id
        elif message.document and message.document.mime_type.startswith("image/"):
            file_id = message.document.file_id
        else:
            await status_msg.edit_text("❌ *অনুগ্রহ করে শুধু সঠিক ইমেজ ফাইল পাঠান!*", parse_mode="Markdown")
            return

        # Progress updates
        await status_msg.edit_text("🔄 *Downloading from Telegram...* [▓▓▓▓░░░░░░] 40%", parse_mode="Markdown")

        file = await context.bot.get_file(file_id)
        file_path = f"temp_{file_id}.jpg"
        await file.download_to_drive(file_path)

        await status_msg.edit_text("🚀 *Generating Direct Link...* [▓▓▓▓▓▓▓▓░░] 80%", parse_mode="Markdown")

        # Upload via Dual API
        direct_link = upload_image_api(file_path)

        # Cleanup local storage
        if os.path.exists(file_path):
            os.remove(file_path)

        if direct_link:
            result_text = (
                f"✅ *আপনার ছবির ডাইরেক্ট লিঙ্ক প্রস্তুত!*\n\n"
                f"🔗 *Direct Link:*\n`{direct_link}`\n\n"
                f"💡 _লিঙ্কে চাপ দিয়ে সহজেই কপি করতে পারবেন।_"
            )
            keyboard = [[InlineKeyboardButton("🌐 Open Direct Link", url=direct_link)]]
            await status_msg.edit_text(result_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

            # Send Notification to Admin Panel
            try:
                admin_notify = (
                    f"🔔 *New Image Uploaded!*\n\n"
                    f"👤 *User:* {user.first_name} (@{user.username if user.username else 'N/A'})\n"
                    f"🆔 *User ID:* `{user.id}`\n"
                    f"🔗 *Link:* `{direct_link}`"
                )
                await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=admin_notify, parse_mode="Markdown")
            except Exception as admin_err:
                logging.error(f"Failed to notify admin: {admin_err}")
        else:
            await status_msg.edit_text("⚠️ *লিঙ্ক জেনারেট করতে সমস্যা হয়েছে! অনুগ্রহ করে আবার চেষ্টা করুন।*", parse_mode="Markdown")

    except Exception as e:
        logging.error(f"Error handling image: {e}")
        await status_msg.edit_text("❌ *একটি অপ্রত্যাশিত সমস্যা হয়েছে। আবার চেষ্টা করুন।*", parse_mode="Markdown")

# Main Runner
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.PHOTO | filters.Document.IMAGE, handle_image))

    print("Bot is online and running smoothly...")
    app.run_polling()

if __name__ == "__main__":
    main()
    
