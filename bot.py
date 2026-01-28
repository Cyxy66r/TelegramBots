import os
import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message
import yt_dlp
from urllib.parse import urlparse

# ================= CONFIG =================
BOT_TOKEN = os.getenv("8209355827:AAHfJ8ew5YmTyAu4VoRrj2T3UZBq2m1ZrQM")
API_ID = int(os.getenv("37753288"))
API_HASH = os.getenv("68f5e26ac13f659083814b1f032ffc29")

app = Client("kawaii_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

downloads_dir = "downloads"
pending_urls = {}

# ================= QUEUE SYSTEM =================
download_queue = asyncio.Queue()

# ================= COOKIE FILES =================
COOKIE_FILES = {
    "instagram": "cookies/instagram.txt",
    "facebook": "cookies/facebook.txt",
    "youtube": "cookies/youtube.txt",
    "tiktok": "cookies/tiktok.txt",
    "twitter": "cookies/twitter.txt",
    "x": "cookies/twitter.txt",
}

# ================= VIDEO QUALITIES =================
VIDEO_QUALITIES = {
    "4k": "bestvideo[height>=2160]+bestaudio/best",
    "2k": "bestvideo[height>=1440]+bestaudio/best",
    "fhd": "bestvideo[height<=1080]+bestaudio/best",
    "hd": "bestvideo[height<=720]+bestaudio/best",
    "sd": "bestvideo[height<=480]+bestaudio/best",
    "low": "bestvideo[height<=360]+bestaudio/best"
}

# ================= HELPERS =================
def get_platform(url: str):
    d = urlparse(url).netloc.lower()
    if "instagram" in d:
        return "instagram"
    if "facebook" in d:
        return "facebook"
    if "youtu" in d:
        return "youtube"
    if "tiktok" in d:
        return "tiktok"
    if "twitter" in d or "x.com" in d:
        return "twitter"
    return None

def get_cookie_file(url: str):
    platform = get_platform(url)
    cookie = COOKIE_FILES.get(platform)
    return cookie if cookie and os.path.exists(cookie) else None

def is_valid_url(url: str) -> bool:
    p = urlparse(url)
    return bool(p.scheme and p.netloc)

# ================= QUEUE WORKER =================
async def queue_worker():
    while True:
        job = await download_queue.get()
        try:
            mode, callback, url, value = job
            if mode == "video":
                await download_video(callback, url, value)
            else:
                await download_audio(callback, url, value)
        except Exception as e:
            await callback.message.reply(f"❌ Download failed:\n`{e}`")
        finally:
            download_queue.task_done()

# ================= START =================
@app.on_message(filters.command("start"))
async def start(client, message: Message):
    await message.reply_text(
        "🎥 **KawaII5Bot Downloader**\n\n"
        "Send a video link 👇"
    )

# ================= URL INPUT =================
@app.on_message(filters.text & ~filters.command("start"))
async def process_url(client, message: Message):
    url = message.text.strip()

    if not is_valid_url(url):
        return await message.reply("❌ Invalid URL")

    pending_urls[message.chat.id] = url

    kb = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("4K", callback_data="v_4k"),
            InlineKeyboardButton("2K", callback_data="v_2k")
        ],
        [
            InlineKeyboardButton("1080p", callback_data="v_fhd"),
            InlineKeyboardButton("720p", callback_data="v_hd")
        ],
        [
            InlineKeyboardButton("480p", callback_data="v_sd"),
            InlineKeyboardButton("360p", callback_data="v_low")
        ],
        [
            InlineKeyboardButton("MP3", callback_data="a_128")
        ]
    ])

    await message.reply_text("Select quality:", reply_markup=kb)

# ================= CALLBACK =================
@app.on_callback_query()
async def handle_callback(client, callback: CallbackQuery):
    chat_id = callback.message.chat.id

    if chat_id not in pending_urls:
        return await callback.answer("Send URL first", show_alert=True)

    url = pending_urls[chat_id]
    data = callback.data

    if data.startswith("v_"):
        quality = data[2:]
        await download_queue.put(("video", callback, url, quality))
    elif data.startswith("a_"):
        bitrate = data[2:]
        await download_queue.put(("audio", callback, url, bitrate))
    else:
        return

    position = download_queue.qsize()
    await callback.edit_message_text(
        f"✅ Added to queue\n⏳ Position: **{position}**"
    )

# ================= VIDEO =================
async def download_video(callback: CallbackQuery, url: str, quality: str):
    os.makedirs(downloads_dir, exist_ok=True)
    cookie_file = get_cookie_file(url)

    ydl_opts = {
        "format": VIDEO_QUALITIES[quality],
        "outtmpl": f"{downloads_dir}/%(title).200s_[{quality}].%(ext)s",
        "merge_output_format": "mp4",
        "cookiefile": cookie_file,
        "quiet": True
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)

    file_path = next(
        os.path.join(downloads_dir, f)
        for f in os.listdir(downloads_dir)
        if f"[{quality}]" in f
    )

    await callback.message.reply_video(
        video=file_path,
        caption=f"🎬 **{info.get('title','Video')}**",
        supports_streaming=True
    )

    os.remove(file_path)

# ================= AUDIO =================
async def download_audio(callback: CallbackQuery, url: str, bitrate: str):
    os.makedirs(downloads_dir, exist_ok=True)
    cookie_file = get_cookie_file(url)

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": f"{downloads_dir}/%(title).200s_[audio].%(ext)s",
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": bitrate,
        }],
        "cookiefile": cookie_file,
        "quiet": True
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)

    file_path = next(
        os.path.join(downloads_dir, f)
        for f in os.listdir(downloads_dir)
        if f.endswith(".mp3")
    )

    await callback.message.reply_audio(
        audio=file_path,
        title=info.get("title", "Audio")
    )

    os.remove(file_path)

# ================= RUN =================
if __name__ == "__main__":
    os.makedirs(downloads_dir, exist_ok=True)
    loop = asyncio.get_event_loop()
    loop.create_task(queue_worker())
    app.run()
