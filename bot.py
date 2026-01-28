#!/usr/bin/env python3
"""
KawaII5Bot - FIXED for Render.com
"""

import os
import re
import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message
import yt_dlp
from urllib.parse import urlparse
from pathlib import Path

# ==================== SAFE STARTUP ====================
BOT_TOKEN = os.getenv("8209355827:AAHfJ8ew5YmTyAu4VoRrj2T3UZBq2m1ZrQM")
API_ID = os.getenv("37753288")
API_HASH = os.getenv("68f5e26ac13f659083814b1f032ffc29")

print("🔍 Checking ENV vars...")
print(f"BOT_TOKEN: {'✅' if BOT_TOKEN else '❌'}")
print(f"API_ID: {'✅' if API_ID else '❌'}")
print(f"API_HASH: {'✅' if API_HASH else '❌'}")

if not all([BOT_TOKEN, API_ID, API_HASH]):
    print("❌ Fix ENV vars in Render Dashboard!")
    exit(1)

API_ID = int(API_ID)

app = Client("kawaii_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

COOKIES_FILE = "cookies.txt"
downloads_dir = "downloads"
pending_urls = {}

VIDEO_QUALITIES = {
    "4k": "best[height>=2160]",
    "2k": "best[height>=1440]", 
    "fhd": "best[height<=1080]",
    "hd": "best[height<=720]",
    "sd": "best[height<=480]",
    "low": "best[height<=360]"
}

def is_valid_url(url: str) -> bool:
    parsed = urlparse(url)
    return bool(parsed.scheme and parsed.netloc and any(
        platform in parsed.netloc.lower() for platform in 
        ['youtube', 'youtu.be', 'instagram', 'facebook', 'tiktok', 'twitter', 'x.com']
    ))

# ==================== COMMANDS ====================
@app.on_message(filters.command("start"))
async def start(client, message: Message):
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🎬 VIDEO", callback_data="video_menu")],
        [InlineKeyboardButton("🎵 AUDIO", callback_data="audio_menu")],
        [InlineKeyboardButton("🍪 COOKIES", callback_data="cookies_help")]
    ])
    await message.reply_text(
        "🎥 **KawaII5Bot** - 1000+ Platforms!\n\n"
        "**YouTube • Instagram • TikTok • Facebook**\n\n"
        "Send video URL! 👇",
        reply_markup=kb,
        disable_web_page_preview=True
    )

@app.on_message(filters.text & ~filters.command("start"))
async def process_url(client, message: Message):
    url = message.text.strip()
    
    if not is_valid_url(url):
        return await message.reply("❌ **Invalid URL!**\nSend YouTube/Instagram/etc link")
    
    chat_id = message.chat.id
    pending_urls[chat_id] = {"url": url}
    
    video_kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("4K 🎥", callback_data="v_4k"), InlineKeyboardButton("2K 📺", callback_data="v_2k")],
        [InlineKeyboardButton("1080p ✨", callback_data="v_fhd"), InlineKeyboardButton("720p ✅", callback_data="v_hd")],
        [InlineKeyboardButton("480p 📱", callback_data="v_sd"), InlineKeyboardButton("360p 📲", callback_data="v_low")],
        [InlineKeyboardButton("🔄 NEW", callback_data="clear")]
    ])
    
    await message.reply_text(
        f"🔗 **{url[:50]}...**\n\n**🎬 VIDEO Quality:**",
        reply_markup=video_kb
    )

# ==================== CALLBACKS ====================
@app.on_callback_query()
async def callback_handler(client, callback: CallbackQuery):
    data = callback.data
    chat_id = callback.message.chat.id
    
    if chat_id not in pending_urls:
        return await callback.answer("Send URL first!")
    
    url_data = pending_urls[chat_id]
    url = url_data["url"]
    
    if data == "clear":
        pending_urls.pop(chat_id, None)
        return await callback.edit_message_text("🔄 Ready!")
    
    if data == "cookies_help":
        return await callback.edit_message_text(
            "**🍪 Private Videos:**\n"
            "1. Chrome → Login IG/FB\n"
            "2. `Get cookies.txt` extension\n"
            "3. Export cookies.txt → Upload\n"
            "✅ Private works!"
        )
    
    await callback.edit_message_text("⏳ Downloading...")
    
    try:
        if data.startswith("v_"):
            await download_video(callback, url, data[2:])
        elif data.startswith("a_"):
            await download_audio(callback, url, data[2:])
    except Exception as e:
        await callback.edit_message_text(f"❌ Error: {str(e)}")

async def download_video(callback: CallbackQuery, url: str, quality: str):
    Path(downloads_dir).mkdir(exist_ok=True)
    
    ydl_opts = {
        'format': f'{VIDEO_QUALITIES[quality]}/best',
        'outtmpl': f'{downloads_dir}/%(title)s_[{quality}]%(ext)s',
        'cookiefile': COOKIES_FILE if os.path.exists(COOKIES_FILE) else None,
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        
        files = os.listdir(downloads_dir)
        vid_file = next(f for f in files if f'{quality}]' in f)
        file_path = os.path.join(downloads_dir, vid_file)
        
        await callback.message.reply_video(
            video=file_path,
            caption=f"✅ **{quality.upper()}**\n{info.get('title', '')[:50]}"
        )
    
    os.remove(file_path)
    await callback.edit_message_text("✅ Done! 🎬")

async def download_audio(callback: CallbackQuery, url: str, bitrate: str):
    Path(downloads_dir).mkdir(exist_ok=True)
    
    ydl_opts = {
        'format': 'bestaudio',
        'outtmpl': f'{downloads_dir}/%(title)s_[{bitrate}]%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': bitrate.rstrip('k'),
        }],
        'cookiefile': COOKIES_FILE if os.path.exists(COOKIES_FILE) else None,
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        
        files = os.listdir(downloads_dir)
        audio_file = next(f for f in files if f.endswith('.mp3'))
        file_path = os.path.join(downloads_dir, audio_file)
        
        await callback.message.reply_audio(
            audio=file_path,
            caption=f"✅ **{bitrate} MP3**\n{info.get('title', '')}"
        )
    
    os.remove(file_path)
    await callback.edit_message_text("✅ Done! 🎵")

if __name__ == "__main__":
    print("🚀 Starting KawaII5Bot...")
    os.makedirs(downloads_dir, exist_ok=True)
    app.run()
