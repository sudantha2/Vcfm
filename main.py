
import asyncio
import os
from pyrogram import Client, filters
from pyrogram.types import Message
from pymongo import MongoClient
from pytgcalls import PyTgCalls
from pytgcalls.types import AudioPiped
import requests
import logging
from keep_alive import keep_alive

# Configure logging
logging.basicConfig(level=logging.INFO)

# Get environment variables
API_ID = 24140233
API_HASH = "d81fccd3356451ff20e577a5192e5782"
BOT_TOKEN = "7695188163:AAFLPNDuxRIJkEkUMpG_Qijfi7-OoILOMzM"
OWNER_ID = 5132917762
MONGO_URI = "mongodb+srv://VcPlayer:Sudantha123@cluster1.cqjy4g5.mongodb.net/?retryWrites=true&w=majority&appName=Cluster1"
SESSION_STRING = "BQFwWckAkVTWSuGuyozXMYQfOxuCxo2fthsVol4raSEdPzz9k56C9MjykE83fvnvXWLJN0P8qTGcNkdYITRDcKZBK2Avf-XoYljtg2G2wq-NZsZtp6bxG7Vq0GtDrDcHubD7_knc0VAtka8SuaDZSfmVkkydrsp5gmfIqlcVDhj66ylHQdP7FlAr5QD7-BCnPCmKwufQ8xlYlXK5BdiECJIgsQvkgq4WjuCB9J29hhlqSl9QMGC4aiwbFbF5CAi6uBCOieQksCHimxAfl2u_hWm9xw5yM4hgP8rE1ocRUhLwz7wO2a1FcmLpvG8rE0-mA58yvN-hZS1Ht2wiWAmO5Y-jMZgsQgAAAAHWkUM3AA"

# Initialize MongoDB
mongo_client = MongoClient(MONGO_URI)
db = mongo_client['fm_bot']
streams_collection = db['streams']

# Initialize bot
bot = Client(
    "fm_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# Initialize userbot
userbot = Client(
    "fm_userbot",
    api_id=API_ID,
    api_hash=API_HASH,
    session_string=os.environ.get('SESSION_STRING', '')
)

# Initialize PyTgCalls
pytgcalls = PyTgCalls(userbot)

# Active streams storage
active_streams = {}

@bot.on_message(filters.command("start"))
async def start_handler(client: Client, message: Message):
    await message.reply_text(
        "ðŸŽµ **FM Player Bot**\n\n"
        "Commands:\n"
        "â€¢ `/playfm <fm_name>` - Play FM in voice chat\n"
        "â€¢ `/stopfm` - Stop current FM\n"
        "â€¢ `/listfm` - List available FM stations\n\n"
        "Owner commands (private only):\n"
        "â€¢ `/fm <fm_name> <stream_url>` - Add FM station"
    )

@bot.on_message(filters.command("fm") & filters.private & filters.user(OWNER_ID))
async def add_fm_handler(client: Client, message: Message):
    try:
        parts = message.text.split(' ', 2)
        if len(parts) < 3:
            await message.reply_text("âŒ Usage: `/fm <fm_name> <stream_url>`")
            return
        
        fm_name = parts[1].lower()
        stream_url = parts[2]
        
        # Validate stream URL
        try:
            response = requests.head(stream_url, timeout=10)
            if response.status_code != 200:
                await message.reply_text("âŒ Invalid stream URL or server is down")
                return
        except:
            await message.reply_text("âŒ Cannot validate stream URL")
            return
        
        # Save to database
        streams_collection.update_one(
            {"name": fm_name},
            {"$set": {"name": fm_name, "url": stream_url}},
            upsert=True
        )
        
        await message.reply_text(f"âœ… FM station **{fm_name}** added successfully!")
        
    except Exception as e:
        await message.reply_text(f"âŒ Error: {str(e)}")

@bot.on_message(filters.command("playfm"))
async def play_fm_handler(client: Client, message: Message):
    try:
        if not message.chat.type in ['group', 'supergroup']:
            await message.reply_text("âŒ This command only works in groups!")
            return
        
        parts = message.text.split(' ', 1)
        if len(parts) < 2:
            await message.reply_text("âŒ Usage: `/playfm <fm_name>`")
            return
        
        fm_name = parts[1].lower()
        
        # Get stream URL from database
        stream_data = streams_collection.find_one({"name": fm_name})
        if not stream_data:
            await message.reply_text(f"âŒ FM station **{fm_name}** not found!")
            return
        
        stream_url = stream_data['url']
        chat_id = message.chat.id
        
        # Check if userbot is in the chat
        try:
            await userbot.get_chat_member(chat_id, "me")
        except:
            await message.reply_text("âŒ Please add the userbot to this chat first!")
            return
        
        # Stop current stream if playing
        if chat_id in active_streams:
            try:
                await pytgcalls.leave_group_call(chat_id)
            except:
                pass
        
        # Join voice chat and play stream
        await pytgcalls.join_group_call(
            chat_id,
            AudioPiped(stream_url)
        )
        
        active_streams[chat_id] = {
            'fm_name': fm_name,
            'stream_url': stream_url
        }
        
        await message.reply_text(f"ðŸŽµ Now playing **{fm_name}** in voice chat!")
        
    except Exception as e:
        await message.reply_text(f"âŒ Error: {str(e)}")

@bot.on_message(filters.command("stopfm"))
async def stop_fm_handler(client: Client, message: Message):
    try:
        chat_id = message.chat.id
        
        if chat_id not in active_streams:
            await message.reply_text("âŒ No FM is currently playing!")
            return
        
        await pytgcalls.leave_group_call(chat_id)
        del active_streams[chat_id]
        
        await message.reply_text("â¹ï¸ FM stream stopped!")
        
    except Exception as e:
        await message.reply_text(f"âŒ Error: {str(e)}")

@bot.on_message(filters.command("listfm"))
async def list_fm_handler(client: Client, message: Message):
    try:
        streams = list(streams_collection.find({}))
        
        if not streams:
            await message.reply_text("âŒ No FM stations available!")
            return
        
        fm_list = "ðŸŽµ **Available FM Stations:**\n\n"
        for stream in streams:
            fm_list += f"â€¢ **{stream['name']}**\n"
        
        fm_list += f"\nTotal: {len(streams)} stations"
        await message.reply_text(fm_list)
        
    except Exception as e:
        await message.reply_text(f"âŒ Error: {str(e)}")

@userbot.on_message(filters.command("ping"))
async def userbot_ping(client: Client, message: Message):
    await message.reply_text("ðŸ¤– Userbot is online!")

async def main():
    print("ðŸš€ Starting FM Player Bot...")
    
    # Start keep_alive server
    keep_alive()
    
    # Start userbot
    await userbot.start()
    print("âœ… Userbot started")
    
    # Start PyTgCalls
    await pytgcalls.start()
    print("âœ… PyTgCalls started")
    
    # Start main bot
    await bot.start()
    print("âœ… Main bot started")
    
    print("ðŸŽµ FM Player Bot is now running!")
    
    # Keep the bot running
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
