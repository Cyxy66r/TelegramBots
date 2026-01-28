import os
import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import yt_dlp
from urllib.parse import urlparse

BOT_TOKEN = "8209355827:AAHfJ8ew5YmTyAu4VoRrj2T3UZBq2m1ZrQM"  # @KawaII5Bot token
API_ID = "37753288"
API_HASH = "68f5e26ac13f659083814b1f032ffc29"

app = Client("kawaii_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Store URLs by chat_id
pending_urls = {}

VIDEO_QUALITIES = {
    "4k": "best[height>=2160]",
    "2k": "best[height>=1440]", 
    "1080p": "best[height<=1080]",
    "720p": "best[height<=720]",
    "480p": "best[height<=480]",
    "360p": "best[height<=360]"
}

@app.on_message(filters.command("start"))
async def start_cmd(client, message):
    btns = InlineKeyboardMarkup([
        [InlineKeyboardButton("🎬 VIDEO QUALITY", callback_data="video_menu")],
        [InlineKeyboardButton("🎵 AUDIO QUALITY", callback_data="audio_menu")]
    ])
    await message.reply_text(
        "🎥 **KawaII5Bot** - Pro Downloader\n\n"
        "📤 Send any video link:\n"
        "• YouTube • Instagram • Facebook • TikTok",
        reply_markup=btns,
        disable_web_page_preview=True
    )

@app.on_message(filters.text & ~filters.command("start"))
async def save_url(client, message):
    url = message.text.strip()
    
    # Validate URL
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        return await message.reply("❌ **Invalid URL!**\nSend http/https link")
    
    # Save URL for this chat
    chat_id = message.chat.id
    pending_urls[chat_id] = url
    
    # IMMEDIATELY show buttons
    video_btns = InlineKeyboardMarkup([
        [InlineKeyboardButton("🎥 4K", callback_data="v_4k"), InlineKeyboardButton("📺 2K", callback_data="v_2k")],
        [InlineKeyboardButton("✨ 1080p", callback_data="v_1080p"), InlineKeyboardButton("✅ 720p", callback_data="v_720p")],
        [InlineKeyboardButton("📱 480p", callback_data="v_480p"), InlineKeyboardButton("📲 360p", callback_data="v_360p")],
        [InlineKeyboardButton("🔙 New Link", callback_data="clear_url")]
    ])
    
    await message.reply_text(
        f"✅ **URL Saved:** `{url}`\n\n"
        "🎬 **Choose VIDEO Quality:**",
        reply_markup=video_btns,
        parse_mode="markdown"
    )
    
    # Also send audio options
    audio_btns = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔊 320kbps", callback_data="a_320"), InlineKeyboardButton("🎵 256kbps", callback_data="a_256")],
        [InlineKeyboardButton("📻 192kbps", callback_data="a_192"), InlineKeyboardButton("🔉 128kbps", callback_data="a_128")],
        [InlineKeyboardButton("📡 64kbps", callback_data="a_64")],
        [InlineKeyboardButton("🔙 New Link", callback_data="clear_url")]
    ])
    
    await message.reply_text("🎵 **Or choose AUDIO Quality:**", reply_markup=audio_btns)

@app.on_callback_query()
async def cb_handler(client, callback: CallbackQuery):
    data = callback.data
    chat_id = callback.message.chat.id
    
    if chat_id not in pending_urls:
        return await callback.edit_message_text("❌ **First send a URL!**")
    
    url = pending_urls[chat_id]
    
    if data == "clear_url":
        pending_urls.pop(chat_id, None)
        return await callback.edit_message_text("🔄 **Ready for new URL!**")
    
    await callback.answer("🚀 Downloading...")
    
    # Download based on type
    if data.startswith("v_"):
        quality = data[2:]
        await download_video(callback, url, quality)
    elif data.startswith("a_"):
        bitrate = data[2:]
        await download_audio(callback, url, bitrate)

async def download_video(callback, url, quality):
    try:
        await callback.edit_message_text(f"🎬 Downloading **{quality.upper()}**...")
        
        ydl_opts = {
            'format': f'{VIDEO_QUALITIES[quality]}+bestaudio/best[height<=?1080]',
            'outtmpl': f'downloads/vid_%(title)s_{quality}.%(ext)s'
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            files = os.listdir('downloads')
            file_path = [f for f in files if f.startswith('vid_')][0]
            full_path = f'downloads/{file_path}'
            
            caption = f"✅ **{quality.upper()} Video**\n📺 **{info.get('title', 'Unknown')}**"
            
            await callback.message.reply_video(
                video=full_path,
                caption=caption,
                supports_streaming=True
            )
        
        # Cleanup
        os.remove(full_path)
        await callback.edit_message_text("✅ **Video sent!** 🎉")
        
    except Exception as e:
        await callback.edit_message_text(f"❌ **Error:** `{str(e)[:100]}`")

async def download_audio(callback, url, bitrate):
    try:
        await callback.edit_message_text(f"🎵 Extracting **{bitrate}** audio...")
        
        ydl_opts = {
            'format': 'bestaudio',
            'outtmpl': f'downloads/audio_%(title)s_{bitrate}.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': bitrate[:-3],  # Remove 'kbps'
            }]
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            files = os.listdir('downloads')
            file_path = [f for f in files if f.startswith('audio_')][0]
            full_path = f'downloads/{file_path}'
            
            await callback.message.reply_audio(
                audio=full_path,
                title=info.get('title', 'Audio'),
                caption=f"✅ **{bitrate} Audio**"
            )
        
        os.remove(full_path)
        await callback.edit_message_text("✅ **Audio sent!** 🎵")
        
    except Exception as e:
        await callback.edit_message_text(f"❌ **Error:** `{str(e)[:100]}`")

if __name__ == "__main__":
    os.makedirs("downloads", exist_ok=True)
    print("🤖 KawaII5Bot Starting...")
    app.run()
