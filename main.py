from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import re

# ------------------------------
#  Sadə sinonimlər və “mini stemmer”
# ------------------------------
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

# Azərbaycan sonluqlarını silən mini stemmer
def simple_stem(word):
    endings = ["lar", "lər", "ın", "in", "un", "ün", "ı", "i", "u", "ü", "da", "də", "dan", "dən", "la", "lə"]
    for end in endings:
        if word.endswith(end) and len(word) > len(end) + 1:
            return word[:-len(end)]
    return word

# Mətni analiz edib sinonimlərlə bərabərləşdir
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

# Uyğunluq faizi hesabla
def match_score(text1, text2):
    set1 = preprocess(text1)
    set2 = preprocess(text2)
    if not set1 or not set2:
        return 0
    score = len(set1 & set2) / len(set1 | set2)
    return round(score * 100, 2)


# ------------------------------
#  Telegram bot hissəsi
# ------------------------------
users = {}

# /start komandası
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.chat_id
    users[user_id] = {"name": update.message.from_user.first_name, "text": ""}
    await update.message.reply_text(
        f"Salam {users[user_id]['name']}! 👋\n"
        f"Bu VibeMatchBot-dur — maraqlarına uyğun insanlarla tanış olmaq üçün.\n\n"
        f"İndi maraqlarını yaz (məsələn: 'Mən kitab oxumağı sevirəm, hobbilərim musiqi və idmandır.')."
    )

# İstifadəçi maraqlarını qeyd edir
async def add_interest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.chat_id
    if user_id not in users:
        await update.message.reply_text("Əvvəl /start yaz.")
        return

    users[user_id]["text"] = update.message.text
    await update.message.reply_text("✅ Maraqlar yadda saxlanıldı! Uyğun insan tapmaq üçün /findmatch yaz.")

# Uyğun insan tap
async def find_match(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.chat_id
    if user_id not in users or not users[user_id]["text"]:
        await update.message.reply_text("Əvvəl maraqlarını yaz.")
        return

    best_match = None
    best_score = 0

    for uid, data in users.items():
        if uid == user_id or not data["text"]:
            continue
        score = match_score(users[user_id]["text"], data["text"])
        if score > best_score:
            best_match = uid
            best_score = score

    if best_match and best_score > 20:
        name1 = users[user_id]["name"]
        name2 = users[best_match]["name"]
        await update.message.reply_text(f"🎯 {name2} ilə {best_score}% uyğunluq tapıldı!")
        await context.bot.send_message(
            chat_id=best_match,
            text=f"🎯 {name1} ilə {best_score}% uyğunluq tapıldı!"
        )
    else:
        await update.message.reply_text("Hələ uyğun insan tapılmadı 😔")

# Botu işə sal
app = ApplicationBuilder().token("7175581321:AAFwo1JvMeWmfZ0VHzL--5KS8b9bpBQkY5Q").build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, add_interest))
app.add_handler(CommandHandler("findmatch", find_match))

app.run_polling()
