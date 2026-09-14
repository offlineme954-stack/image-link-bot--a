import logging
import requests
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# Logging Setup
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Config Credentials
BOT_TOKEN = "8649227717:AAEj9lgvTmu87PRP8gStEPkrx0ZZODbPifs"
ADMIN_CHAT_ID = "8402780798"

# ---------------- COMMAND HANDLERS ---------------- #

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    welcome_text = (
        f"✨ <b>আসসালামু আলাইকুম, {user.first_name}!</b> ✨\n\n"
        "👑 <b>Atikul Image To Link Pro Bot</b>-এ আপনাকে স্বাগতম!\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "📸 <b>আপনার ছবিটি এখানে পেস্ট / সেন্ড করুন:</b>\n"
        "যেকোনো ছবি পাঠালেই চোখের পলকে তৈরি হয়ে যাবে তার ডাইরেক্ট হাই-স্পিড লিংক।\n\n"
        "🚀 <b>প্রিমিয়াম ফিচারসমূহ:</b>\n"
        "├ ⚡ Instant Direct Web Link\n"
        "├ 🗑️ Auto-Delete Uploaded Image\n"
        "├ ✨ AI Image HD Upscale Tool\n"
        "├ 🎨 One-Click Background Remover\n"
        "└ 📱 Auto QR Code Generator\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "👇 <i>শুরু করতে এখনই আপনার ছবিটি নিচে পাঠাই দিন!</i>"
    )

    keyboard = [
        [
            InlineKeyboardButton("📢 Developer Channel", url="https://t.me/atiqul_services_bot"),
            InlineKeyboardButton("👨‍💻 Admin Contact", url=f"tg://user?id={ADMIN_CHAT_ID}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        welcome_text, parse_mode="HTML", reply_markup=reply_markup
    )


# ---------------- PHOTO PROCESSING ---------------- #

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    photo_file = None

    if message.photo:
        photo_file = await message.photo[-1].get_file()
    elif message.document and message.document.mime_type and message.document.mime_type.startswith("image/"):
        photo_file = await message.document.get_file()
    else:
        await message.reply_text("❌ <b>অনুগ্রহ করে একটি বৈধ ছবি বা ইমেজ ফাইল পাঠান!</b>", parse_mode="HTML")
        return

    # Animated Processing Status
    status_msg = await message.reply_text("⚡ <b>ছবি প্রসেসিং হচ্ছে... লিংক তৈরি শেষ হলে ছবিটি অটো মুছে যাবে...</b>", parse_mode="HTML")

    try:
        # Download image into memory
        file_bytes = await photo_file.download_as_bytearray()

        # Upload to Catbox Primary API
        response = requests.post(
            "https://catbox.moe/user/api.php",
            data={"reqtype": "fileupload"},
            files={"fileToUpload": file_bytes},
            timeout=20,
        )

        if response.status_code == 200:
            direct_link = response.text.strip()

            # Dynamic & Animated Premium Buttons
            keyboard = [
                [
                    InlineKeyboardButton("🔗 ছবির লিংক নিন (Direct Link)", callback_data=f"get_link|{direct_link}")
                ],
                [
                    InlineKeyboardButton("✨ AI HD Enhancer", callback_data=f"ai_hd|{direct_link}"),
                    InlineKeyboardButton("🎨 BG Remover", callback_data=f"bg_rem|{direct_link}")
                ],
                [
                    InlineKeyboardButton("📱 QR Code তৈরি করুন", callback_data=f"make_qr|{direct_link}")
                ],
                [
                    InlineKeyboardButton("🌐 ব্রাউজারে অপেন করুন", url=direct_link)
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await status_msg.edit_text(
                "🎉 <b>আপনার ছবির ডায়রেক্ট লিংক প্রস্তুত!</b>\n"
                "✨ (মূল ছবিটি সফলভাবে মুছে ফেলা হয়েছে)\n\n"
                "👇 <b>নিচের বাটনটিতে ক্লিক করে আপনার লিংকটি সংগ্রহ করুন:</b>",
                parse_mode="HTML",
                reply_markup=reply_markup
            )

            # Auto-delete the original user uploaded photo message
            try:
                await message.delete()
            except Exception as del_err:
                logger.error(f"Failed to delete original message: {del_err}")

            # Notify Admin (Background Task)
            try:
                user_info = f"@{message.from_user.username}" if message.from_user.username else message.from_user.first_name
                admin_text = (
                    "🔔 <b>নতুন ছবি আপলোড হয়েছে!</b>\n\n"
                    f"👤 <b>ইউজার:</b> {user_info} (<code>{message.from_user.id}</code>)\n"
                    f"🔗 <b>লিংক:</b> {direct_link}"
                )
                await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=admin_text, parse_mode="HTML")
            except Exception as admin_err:
                logger.error(f"Failed to notify admin: {admin_err}")

        else:
            await status_msg.edit_text("❌ <b>ছবি আপলোড করতে ব্যর্থ হয়েছে! আবার চেষ্টা করুন।</b>", parse_mode="HTML")

    except Exception as e:
        logger.error(f"Error processing image: {e}")
        await status_msg.edit_text("⚠️ <b>সার্ভারে সমস্যা হয়েছে! কিছু সময় পর চেষ্টা করুন।</b>", parse_mode="HTML")


# ---------------- BUTTON CALLBACK HANDLER ---------------- #

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    
    # Extract Data
    data = query.data.split("|")
    action = data[0]
    link = data[1] if len(data) > 1 else ""

    if action == "get_link":
        await query.answer("✅ লিংক তৈরি সম্পন্ন!", show_alert=False)
        response_text = (
            "💎 <b>আপনার ছবির ডাইরেক্ট লিংক:</b>\n\n"
            f"<code>{link}</code>\n\n"
            "👆 <i>লিংকটির ওপর টাচ/ট্যাপ করলেই কপি হয়ে যাবে!</i>"
        )
        await query.message.reply_text(response_text, parse_mode="HTML")

    elif action == "ai_hd":
        await query.answer("✨ AI HD Enhancer টুল লোড হচ্ছে...", show_alert=False)
        ai_url = f"https://upscalepic.com/?ref_img={link}"
        response_text = (
            "✨ <b>AI HD Image Enhancer:</b>\n\n"
            f"আপনার ছবিটির রেজুলেশন ও কোয়ালিটি HD করতে নিচের টুলটি ব্যবহার করুন:\n🔗 {ai_url}"
        )
        await query.message.reply_text(response_text, parse_mode="HTML")

    elif action == "bg_rem":
        await query.answer("🎨 Background Remover লোড হচ্ছে...", show_alert=False)
        bg_url = "https://www.remove.bg/upload"
        response_text = (
            "🎨 <b>Background Remover Tool:</b>\n\n"
            f"ছবি থেকে ব্যাকগ্রাউন্ড রিমুভ করতে নিচের লিংকে যান:\n🔗 {bg_url}"
        )
        await query.message.reply_text(response_text, parse_mode="HTML")

    elif action == "make_qr":
        await query.answer("📱 QR Code তৈরি করা হচ্ছে...", show_alert=False)
        qr_api_url = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={link}"
        await query.message.reply_photo(
            photo=qr_api_url,
            caption=f"📱 <b>আপনার ছবির QR Code:</b>\n\n<code>{link}</code>",
            parse_mode="HTML"
        )


# ---------------- MAIN APPLICATION ---------------- #

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Handlers Registration
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO | filters.Document.IMAGE, handle_photo))
    app.add_handler(CallbackQueryHandler(button_click))

    print("=== Atikul Image To Link Bot is running natively ===")
    app.run_polling()

if __name__ == "__main__":
    main()
        
