import logging
import os
import asyncio
import yt_dlp
import shutil
import subprocess
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command
from aiogram import Router

# Bot tokenini shu yerga kiriting
TOKEN = "7654811530:AAFfSpa93qeKmIggtikUh2nCB9tWRwNHPpg"

# Telegram bot va dispatcher yaratish
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()
router = Router()

# Logging sozlamalari
logging.basicConfig(level=logging.INFO)

# FFmpeg mavjudligini tekshirish
if not shutil.which("ffmpeg"):
    raise RuntimeError("FFmpeg o‘rnatilmagan yoki yo‘q. Iltimos, uni o‘rnating.")

# Tugmalar menyusi
buttons = [
    [KeyboardButton(text="O'zbek"), KeyboardButton(text="Русский"), KeyboardButton(text="English")]
]
language_keyboard = ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

@router.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer("Tilni tanlang / Выберите язык / Choose a language:", reply_markup=language_keyboard)

@router.message()
async def language_selected(message: types.Message):
    if message.text in ["O'zbek", "Русский", "English"]:
        greetings = {
            "O'zbek": "YouTube havolasini yuboring:",
            "Русский": "Отправьте ссылку на YouTube:",
            "English": "Send a YouTube link:",
        }
        await message.answer(greetings[message.text])
    elif message.text.startswith("http"):
        await ask_video_quality(message)

async def ask_video_quality(message: types.Message):
    url = message.text
    quality_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="1080p", callback_data=f"quality_1080p_{url}"),
         InlineKeyboardButton(text="720p", callback_data=f"quality_720p_{url}")],
        [InlineKeyboardButton(text="480p", callback_data=f"quality_480p_{url}"),
         InlineKeyboardButton(text="360p", callback_data=f"quality_360p_{url}")],
        [InlineKeyboardButton(text="240p", callback_data=f"quality_240p_{url}")]
    ])
    await message.answer("Videoning sifatini tanlang:", reply_markup=quality_keyboard)

@router.callback_query()
async def process_quality_selection(callback_query: types.CallbackQuery):
    data = callback_query.data.split("_")
    quality = data[1]
    url = "_".join(data[2:])
    await callback_query.message.answer(f"{quality} sifatida yuklab olinmoqda...")
    await download_video(callback_query.message, url, quality)

async def download_video(message: types.Message, url: str, quality: str):
    try:
        quality_map = {
            "1080p": "137+bestaudio",
            "720p": "136+bestaudio",
            "480p": "135+bestaudio",
            "360p": "134+bestaudio",
            "240p": "133+bestaudio",
        }
        format_string = quality_map.get(quality, "134+bestaudio")

        ydl_opts = {
            'format': format_string,
            'outtmpl': 'downloaded_video.%(ext)s',
            'merge_output_format': 'mp4',
            'postprocessors': [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',
            }]
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        input_file = "downloaded_video.mp4"
        output_file = "converted_video.mp4"

        # FFmpeg orqali videoni aniq 16:9 formatda qilish
        ffmpeg_command = [
            "ffmpeg", "-i", input_file, "-vf", "scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2",
            "-c:a", "copy", output_file
        ]
        subprocess.run(ffmpeg_command, check=True)

        video = FSInputFile(output_file)
        await message.answer_video(video, caption="Video yuklab olindi!", supports_streaming=True)

        os.remove(input_file)
        os.remove(output_file)  # Tozalash
    except Exception as e:
        await message.answer(f"Xatolik yuz berdi: {e}")

async def main():
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())