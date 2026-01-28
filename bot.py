import os
import re
import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message
import yt_dlp
from urllib.parse import urlparse

# CONFIG - UPDATE THESE!
BOT_TOKEN = os.getenv("8209355827:AAHfJ8ew5YmTyAu4VoRrj2T3UZBq2m1ZrQM")
API_ID = int(os.getenv("37753288"))
API_HASH = os.getenv("68f5e26ac13f659083814b1f032ffc29")

app = Client("kawaii_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Cookies file (for Instagram/FB login)
COOKIES_FILE = "cookies.txt"

# Global storage
pending_urls = {}
downloads_dir = "downloads"

VIDEO_QUALITIES = {
    "4k": "best[height>=2160]",
    "2k": "best[height>=1440]",
    "fhd": "best[height<=1080]",
    "hd": "best[height<=720]",
    "sd": "best[height<=480]",
    "low": "best[height<=360]"
}

@app.on_message(filters.command("start"))
async def start(client, message: Message):
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🎬 VIDEO DOWNLOAD", callback_data="video_menu")],
        [InlineKeyboardButton("🎵 AUDIO ONLY", callback_data="audio_menu")],
        [InlineKeyboardButton("🍪 COOKIES HELP", callback_data="cookies_help")]
    ])
    await message.reply_text(
        "🎥 **KawaII5Bot** - Ultimate Downloader\n\n"
        "✅ **1000+ Platforms:** YouTube • Instagram • Facebook • TikTok • Twitter\n"
        "🎬 **Qualities:** 4K • 2K • 1080p • 720p • 480p • 360p\n"
        "🎵 **Audio:** 320-64kbps\n\n"
        "**Send any video link!** 👇",
        reply_markup=kb,
        disable_web_page_preview=True
    )

@app.on_message(filters.text & ~filters.command("start"))
async def process_url(client, message: Message):
    url = message.text.strip()
    
    # URL validation
    if not is_valid_url(url):
        return await message.reply("❌ **Invalid URL!**\nUse: `https://...`", parse_mode="markdown")
    
    chat_id = message.chat.id
    pending_urls[chat_id] = {"url": url, "message_id": message.id}
    
    # Video quality buttons
    video_kb = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🎥 4K UHD", callback_data="v_4k"),
            InlineKeyboardButton("📺 2K QHD", callback_data="v_2k")
        ],
        [
            InlineKeyboardButton("✨ 1080p FHD", callback_data="v_fhd"),
            InlineKeyboardButton("✅ 720p HD", callback_data="v_hd")
        ],
        [
            InlineKeyboardButton("📱 480p", callback_data="v_sd"),
            InlineKeyboardButton("📲 360p", callback_data="v_low")
        ],
        [InlineKeyboardButton("🔄 New Link", callback_data="clear")]
    ])
    
    await message.reply_text(
        f"🔗 **URL Ready:** `{url[:50]}...`\n\n"
        "🎬 **Select VIDEO Quality:**",
        reply_markup=video_kb,
        parse_mode="markdown"
    )
    
    # Audio buttons
    audio_kb = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔊 320kbps", callback_data="a_320"),
            InlineKeyboardButton("🎵 256kbps", callback_data="a_256")
        ],
        [
            InlineKeyboardButton("📻 192kbps", callback_data="a_192"),
            InlineKeyboardButton("🔉 128kbps", callback_data="a_128")
        ],
        [InlineKeyboardButton("📡 64kbps", callback_data="a_64")],
        [InlineKeyboardButton("🔄 New Link", callback_data="clear")]
    ])
    
    await message.reply_text("**Or select AUDIO Quality:** 🎵", reply_markup=audio_kb, parse_mode="markdown")

