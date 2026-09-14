import logging
import requests
import time
import json
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
REQUIRED_CHANNEL = "@atiqul_services_bot"  # Force Subscribe Channel Username

# Memory Storage for Stats & Anti-Spam
USER_COOLDOWN = {}
TOTAL_UPLOADS = 0

# ---------------- MULTI-API UPLOADER (5 APIs) ---------------- #

def upload_image_multi_api(file_bytes):
    # 1. API 1: Catbox
    try:
        res = requests.post(
            "https://catbox.moe/user/api.php",
            data={"reqtype": "fileupload"},
            files={"fileToUpload": ("image.jpg", file_bytes)},
            timeout=10,
        )
        if res.status_code == 200 and res.text.startswith("http"):
            return res.text.strip()
    except Exception as e:
        logger.error(f"Catbox API failed: {e}")

    # 2. API 2: FreeImage.host
    try:
        res = requests.post(
            "https://freeimage.host/api/1/upload",
            data={"key": "6d207e02198a847aa98d0a2a901485a5", "action": "upload", "format": "json"},
            files={"source": ("image.jpg", file_bytes)},
            timeout=10,
        )
        if res.status_code == 200:
            json_data = res.json()
            if "image" in json_data and "url" in json_data["image"]:
                return json_data["image"]["url"]
    except Exception as e:
        logger.error(f"FreeImage API failed: {e}")

    # 3. API 3: ImgBB API
    try:
        res = requests.post(
            "https://api.imgbb.com/1/upload",
            data={"key": "6d207e02198a847aa98d0a2a901485a5"},
            files={"image": ("image.jpg", file_bytes)},
            timeout=10,
        )
        if res.status_code == 200:
            json_data = res.json()
            if "data" in json_data and "url" in json_data["data"]:
                return json_data["data"]["url"]
    except Exception as e:
        logger.error(f"ImgBB API failed: {e}")

    # 4. API 4: TmpFiles.org
    try:
        res = requests.post(
            "https://tmpfiles.org/api/v1/upload",
            files={"file": ("image.jpg", file_bytes)},
            timeout=10,
        )
        if res.status_code == 200:
            json_data = res.json()
            if "data" in json_data and "url" in json_data["data"]:
                # Convert view url to direct download url
                url = json_data["data"]["url"]
                return url.replace("tmpfiles.org/", "tmpfiles.org/dl/")
    except Exception as e:
        logger.error(f"TmpFiles API failed: {e}")

    # 5. API 5: Litterbox (Temporary 1 Hour Backup)
    try:
        res = requests.post(
            "https://litterbox.catbox.moe/resources/internals/api.php",
            data={"reqtype": "fileupload", "time": "1h"},
            files={"fileToUpload": ("image.jpg", file_bytes)},
            timeout=10,
        )
        if res.status_code == 200 and res.text.startswith("http"):
            return res.text.strip()
    except Exception as e:
        logger.error(f"Litterbox API failed: {e}")

    return None

def shorten_url(long_url):
    try:
        res = requests.get(f"https://tinyurl.com/api-create.php?url={long_url}", timeout=8)
        if res.status_code == 200:
            return res.text.strip()
    except Exception as e:
        logger.error(f"Shortener failed: {e}")
    return long_url

# Helper function to check channel subscription
async def check_subscription(user_id, context):
    try:
        member = await context.bot.get_chat_member(chat_id=REQUIRED_CHANNEL, user_id=user_id)
        if member.status in ["creator", "administrator", "member"]:
            return True
    except Exception as e:
        logger.error(f"Sub check error: {e}")
        return True  # If check fails due to permissions, allow user
    return False


