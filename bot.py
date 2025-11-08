import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
import asyncpg

BOT_TOKEN = "8488952025:AAHD9B3_BgBKX8gpFRVRkjLTWaFt1lToLwM"
DATABASE_URL = "postgresql://postgres:zulfeli4@db.ycxdqjuetazigtbjpvwe.supabase.co:5432/postgres?sslmode=require"

async def create_db_pool():
    return await asyncpg.create_pool(DATABASE_URL)

dp = Dispatcher()

@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(
        "Salam! 👋\n"
        "Profil yaratmaq üçün adını yaz:"
    )
    dp.fsm_data[message.from_user.id] = {"step": "name"}

@dp.message()
async def collect_data(message: types.Message):
    user_id = message.from_user.id
    if user_id not in dp.fsm_data:
        return await message.answer("Zəhmət olmasa /start yaz.")

    step = dp.fsm_data[user_id]["step"]
    if step == "name":
        dp.fsm_data[user_id]["name"] = message.text
        dp.fsm_data[user_id]["step"] = "age"
        return await message.answer("Yaşını yaz:")
    if step == "age":
        try:
            dp.fsm_data[user_id]["age"] = int(message.text)
        except ValueError:
            return await message.answer("Yaş rəqəm olmalıdır. Yenidən yaz:")
        dp.fsm_data[user_id]["step"] = "city"
        return await message.answer("Şəhər:")
    if step == "city":
        dp.fsm_data[user_id]["city"] = message.text
        dp.fsm_data[user_id]["step"] = "gender"
        return await message.answer("Cinsin? (Kişi/Qadın)")
    if step == "gender":
        dp.fsm_data[user_id]["gender"] = message.text
        dp.fsm_data[user_id]["step"] = "target_gender"
        return await message.answer("Kiminlə tanış olmaq istəyirsən? (Kişi/Qadın)")
    if step == "target_gender":
        dp.fsm_data[user_id]["target_gender"] = message.text
        dp.fsm_data[user_id]["step"] = "bio"
        return await message.answer("Qısa bio yaz:")
    if step == "bio":
        dp.fsm_data[user_id]["bio"] = message.text
        dp.fsm_data[user_id]["step"] = "media"
        return await message.answer("1–3 şəkil və ya video göndər (ard-arda). Bitirəndə 'bitdi' yaz.")
    if step == "media":
        if "media" not in dp.fsm_data[user_id]:
            dp.fsm_data[user_id]["media"] = []
        if message.text and message.text.lower() == "bitdi":
            data = dp.fsm_data[user_id]
            media_list = data["media"]
            media1 = media_list[0] if len(media_list) > 0 else None
            media2 = media_list[1] if len(media_list) > 1 else None
            media3 = media_list[2] if len(media_list) > 2 else None
            pool = await create_db_pool()
            async with pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO profiles (user_id, name, age, city, gender, target_gender, bio, media1, media2, media3)
                    VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10)
                    ON CONFLICT (user_id) DO UPDATE SET
                    name=$2, age=$3, city=$4, gender=$5, target_gender=$6,
                    bio=$7, media1=$8, media2=$9, media3=$10
                """,
                user_id, data["name"], data["age"], data["city"],
                data["gender"], data["target_gender"], data["bio"],
                media1, media2, media3)
            await message.answer("✅ Profil yadda saxlanıldı!")
            del dp.fsm_data[user_id]
            return
        file_id = None
        if message.photo:
            file_id = message.photo[-1].file_id
        elif message.video:
            file_id = message.video.file_id
        if file_id:
            dp.fsm_data[user_id]["media"].append(file_id)
            return await message.answer("✅ Qəbul edildi. Daha varsa göndər, yoxsa 'bitdi' yaz.")
        return await message.answer("Şəkil və ya video göndər, yaxud 'bitdi' yaz.")

async def main():
    bot = Bot(token=BOT_TOKEN)
    dp.fsm_data = {}
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
