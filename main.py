from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import re

users = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.chat_id
    users[user_id] = {"name": update.message.from_user.first_name, "text": ""}
    await update.message.reply_text(
        f"Salam {users[user_id]['name']}! 👋\nBu VibeMatchBot-dur — maraqlarına uyğun insanlarla tanış olmaq üçün.\n\nİndi maraqlarını yaz (məsələn: 'Mən kitab oxumağı sevirəm, hobbilərim musiqi və idmandır.')."
    )

async def add_interest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.chat_id
    if user_id not in users:
        await update.message.reply_text("Əvvəl /start yaz.")
        return

    users[user_id]["text"] = update.message.text.lower()
    await update.message.reply_text("✅ Maraqlar yadda saxlanıldı! Uyğun insan tapmaq üçün /findmatch yaz.")

from nltk.stem.snowball import SnowballStemmer
stemmer = SnowballStemmer("azerbaijani")

def preprocess(text):
    words = re.findall(r'\w+', text.lower())
    # Hər sözü kökünə sal
    stems = [stemmer.stem(w) for w in words]
    return set(stems)

def match_score(text1, text2):
    words1 = preprocess(text1)
    words2 = preprocess(text2)
    if not words1 or not words2:
        return 0
    score = len(words1 & words2) / len(words1 | words2)
    return round(score * 100, 2)


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

app = ApplicationBuilder().token("7175581321:AAFwo1JvMeWmfZ0VHzL--5KS8b9bpBQkY5Q").build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, add_interest))
app.add_handler(CommandHandler("findmatch", find_match))

app.run_polling()