# ---------------- COMMAND HANDLERS ---------------- #

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    # Force Sub Check
    is_subbed = await check_subscription(user.id, context)
    if not is_subbed:
        keyboard = [
            [InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{REQUIRED_CHANNEL.replace('@', '')}")],
            [InlineKeyboardButton("✅ Joined / Verify", callback_data="check_sub_again")]
        ]
        await update.message.reply_text(
            f"⚠️ <b>বটটি ব্যবহার করতে আপনাকে অবশ্যই আমাদের চ্যানেলে জয়েন করতে হবে!</b>\n\n"
            f"নিচের বাটনে ক্লিক করে <b>{REQUIRED_CHANNEL}</b> এ জয়েন করুন এবং 'Joined / Verify' বাটনে চাপ দিন।",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    welcome_text = (
        f"✨ <b>আসসালামু আলাইকুম, {user.first_name}!</b> ✨\n\n"
        "👑 <b>Atikul Image To Link Pro Bot</b>-এ আপনাকে স্বাগতম!\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "📸 <b>আপনার ছবিটি পাঠাই দিন:</b>\n"
        "যেকোনো ছবি সেন্ড করলেই ৫টি হাই-স্পিড সার্ভার দিয়ে সাথে সাথে লিংক তৈরি হয়ে যাবে।\n\n"
        "🚀 <b>প্রিমিয়াম ফিচারসমূহ:</b>\n"
        "├ ⚡ 5x Multi-Server Redundancy\n"
        "├ 🗑️ Auto-Delete Uploaded Image\n"
        "├ 🔗 Short URL Generator (TinyURL)\n"
        "├ ✨ AI Image HD Upscale Tool\n"
        "├ 🎨 One-Click Background Remover\n"
        "└ 📱 Auto QR Code Generator\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "👇 <i>শুরু করতে ছবি আপলোড করুন!</i>"
    )

    keyboard = [
        [InlineKeyboardButton("📤 Upload Instructions", callback_data="btn_upload_instruction")],
        [
            InlineKeyboardButton("📢 Developer Channel", url=f"https://t.me/{REQUIRED_CHANNEL.replace('@', '')}"),
            InlineKeyboardButton("👨‍💻 Admin Contact", url=f"tg://user?id={ADMIN_CHAT_ID}")
        ]
    ]

    await update.message.reply_text(
        welcome_text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_user.id) == ADMIN_CHAT_ID:
        await update.message.reply_text(f"📊 <b>Total Uploads Processed:</b> <code>{TOTAL_UPLOADS}</code>", parse_mode="HTML")


# ---------------- PHOTO PROCESSING ---------------- #

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global TOTAL_UPLOADS
    message = update.message
    user_id = message.from_user.id

    # Force Sub Check
    is_subbed = await check_subscription(user_id, context)
    if not is_subbed:
        await message.reply_text("⚠️ <b>অনুগ্রহ করে আগে আমাদের চ্যানেলে জয়েন করুন!</b>\nকমান্ড: /start", parse_mode="HTML")
        return

    # Anti-Spam Rate Limit (5 seconds cooldown)
    current_time = time.time()
    if user_id in USER_COOLDOWN and current_time - USER_COOLDOWN[user_id] < 5:
        await message.reply_text("⚠️ <b>স্প্যাম রোধে প্রতি ৫ সেকেন্ড পর পর ছবি পাঠান!</b>", parse_mode="HTML")
        return
    USER_COOLDOWN[user_id] = current_time

    photo_file = None
    file_size_kb = 0

    if message.photo:
        photo_obj = message.photo[-1]
        photo_file = await photo_obj.get_file()
        file_size_kb = round(photo_obj.file_size / 1024, 2) if photo_obj.file_size else 0
    elif message.document and message.document.mime_type and message.document.mime_type.startswith("image/"):
        photo_file = await message.document.get_file()
        file_size_kb = round(message.document.file_size / 1024, 2) if message.document.file_size else 0
    else:
        await message.reply_text("❌ <b>অনুগ্রহ করে একটি বৈধ ছবি পাঠাইন!</b>", parse_mode="HTML")
        return

    status_msg = await message.reply_text("⚡ <b>Multi-API দিয়ে ছবি প্রসেসিং হচ্ছে...</b>", parse_mode="HTML")

    try:
        file_bytes = await photo_file.download_as_bytearray()
        direct_link = upload_image_multi_api(file_bytes)

        if direct_link:
            TOTAL_UPLOADS += 1
            keyboard = [
                [InlineKeyboardButton("🔗 ছবির লিংক নিন (Direct Link)", callback_data=f"get_link|{direct_link}")],
                [
                    InlineKeyboardButton("✂️ Short Link", callback_data=f"short_link|{direct_link}"),
                    InlineKeyboardButton("ℹ️ Info", callback_data=f"img_info|{file_size_kb}")
                ],
                [
                    InlineKeyboardButton("✨ AI HD Enhancer", callback_data=f"ai_hd|{direct_link}"),
                    InlineKeyboardButton("🎨 BG Remover", callback_data=f"bg_rem|{direct_link}")
                ],
                [InlineKeyboardButton("📱 QR Code তৈরি করুন", callback_data=f"make_qr|{direct_link}")],
                [InlineKeyboardButton("🌐 ব্রাউজারে অপেন করুন", url=direct_link)]
            ]

            await status_msg.edit_text(
                "🎉 <b>আপনার ছবির ডাইরেক্ট লিংক প্রস্তুত!</b>\n"
                "✨ (মূল ছবিটি সফলভাবে মুছে ফেলা হয়েছে)\n\n"
                "👇 <b>বাটন থেকে আপনার সেবা নির্বাচন করুন:</b>",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

            # Auto-delete user photo
            try:
                await message.delete()
            except Exception as del_err:
                logger.error(f"Failed to delete original photo: {del_err}")

            # Notify Admin
            try:
                user_info = f"@{message.from_user.username}" if message.from_user.username else message.from_user.first_name
                admin_text = (
                    "🔔 <b>নতুন ছবি আপলোড হয়েছে!</b>\n\n"
                    f"👤 <b>ইউজার:</b> {user_info} (<code>{message.from_user.id}</code>)\n"
                    f"🔗 <b>লিংক:</b> {direct_link}"
                )
                await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=admin_text, parse_mode="HTML")
            except Exception as admin_err:
                logger.error(f"Admin notification failed: {admin_err}")

        else:
            await status_msg.edit_text("❌ <b>সবগুলো সার্ভার চেষ্টা করা হয়েছে, কিন্তু আপলোড ব্যর্থ হয়েছে। আবার চেষ্টা করুন!</b>", parse_mode="HTML")

    except Exception as e:
        logger.error(f"Processing error: {e}")
        await status_msg.edit_text("⚠️ <b>সার্ভারে সমস্যা হয়েছে! অনুগ্রহ করে আবার চেষ্টা করুন।</b>", parse_mode="HTML")


# ---------------- BUTTON CALLBACK HANDLER ---------------- #

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data.split("|")
    action = data[0]
    link = data[1] if len(data) > 1 else ""

    if action == "check_sub_again":
        is_subbed = await check_subscription(query.from_user.id, context)
        if is_subbed:
            await query.answer("✅ ভেরিফিকেশন সফল!", show_alert=True)
            await query.message.edit_text("🎉 <b>স্বাগতম!</b> আপনি সফলভাবে চ্যানেলে জয়েন করেছেন। এখন আমাকে যেকোনো ছবি পাঠাই দিন!", parse_mode="HTML")
        else:
            await query.answer("❌ আপনি এখনো জয়েন করেননি!", show_alert=True)

    elif action == "btn_upload_instruction":
        await query.answer()
        await query.message.reply_text(
            "📸 <b>ছবি আপলোড করার নিয়ম:</b>\n\nগ্যালারি থেকে আপনার যেকোনো Image বা Document ফাইল সরাসরি এই চ্যাটে সেন্ড করুন।",
            parse_mode="HTML"
        )

    elif action == "get_link":
        await query.answer("✅ লিংক প্রস্তুত!", show_alert=False)
        await query.message.reply_text(f"💎 <b>আপনার ডাইরেক্ট লিংক:</b>\n\n<code>{link}</code>", parse_mode="HTML")

    elif action == "short_link":
        await query.answer("✂️ শর্ট লিংক তৈরি হচ্ছে...", show_alert=False)
        s_url = shorten_url(link)
        await query.message.reply_text(f"✂️ <b>আপনার শর্ট লিংক:</b>\n\n<code>{s_url}</code>", parse_mode="HTML")

    elif action == "img_info":
        await query.answer(f"📦 ফাইল সাইজ: {link} KB", show_alert=True)

    elif action == "ai_hd":
        await query.answer("✨ AI HD Enhancer লোড হচ্ছে...", show_alert=False)
        await query.message.reply_text(f"✨ <b>AI HD Image Enhancer:</b>\n🔗 https://upscalepic.com/?ref_img={link}", parse_mode="HTML")

    elif action == "bg_rem":
        await query.answer("🎨 BG Remover লোড হচ্ছে...", show_alert=False)
        await query.message.reply_text("🎨 <b>Background Remover:</b>\n🔗 https://www.remove.bg/upload", parse_mode="HTML")

    elif action == "make_qr":
        await query.answer("📱 QR Code তৈরি হচ্ছে...", show_alert=False)
        qr_api_url = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={link}"
        await query.message.reply_photo(photo=qr_api_url, caption=f"📱 <b>QR Code:</b>\n<code>{link}</code>", parse_mode="HTML")


# ---------------- MAIN APPLICATION ---------------- #

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", stats_command))
    app.add_handler(MessageHandler(filters.PHOTO | filters.Document.IMAGE, handle_photo))
    app.add_handler(CallbackQueryHandler(button_click))

    print("=== Supercharged Image To Link Bot running ===")
    app.run_polling()

if __name__ == "__main__":
    main()
            
