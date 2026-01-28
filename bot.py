import os
import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import yt_dlp
from urllib.parse import urlparse

# Bot configuration - CHANGE THESE!
BOT_TOKEN = "8348615649:AAFY799SOdeKpLwtDTgHKyVdgU3HSxgjbtY"
API_ID = "37753288"  # my.telegram.org
API_HASH = "68f5e26ac13f659083814b1f032ffc29"

app = Client("video_downloader_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Quality selectors
VIDEO_QUALITIES = {
    "4k": "best[height>=2160]",
    "2k": "best[height>=1440]", 
    "1080p": "best[height<=1080]",
    "720p": "best[height<=720]",
    "480p": "best[height<=480]",
    "360p": "best[height<=360]"
}

AUDIO_BITRATES = {
    "320kbps": 320,
    "256kbps": 256,
    "192kbps": 192,
    "128kbps": 128,
    "64kbps": 64
}

user_data = {}  # Store user URLs temporarily

@app.on_message(filters.command("start"))
async def start_command(client, message):
    welcome_text = """
🎥 **PRO Video Downloader Bot**

**Supported:** Instagram • Facebook • YouTube • TikTok • Twitter + 1000+ sites!

**🎬 Video:** 4K • 2K • 1080p • 720p • 480p • 360p
**🎵 Audio:** 320kbps • 256kbps • 192kbps • 128kbps • 64kbps

Just send any video link! 👇
    """
    
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("🎬 VIDEO OPTIONS", callback_data="video_menu")],
        [InlineKeyboardButton("🎵 AUDIO OPTIONS", callback_data="audio_menu")]
    ])
    
    await message.reply_text(welcome_text, reply_markup=buttons, disable_web_page_preview=True)

@app.on_message(filters.text & ~filters.command("start"))
async def handle_url(client, message):
    url = message.text.strip()
    
    # Check if it's a valid URL
    if not urlparse(url).scheme:
        return await message.reply("❌ Send a **valid URL** (http/https)")
    
    user_data[message.from_user.id] = url
    await message.reply("✅ **URL saved!**\n\nChoose quality below 👇")

@app.on_callback_query()
async def callback_handler(client, callback_query: CallbackQuery):
    data = callback_query.data
    user_id = callback_query.from_user.id
    await callback_query.answer()
    
    if user_id not in user_data:
        return await callback_query.edit_message_text("❌ First send a video URL!")
    
    url = user_data[user_id]
    
    if data == "video_menu":
        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("🎥 4K UHD", callback_data="video_4k")],
            [InlineKeyboardButton("📺 2K QHD", callback_data="video_2k")],
            [InlineKeyboardButton("✨ 1080p FHD", callback_data="video_1080p")],
            [InlineKeyboardButton("✅ 720p HD", callback_data="video_720p")],
            [InlineKeyboardButton("📱 480p", callback_data="video_480p"), InlineKeyboardButton("📲 360p", callback_data="video_360p")],
            [InlineKeyboardButton("🔙 New URL", callback_data="clear")]
        ])
        await callback_query.edit_message_text("🎬 **VIDEO QUALITY**", reply_markup=buttons)
    
    elif data == "audio_menu":
        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔊 320kbps", callback_data="audio_320kbps"), InlineKeyboardButton("🎵 256kbps", callback_data="audio_256kbps")],
            [InlineKeyboardButton("📻 192kbps", callback_data="audio_192kbps"), InlineKeyboardButton("🔉 128kbps", callback_data="audio_128kbps")],
            [InlineKeyboardButton("📡 64kbps", callback_data="audio_64kbps")],
            [InlineKeyboardButton("ℹ️ Max: 320kbps | Min: 64kbps", callback_data="audio_info")],
            [InlineKeyboardButton("🔙 New URL", callback_data="clear")]
        ])
        await callback_query.edit_message_text("🎵 **AUDIO QUALITY**", reply_markup=buttons)
    
    elif data.startswith("video_"):
        quality = data.split("_")[1]
        await download_video(callback_query, url, quality)
    
    elif data.startswith("audio_"):
        bitrate = data.split("_")[1]
        await download_audio(callback_query, url, bitrate)
    
    elif data == "clear":
        user_data.pop(user_id, None)
        await callback_query.edit_message_text("🔄 Ready for new URL!")

async def download_video(callback, url, quality):
    await callback.edit_message_text(f"🚀 Downloading **{quality.upper()}** video...")
    
    try:
        ydl_opts = {
            'format': f'{VIDEO_QUALITIES[quality]}+bestaudio/best',
            'outtmpl': f'downloads/%(title)200s_[{quality}]%(ext)s',
            'merge_output_format': 'mp4'
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info).replace('.webm', '.mp4').replace('.mhtml', '.mp4')
            
            await callback.message.reply_video(
                video=file_path,
                caption=f"✅ **{quality.upper()} Video**\n📹 Resolution: {quality}\n💾 Size: {format(os.path.getsize(file_path)/1024/1024, '.1f')} MB"
            )
        
        os.remove(file_path)
        await callback.edit_message_text("✅ Video sent successfully!")
        
    except Exception as e:
        await callback.edit_message_text(f"❌ Error: {str(e)[:100]}")

async def download_audio(callback, url, bitrate):
    await callback.edit_message_text(f"🎵 Extracting **{bitrate}** audio...")
    
    try:
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': f'downloads/%(title)200s_[{bitrate}]%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': AUDIO_BITRATES[bitrate],
            }]
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info).replace('.webm', '.mp3').replace('.mhtml', '.mp3')
            
            await callback.message.reply_audio(
                audio=file_path,
                title=info.get('title', 'Audio'),
                performer=info.get('uploader', 'Unknown'),
                caption=f"✅ **{bitrate} Audio**\n🔊 Bitrate: {bitrate}\n⏱️ Duration: {info.get('duration', 0)}s"
            )
        
        os.remove(file_path)
        await callback.edit_message_text("✅ Audio sent successfully!")
        
    except Exception as e:
        await callback.edit_message_text(f"❌ Error: {str(e)[:100]}")

if __name__ == "__main__":
    os.makedirs("downloads", exist_ok=True)
    print("🤖 Starting Video Downloader Bot...")
    app.run()
