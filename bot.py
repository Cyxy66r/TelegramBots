import os
import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import yt_dlp

# Bot configuration
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"
API_ID = "YOUR_API_ID"
API_HASH = "YOUR_API_HASH"

app = Client("video_downloader_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Enhanced Quality Options with Specific Resolutions & Bitrates
VIDEO_QUALITIES = {
    "4k": "best[height>=2160]",
    "2k": "best[height>=1440]",
    "1080p": "best[height<=1080]",
    "720p": "best[height<=720]",
    "480p": "best[height<=480]",
    "360p": "best[height<=360]"
}

AUDIO_BITRATES = {
    "320kbps": "bestaudio[abr<=320]",
    "256kbps": "bestaudio[abr<=256]", 
    "192kbps": "bestaudio[abr<=192]",
    "128kbps": "bestaudio[abr<=128]",
    "64kbps": "bestaudio[abr<=64]"
}

# Bitrate limits info
BITRATE_INFO = {
    "max": "320kbps (Highest Quality)",
    "min": "64kbps (Smallest Size)"
}

@app.on_message(filters.command("start"))
async def start_command(client, message):
    welcome_text = """
🎥 **ULTIMATE Video Downloader Bot** 🎥

**Supported Platforms:**
• 📱 Instagram Reels/Stories/IGTV
• 📘 Facebook Videos/Reels  
• 📺 YouTube (4K/8K Support!)
• 🎵 TikTok
• 📱 Twitter/X Videos
• 1000+ More Platforms!

**Quality Options:** 4K • 2K • 1080p • 720p • 480p • 360p
**Audio Options:** 320kbps • 256kbps • 192kbps • 128kbps • 64kbps

**Max Audio:** 320kbps | **Min Audio:** 64kbps
    """
    
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("🎬 VIDEO QUALITY", callback_data="show_video")],
        [InlineKeyboardButton("🎵 AUDIO QUALITY", callback_data="show_audio")],
        [InlineKeyboardButton("ℹ️ HELP", callback_data="help")]
    ])
    
    await message.reply_text(welcome_text, reply_markup=buttons)

@app.on_message(filters.text & ~filters.command(["start"]))
async def handle_url(client, message):
    url = message.text.strip()
    if not url:
        return await message.reply("❌ Send a valid URL!")
    
    # Store URL in session for callback use
    message.chat.url_data = url
    
    main_buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("🎬 CHOOSE VIDEO QUALITY ➡️", callback_data="video_menu")],
        [InlineKeyboardButton("🎵 CHOOSE AUDIO QUALITY ➡️", callback_data="audio_menu")],
        [InlineKeyboardButton("🔄 REFRESH", callback_data="refresh")]
    ])
    
    await message.reply_text(
        f"🔗 **Link Detected:** `{url}`\n\n"
        "Choose **Video** or **Audio** quality below:",
        reply_markup=main_buttons,
        parse_mode="markdown"
    )

@app.on_callback_query()
async def callback_handler(client, callback_query: CallbackQuery):
    data = callback_query.data
    chat_id = callback_query.message.chat.id
    await callback_query.answer()
    
    url = callback_query.message.reply_markup.inline_keyboard[0][0].text if hasattr(callback_query.message, 'reply_markup') else None
    
    if data == "show_video":
        video_buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("4K UHD 🎥", callback_data="video_4k")],
            [InlineKeyboardButton("2K QHD 📺", callback_data="video_2k")],
            [InlineKeyboardButton("1080p FHD ✨", callback_data="video_1080p")],
            [InlineKeyboardButton("720p HD ✅", callback_data="video_720p")],
            [InlineKeyboardButton("480p 📱", callback_data="video_480p"), InlineKeyboardButton("360p 📲", callback_data="video_360p")],
            [InlineKeyboardButton("🔙 Back", callback_data="start")]
        ])
        await callback_query.edit_message_text("🎬 **VIDEO QUALITY OPTIONS**", reply_markup=video_buttons)
    
    elif data == "show_audio":
        audio_buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("320kbps 🔊", callback_data="audio_320"), InlineKeyboardButton("256kbps 🎵", callback_data="audio_256")],
            [InlineKeyboardButton("192kbps 📻", callback_data="audio_192"), InlineKeyboardButton("128kbps 🔉", callback_data="audio_128")],
            [InlineKeyboardButton("64kbps 📡", callback_data="audio_64")],
            [InlineKeyboardButton(f"ℹ️ MAX: {BITRATE_INFO['max']}", callback_data="audio_info"), InlineKeyboardButton(f"ℹ️ MIN: {BITRATE_INFO['min']}", callback_data="audio_info")],
            [InlineKeyboardButton("🔙 Back", callback_data="start")]
        ])
        await callback_query.edit_message_text("🎵 **AUDIO QUALITY OPTIONS**\n\n**Max:** 320kbps | **Min:** 64kbps", reply_markup=audio_buttons)
    
    elif data.startswith("video_"):
        quality = data.split("_")[1]
        await download_with_quality(callback_query, url or callback_query.message.text, f"video_{quality}", "VIDEO")
    
    elif data.startswith("audio_"):
        bitrate = data.split("_")[1] + "kbps"
        await download_with_quality(callback_query, url or callback_query.message.text, f"audio_{bitrate}", "AUDIO")
    
    elif data == "video_menu":
        await callback_handler(client, CallbackQuery(callback_query.message.chat.id, callback_query.message.message_id, "show_video"))
    
    elif data == "audio_menu":
        await callback_handler(client, CallbackQuery(callback_query.message.chat.id, callback_query.message.message_id, "show_audio"))

async def download_with_quality(callback_query, url, quality_key, media_type):
    await callback_query.edit_message_text(f"🚀 **{media_type}** downloading in **{quality_key.replace('_', ' ').title()}**...")
    
    try:
        # Enhanced yt-dlp options for specific qualities
        if media_type == "VIDEO":
            format_selector = VIDEO_QUALITIES[quality_key.split("_")[1]]
            ydl_opts = {
                'format': f'{format_selector}+bestaudio/best',
                'outtmpl': f'downloads/%(title)s_[{quality_key}]%(ext)s'
            }
        else:
            bitrate = quality_key.split("_")[1]
            ydl_opts = {
                'format': f'bestaudio[abr<={bitrate}]',
                'outtmpl': f'downloads/%(title)s_[{quality_key}]%(ext)s',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': bitrate,
                }]
            }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            # Send file based on type
            if media_type == "VIDEO":
                await callback_query.message.reply_video(
                    video=filename,
                    caption=f"✅ **{media_type}** `{quality_key.replace('_', ' ').title()}`\n💾 **Size:** {format(os.path.getsize(filename)/1024/1024, '.1f')} MB"
                )
            else:
                await callback_query.message.reply_audio(
                    audio=filename,
                    caption=f"✅ **{media_type}** `{quality_key.replace('_', ' ').title()}`\n🔊 **Bitrate:** {bitrate}"
                )
        
        # Cleanup
        os.remove(filename)
        await callback_query.edit_message_text(f"✅ **{media_type}** sent successfully!")
        
    except Exception as e:
        await callback_query.edit_message_text(f"❌ **Error:** {str(e)[:100]}...\nTry different quality!")

if __name__ == "__main__":
    os.makedirs("downloads", exist_ok=True)
    print("🤖 Bot starting...")
    app.run()