@app.on_callback_query()
async def handle_callback(client, callback: CallbackQuery):
    data = callback.data
    chat_id = callback.message.chat.id
    
    if chat_id not in pending_urls:
        return await callback.edit_message_text("❌ **Send URL first!**")
    
    url_data = pending_urls[chat_id]
    url = url_data["url"]
    
    if data == "clear":
        pending_urls.pop(chat_id, None)
        return await callback.edit_message_text("🔄 **Ready for new URL!** 🎉")
    
    if data == "cookies_help":
        return await callback.edit_message_text(
            "**🍪 Cookies for Private Videos:**\n\n"
            "1. Install: `Browser Cookies` extension\n"
            "2. Login Instagram/Facebook in browser\n"
            "3. Export cookies → Save as `cookies.txt`\n"
            "4. Upload to bot folder\n\n"
            "**Now private videos work!** 🔓"
        )
    
    await callback.edit_message_text("🚀 **Downloading...** ⏳")
    
    try:
        if data.startswith("v_"):
            quality = data[2:]
            await download_video(callback, url, quality)
        elif data.startswith("a_"):
            bitrate = data[2:]
            await download_audio(callback, url, bitrate)
    except Exception as e:
        await callback.edit_message_text(f"❌ **Failed:** `{str(e)}`", parse_mode="markdown")

async def download_video(callback: CallbackQuery, url: str, quality: str):
    os.makedirs(downloads_dir, exist_ok=True)
    
    ydl_opts = {
        'format': f'{VIDEO_QUALITIES[quality]}+bestaudio[ext=m4a]/best[height<=1080]',
        'outtmpl': f'{downloads_dir}/%(title).200s_[{quality}]%(ext)s',
        'merge_output_format': 'mp4',
        'cookiefile': COOKIES_FILE if os.path.exists(COOKIES_FILE) else None,
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        files = os.listdir(downloads_dir)
        vid_file = next(f for f in files if f.endswith(f'[{quality}]'))
        file_path = os.path.join(downloads_dir, vid_file)
        
        caption = (
            f"✅ **{quality.upper()} VIDEO**\n"
            f"📹 **{info.get('title', 'Unknown')[:50]}**\n"
            f"👤 **{info.get('uploader', 'Unknown')}**\n"
            f"⏱️ **{info.get('duration', 0)}s**"
        )
        
        await callback.message.reply_video(
            video=file_path,
            caption=caption,
            supports_streaming=True,
            progress=upload_progress
        )
    
    os.remove(file_path)
    await callback.edit_message_text("✅ **Video Delivered!** 🎬")

async def download_audio(callback: CallbackQuery, url: str, bitrate: str):
    os.makedirs(downloads_dir, exist_ok=True)
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': f'{downloads_dir}/%(title).200s_[{bitrate}]%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': bitrate.rstrip('kbps'),
        }],
        'cookiefile': COOKIES_FILE if os.path.exists(COOKIES_FILE) else None,
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        files = os.listdir(downloads_dir)
        audio_file = next(f for f in files if f.endswith(f'[{bitrate}]'))
        file_path = os.path.join(downloads_dir, audio_file)
        
        await callback.message.reply_audio(
            audio=file_path,
            title=info.get('title', 'Audio'),
            performer=info.get('uploader', 'Unknown'),
            caption=f"✅ **{bitrate} AUDIO** | ⏱️ {info.get('duration', 0)}s"
        )
    
    os.remove(file_path)
    await callback.edit_message_text("✅ **Audio Delivered!** 🎵")

def is_valid_url(url: str) -> bool:
    parsed = urlparse(url)
    return bool(parsed.scheme and parsed.netloc and any(
        platform in parsed.netloc.lower() for platform in 
        ['youtube', 'youtu.be', 'instagram', 'facebook', 'tiktok', 'twitter', 'x.com']
    ))

async def upload_progress(current: int, total: int, *args):
    percent = (current / total) * 100
    print(f"Upload: {percent:.1f}%")

if __name__ == "__main__":
    os.makedirs(downloads_dir, exist_ok=True)
    print("🤖 KawaII5Bot Production Ready! 🚀")
    app.run()
