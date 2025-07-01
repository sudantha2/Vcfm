import os
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pytgcalls import PyTgCalls, idle
from pytgcalls.types.input_stream import InputStream, InputAudioStream
from pymongo import MongoClient
from keep_alive import keep_alive

# --- Configurations ---
API_ID = 24140233
API_HASH = "d81fccd3356451ff20e577a5192e5782"
BOT_TOKEN = "7695188163:AAFLPNDuxRIJkEkUMpG_Qijfi7-OoILOMzM"
OWNER_ID = 5132917762
MONGO_URI = "mongodb+srv://VcPlayer:Sudantha123@cluster1.cqjy4g5.mongodb.net/?retryWrites=true&w=majority&appName=Cluster1"
SESSION_STRING = "BQFwWckAkVTWSuGuyozXMYQfOxuCxo2fthsVol4raSEdPzz9k56C9MjykE83fvnvXWLJN0P8qTGcNkdYITRDcKZBK2Avf-XoYljtg2G2wq-NZsZtp6bxG7Vq0GtDrDcHubD7_knc0VAtka8SuaDZSfmVkkydrsp5gmfIqlcVDhj66ylHQdP7FlAr5QD7-BCnPCmKwufQ8xlYlXK5BdiECJIgsQvkgq4WjuCB9J29hhlqSl9QMGC4aiwbFbF5CAi6uBCOieQksCHimxAfl2u_hWm9xw5yM4hgP8rE1ocRUhLwz7wO2a1FcmLpvG8rE0-mA58yvN-hZS1Ht2wiWAmO5Y-jMZgsQgAAAAHWkUM3AA"

# Clients
bot = Client("fm_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
user = Client("userbot", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)
call = PyTgCalls(user)

# DB setup
mongo = MongoClient(MONGO_URI)
db = mongo["fm_bot"]
stations = db["stations"]

# Start everything
@bot.on_message(filters.command("start") & filters.private)
async def start(_, m: Message):
    await m.reply("🎵 Welcome to FM Player Bot!\nUse /playfm <name> to play an FM station in VC.")

# Add FM station (OWNER only)
@bot.on_message(filters.command("fm") & filters.user(OWNER_ID))
async def add_station(_, m: Message):
    try:
        _, name, url = m.text.split(None, 2)
        stations.update_one({"name": name.lower()}, {"$set": {"url": url}}, upsert=True)
        await m.reply(f"✅ Station '{name}' added to database.")
    except:
        await m.reply("❌ Usage: /fm <name> <direct_stream_url>")

# Play FM in VC
@bot.on_message(filters.command("playfm") & filters.group)
async def play_fm(_, m: Message):
    args = m.text.split(None, 1)
    if len(args) != 2:
        await m.reply("❌ Usage: /playfm <station_name>")
        return
    name = args[1].lower()
    fm = stations.find_one({"name": name})
    if not fm:
        await m.reply("🚫 Station not found.")
        return
    try:
        chat_id = m.chat.id
        await user.join_chat(chat_id)
        await call.join_group_call(
            chat_id,
            InputStream(InputAudioStream(fm['url']))
        )
        await m.reply(f"📻 Playing '{name}' in VC now.")
    except Exception as e:
        await m.reply(f"❌ Error: {e}")

# Stop command
@bot.on_message(filters.command("stop") & filters.group)
async def stop(_, m: Message):
    try:
        await call.leave_group_call(m.chat.id)
        await m.reply("🛑 Stopped FM playback.")
    except:
        await m.reply("⚠️ Not currently streaming.")

# Start all clients
async def start_all():
    await bot.start()
    await user.start()
    await call.start()
    print("✅ All systems online.")
    await idle()

if name == "main":
    keep_alive()
    import asyncio
    asyncio.run(start_all()
