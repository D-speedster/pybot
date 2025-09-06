import logging
import asyncio
import os
from telethon import TelegramClient, events, Button
from telethon.tl.types import DocumentAttributeVideo, DocumentAttributeAudio
from plugins.db_wrapper import DB
from plugins.youtube import handle_youtube_message, handle_youtube_callback
from plugins.instagram import handle_instagram_message, handle_instagram_callback
from config import BOT_TOKEN, API_ID, API_HASH
import re

# تنظیم لاگ
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ایجاد کلاینت Telethon با تنظیمات بهینه
client = TelegramClient(
    'bot_session', 
    API_ID, 
    API_HASH,
    connection_retries=5,
    retry_delay=1,
    timeout=30,
    request_retries=5
)

# Regex patterns
youtube_regex = re.compile(
    r'(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/'
    r'(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})'
)

instagram_regex = re.compile(
    r'https?://(?:www\.)?instagram\.com/(?:p|reel|tv)/([A-Za-z0-9_-]+)/?'
)

@client.on(events.NewMessage(pattern='/start'))
async def start_handler(event):
    """پردازش دستور /start"""
    try:
        user_id = event.sender_id
        
        # اضافه کردن کاربر به دیتابیس
        db = DB()
        db.add_user(user_id)
        
        welcome_message = (
            "🤖 **سلام! به ربات دانلود خوش آمدید**\n\n"
            "📺 **یوتیوب**: لینک ویدیو را ارسال کنید\n"
            "📸 **اینستاگرام**: لینک پست را ارسال کنید\n\n"
            "✨ **ویژگی‌ها:**\n"
            "• نمایش پیشرفت دانلود\n"
            "• کیفیت‌های مختلف\n"
            "• دانلود سریع و مطمئن\n\n"
            "🚀 **برای شروع، لینک خود را ارسال کنید!**"
        )
        
        await event.respond(welcome_message, parse_mode='md')
        
        logger.info(f"کاربر جدید شروع کرد: {user_id}")
        
    except Exception as e:
        logger.error(f"خطا در start handler: {e}")
        await event.respond("❌ خطایی رخ داد. لطفاً دوباره تلاش کنید.")

@client.on(events.NewMessage(func=lambda e: e.text and not e.text.startswith('/')))
async def message_handler(event):
    """پردازش پیام‌های متنی"""
    try:
        text = event.text
        
        # بررسی لینک یوتیوب
        if youtube_regex.search(text):
            await handle_youtube_message(event, client)
        # بررسی لینک اینستاگرام
        elif instagram_regex.search(text):
            await handle_instagram_message(event, client)
        else:
            await event.respond(
                "❌ **لینک نامعتبر**\n\n"
                "لطفاً لینک معتبر یوتیوب یا اینستاگرام ارسال کنید.",
                parse_mode='md'
            )
            
    except Exception as e:
        logger.error(f"خطا در message handler: {e}")
        await event.respond("❌ خطایی رخ داد. لطفاً دوباره تلاش کنید.")

@client.on(events.CallbackQuery)
async def callback_handler(event):
    """پردازش callback query ها"""
    try:
        data = event.data.decode('utf-8')
        
        # YouTube callbacks
        if data.startswith(('yt_video_', 'yt_audio_', 'yt_cover_')):
            await handle_youtube_callback(event, client)
        # Instagram callbacks
        elif data.startswith('ig_post_'):
            await handle_instagram_callback(event, client)
        else:
            await event.answer("❌ درخواست نامعتبر", alert=True)
            
    except Exception as e:
        logger.error(f"خطا در callback handler: {e}")
        await event.answer("❌ خطایی رخ داد", alert=True)

async def main():
    """تابع اصلی"""
    try:
        # شروع کلاینت
        await client.start(bot_token=BOT_TOKEN)
        
        # دریافت اطلاعات ربات
        me = await client.get_me()
        logger.info(f"ربات شروع شد: @{me.username}")
        
        # ایجاد پوشه Downloads
        os.makedirs('Downloads', exist_ok=True)
        
        # اجرای ربات
        logger.info("ربات آماده دریافت پیام است...")
        await client.run_until_disconnected()
        
    except Exception as e:
        logger.error(f"خطا در راه‌اندازی ربات: {e}")
    finally:
        await client.disconnect()

if __name__ == '__main__':
    asyncio.run(main())
