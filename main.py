from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
import re

# ------------------------------
# Məlumatlar və sinonimlər
# ------------------------------
users = {}
pending_profiles = {}

synonyms = {
    "kitab": ["kitablar", "oxumaq", "ədəbiyyat", "roman"],
    "film": ["kino", "serial", "filmlər", "baxmaq"],
    "musiqi": ["mahnı", "mahnılar", "dinləmək", "konsert"],
    "idman": ["futbol", "basketbol", "üzgüçülük", "voleybol", "fitnes", "gym"],
    "səyahət": ["travel", "gezi", "səfər", "turizm"],
    "alış": ["shopping", "market", "mağaza"],
    "oyun": ["game", "gta", "valorant", "oyunlar"],
    "trading": ["forex", "investisiya", "kripto"],
}

def simple_stem(word):
    endings = ["lar", "lər", "ın", "in", "un", "ün", "ı", "i", "u", "ü", "da", "də", "dan", "dən", "la", "lə"]
    for end in endings:
        if word.endswith(end) and len(word) > len(end) + 1:
            return word[:-len(end)]
    return word

def preprocess(text):
    words = re.findall(r'\w+', text.lower())
    result = set()
    for w in words:
        root = simple_stem(w)
        found = False
        for key, vals in synonyms.items():
            if root == key or root in vals:
                result.add(key)
                found = True
                break
        if not found:
            result.add(root)
    return result

def match_score(text1, text2):
    set1 = preprocess(text1)
    set2 = preprocess(text2)
    if not set1 or not set2:
        return 0
    score = len(set1 & set2) / len(set1 | set2)
    return round(score * 100, 2)

# ------------------------------
# Profil yaratma prosesi
# ------------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("📝 Profil yarat", callback_data="create_profile")]]
    await update.message.reply_text(
        "Salam! 👋 Bu VibeMatchBot-dur.\nİnsanlarla maraqlarına görə tanış olmaq istəyirsənsə, əvvəl profilini yaradaq:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.message.chat_id
    await query.answer()

    if query.data == "create_profile":
        pending_profiles[user_id] = {}
        await query.edit_message_text("Adını yaz:")
    elif query.data in ["male", "female"]:
        pending_profiles[user_id]["gender"] = "Kişi" if query.data == "male" else "Qadın"
        await query.edit_message_text("📍 Şəhərini seç:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Bakı", callback_data="city_Bakı")],
                [InlineKeyboardButton("Gəncə", callback_data="city_Gəncə")],
                [InlineKeyboardButton("Sumqayıt", callback_data="city_Sumqayıt")],
                [InlineKeyboardButton("Digər", callback_data="city_Digər")]
            ])
        )
    elif query.data.startswith("age_"):
        pending_profiles[user_id]["age"] = query.data.split("_")[1]
        await query.edit_message_text(
            "🚻 Cinsini seç:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("👦 Kişi", callback_data="male"), InlineKeyboardButton("👧 Qadın", callback_data="female")]
            ])
        )
    elif query.data.startswith("city_"):
        pending_profiles[user_id]["city"] = query.data.split("_")[1]
        await query.edit_message_text("💬 Maraqlarını yaz (vergüllə ayır):")
    else:
        await query.edit_message_text("Naməlum seçim.")

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.chat_id

    if user_id in pending_profiles and "name" not in pending_profiles[user_id]:
        pending_profiles[user_id]["name"] = update.message.text
        await update.message.reply_text(
            "🎂 Yaş aralığını seç:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("18-25", callback_data="age_18-25")],
                [InlineKeyboardButton("26-35", callback_data="age_26-35")],
                [InlineKeyboardButton("36+", callback_data="age_36+")],
            ])
        )
    elif user_id in pending_profiles and "age" in pending_profiles[user_id] and "gender" in pending_profiles[user_id] and "city" not in pending_profiles[user_id]:
        pass
    elif user_id in pending_profiles and "city" in pending_profiles[user_id] and "interests" not in pending_profiles[user_id]:
        pending_profiles[user_id]["interests"] = update.message.text
        await update.message.reply_text("📸 İndi profil şəklini göndər:")
    elif user_id in pending_profiles and "interests" in pending_profiles[user_id] and "photo_id" not in pending_profiles[user_id]:
        await update.message.reply_text("Zəhmət olmasa şəkil göndər (foto kimi, sənəd kimi yox).")
    else:
        await update.message.reply_text("Əvvəl profilini yaratmaq üçün /start yaz.")

async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.chat_id
    if user_id in pending_profiles and "photo_id" not in pending_profiles[user_id]:
        photo = update.message.photo[-1]
        pending_profiles[user_id]["photo_id"] = photo.file_id
        users[user_id] = pending_profiles[user_id]
        del pending_profiles[user_id]

        await update.message.reply_text("✅ Profil yaradıldı! İndi /findmatch yaza bilərsən.")
    else:
        await update.message.reply_text("Əvvəl profil yaratmaq lazımdır. /start yaz.")

# ------------------------------
# Match tapmaq
# ------------------------------
async def find_match(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.chat_id
    if user_id not in users:
        await update.message.reply_text("Əvvəl profil yarat. /start yaz.")
        return

    user = users[user_id]
    best_match = None
    best_score = 0

    for uid, data in users.items():
        if uid == user_id:
            continue
        if data["gender"] == user["gender"]:  # əks cinsləri göstərəcək
            continue
        if data["city"] != user["city"]:
            continue

        score = match_score(user["interests"], data["interests"])
        if score > best_score:
            best_match = uid
            best_score = score

    if best_match and best_score > 30:
        match_user = users[best_match]
        caption = (
            f"🎯 Match tapıldı!\n\n"
            f"👤 Ad: {match_user['name']}\n"
            f"🎂 Yaş: {match_user['age']}\n"
            f"🚻 Cins: {match_user['gender']}\n"
            f"📍 Şəhər: {match_user['city']}\n"
            f"💬 Maraqlar: {match_user['interests']}\n"
            f"❤️ Uyğunluq: {best_score}%"
        )
        await update.message.reply_photo(photo=match_user["photo_id"], caption=caption)
    else:
        await update.message.reply_text("Hələ uyğun insan tapılmadı 😔")

# ------------------------------
# Botu işə sal
# ------------------------------
app = ApplicationBuilder().token("BURAYA_SƏNİN_TELEGRAM_BOT_TOKENİNİ_YAZ").build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(button_handler))
app.add_handler(CommandHandler("findmatch", find_match))
app.add_handler(MessageHandler(filters.PHOTO, photo_handler))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

app.run_polling()
