#!/usr/bin/env python3
"""
@KawaII5Bot - Advanced Telegram Video/Audio Downloader
Powered by yt-dlp + Pyrogram + FFmpeg
Supports 1000+ platforms with cookies authentication
"""

import os
import asyncio
import logging
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.errors import FloodWait
import yt_dlp
import ffmpeg

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Bot configuration
BOT_TOKEN = os.getenv("8209355827:AAHfJ8ew5YmTyAu4VoRrj2T3UZBq2m1ZrQM")
API_ID = int(os.getenv("37753288"))
API_HASH = os.getenv("68f5e26ac13f659083814b1f032ffc29")
COOKIES_FILE = "cookies.txt"

app = Client("KawaII5Bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Video/Audio quality options
VIDEO_QUALITIES = ["360p", "480p", "720p", "1080p", "1440p", "2160p", "best"]
AUDIO_BITRATES = ["64k", "128k", "192k", "256k", "320k"]

class DownloadManager:
    def __init__(self):
        self.download_tasks = {}
    
    async def download_media(self, url: str, quality: str, media_type: str = "video"):
        """Download media using yt-dlp"""
        try:
            ydl_opts = {
                'cookiefile': COOKIES_FILE if os.path.exists(COOKIES_FILE) else None,
                'noplaylist': True,
                'quiet': True,
            }
            
            if media_type == "audio":
                ydl_opts.update({
                    'format': 'bestaudio/best',
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': quality,
                    }],
                })
            else:
                ydl_opts.update({
                    'format': quality if quality != "best" else 'best[height<=?2160]',
                })
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                title = info.get('title', 'Unknown')
                filename = ydl.prepare_filename(info)
                
                # Download
                ydl.download([url])
                
                # Fix filename for audio
                if media_type == "audio":
                    filename = filename.rsplit('.', 1)[0] + '.mp3'
                
                return filename, title
                
        except Exception as e:
            logger.error(f"Download failed: {e}")
            return None, str(e)

download_manager = DownloadManager()

@app.on_message(filters.command("start"))
async def start_command(client, message):
    """Start command with platform info"""
    welcome_text = """
🎥 **@KawaII5Bot** - Universal Downloader

**Supported (1000+ platforms):**
• 📺 YouTube (4K/8K)
• 📱 Instagram Reels/Stories
• 📘 Facebook Videos
• 🎵 TikTok (No watermark)
• 🐦 Twitter/X
• 🎦 Vimeo + 1000+ more!

**Send any video/audio URL!** 👇
"""
    await message.reply(welcome_text)

@app.on_message(filters.text & ~filters.command(["start"]))
async def handle_url(client, message):
    """Handle URL messages"""
    url = message.text.strip()
    
    if not url:
        return
    
    # Check if valid URL
    if not ("http://" in url or "https://" in url):
        await message.reply("❌ Please send a valid URL!")
        return
    
    await message.reply("🔍 **Analyzing URL...**")
    
    # Create inline keyboard for options
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🎥 Video", callback_data=f"video_best_{url}")],
        [
            InlineKeyboardButton("🎵 Audio 320k", callback_data=f"audio_320k_{url}"),
            InlineKeyboardButton("📱 720p", callback_data=f"video_720p_{url}")
        ],
        [
            InlineKeyboardButton("🔥 1080p", callback_data=f"video_1080p_{url}"),
            InlineKeyboardButton("🎬 4K", callback_data=f"video_2160p_{url}")
        ],
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel")]
    ])
    
    await message.reply(
        "⚙️ **Select quality:**",
        reply_markup=keyboard
    )

@app.on_callback_query()
async def handle_callback(client: Client, callback: CallbackQuery):
    """Handle inline keyboard callbacks"""
    data = callback.data
    await callback.answer()
    
    if data == "cancel":
        await callback.edit_message_text("❌ Cancelled!")
        return
    
    # Parse callback data: type_quality_url
    parts = data.split("_", 2)
    if len(parts) != 3:
        await callback.edit_message_text("❌ Invalid selection!")
        return
    
    media_type, quality, url = parts
    
    if media_type not in ["video", "audio"]:
        await callback.edit_message_text("❌ Invalid media type!")
        return
    
    await callback.edit_message_text("⏳ **Downloading...** (This may take a while)")
    
    # Download
    filename, title = await download_manager.download_media(url, quality, media_type)
    
    if not filename or not os.path.exists(filename):
        await callback.edit_message_text(f"❌ **Download failed:**\n`{title}`")
        return
    
    # Send file
    try:
        await callback.edit_message_text("📤 **Uploading...**")
        
        if media_type == "audio":
            await client.send_audio(
                callback.message.chat.id,
                filename,
                caption=f"🎵 **{title}**\n`{quality} MP3`",
                title=title,
                performer="KawaII5Bot"
            )
        else:
            await client.send_video(
                callback.message.chat.id,
                filename,
                caption=f"🎥 **{title}**\n`{quality}`",
                supports_streaming=True
            )
        
        # Cleanup
        os.remove(filename)
        await callback.edit_message_text("✅ **Done!** File cleaned up.")
        
    except FloodWait as e:
        await callback.edit_message_text(f"⏳ Rate limited. Wait {e.value} seconds.")
    except Exception as e:
        await callback.edit_message_text(f"❌ **Upload failed:** {str(e)}")
        if os.path.exists(filename):
            os.remove(filename)

async def main():
    """Main function"""
    logger.info("Starting KawaII5Bot...")
    
    # Check cookies file
    if os.path.exists(COOKIES_FILE):
        logger.info("✅ Cookies file found")
    else:
        logger.warning("⚠️ No cookies.txt - Private content won't work")
    
    await app.start()
    logger.info("🚀 Bot started successfully!")
    await asyncio.Event().wait()  # Keep running

if __name__ == "__main__":
    asyncio.run(main())
