import os

PATH = os.path.dirname(os.path.abspath(__file__))

# متن‌های ربات برای Telethon
TEXT = {
    "start": "🎬 **سلام! به ربات دانلود یوتیوب و اینستاگرام خوش آمدید**\n\n📥 **قابلیت‌های ربات:**\n• دانلود ویدیو از یوتیوب با کیفیت‌های مختلف\n• دانلود صوت MP3 از یوتیوب\n• دانلود پست و ویدیو از اینستاگرام\n• نمایش پیشرفت دانلود به صورت زنده\n• رابط کاربری مدرن و زیبا\n\n🔗 **برای شروع، لینک خود را ارسال کنید**\n\n⚡ **پشتیبانی از Telethon برای عملکرد بهتر**",
    "help": "📋 **راهنمای استفاده:**\n\n🎥 **یوتیوب:**\n• لینک ویدیو را ارسال کنید\n• از بین کیفیت‌های مختلف انتخاب کنید\n• صوت MP3 با کیفیت بالا دریافت کنید\n\n📸 **اینستاگرام:**\n• لینک پست، ریل یا IGTV را ارسال کنید\n• ویدیو یا تصویر را انتخاب کنید\n\n⚡ **ویژگی‌های جدید:**\n• نمایش پیشرفت دانلود\n• پشتیبانی از فرمت‌های مختلف\n• سرعت دانلود بالا\n\n⚠️ **محدودیت‌ها:**\n• حداکثر حجم فایل: 50 مگابایت\n• کیفیت بهینه برای تلگرام",
    "invalid_link": "❌ لینک نامعتبر است. لطفاً لینک معتبر یوتیوب یا اینستاگرام ارسال کنید.",
    "processing": "🔄 در حال پردازش با Telethon...",
    "error": "❌ خطایی رخ داد. لطفاً دوباره تلاش کنید.",
    "youtube_detected": "🎬 لینک یوتیوب شناسایی شد",
    "instagram_detected": "📱 لینک اینستاگرام شناسایی شد",
    "download_started": "📥 دانلود شروع شد",
    "download_completed": "✅ دانلود با موفقیت انجام شد",
    "upload_started": "📤 آپلود به تلگرام شروع شد"
}

# تنظیمات دیتابیس برای Telethon
DATA = {
    "database": {
        "name": "telethon_bot.db",
        "tables": {
            "users": "CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, user_id INTEGER UNIQUE, username TEXT, first_name TEXT, last_name TEXT, join_date TEXT, last_activity TEXT)",
            "downloads": "CREATE TABLE IF NOT EXISTS downloads (id INTEGER PRIMARY KEY, user_id INTEGER, url TEXT, platform TEXT, media_type TEXT, file_size INTEGER, download_date TEXT, FOREIGN KEY (user_id) REFERENCES users (user_id))",
            "sessions": "CREATE TABLE IF NOT EXISTS sessions (id INTEGER PRIMARY KEY, user_id INTEGER, session_data TEXT, created_at TEXT, FOREIGN KEY (user_id) REFERENCES users (user_id))"
        }
    },
    "telethon": {
        "session_name": "bot_session",
        "parse_mode": "md",
        "timeout": 30,
        "max_file_size": 50 * 1024 * 1024,  # 50MB
        "chunk_size": 8192
    }
}