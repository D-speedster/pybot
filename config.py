import os
from pathlib import Path

# Bot Configuration
BOT_TOKEN = os.environ.get("BOT_TOKEN", "5039797268:AAFSDw5iYLrW8-8sZoMUbvvScHajGc3e5Ms")

# Telegram API Configuration
API_ID = int(os.environ.get("API_ID", 1486978))
API_HASH = os.environ.get("API_HASH", "28b6d63bd38d105c77fc1dbe8f647e1a")

# Proxy functionality completely removed for better performance

# Session Management
SESSIONS_DIR = Path("sessions")
SESSIONS_DIR.mkdir(exist_ok=True)

# Userbot Configuration
USERBOT_CONFIG = {
    'max_sessions': int(os.environ.get('MAX_SESSIONS', 3)),
    'session_timeout': int(os.environ.get('SESSION_TIMEOUT', 300)),  # 5 minutes
    'retry_attempts': int(os.environ.get('RETRY_ATTEMPTS', 3)),
    'retry_delay': int(os.environ.get('RETRY_DELAY', 5)),
    'load_balance_method': os.environ.get('LOAD_BALANCE_METHOD', 'round_robin')  # round_robin, least_used
}

# Download Configuration
DOWNLOAD_CONFIG = {
    'temp_dir': Path("temp_downloads"),
    'max_file_size': int(os.environ.get('MAX_FILE_SIZE', 1536 * 1024 * 1024)),  # 1.5GB
    'cleanup_after': int(os.environ.get('CLEANUP_AFTER', 3600)),  # 1 hour
    'concurrent_downloads': int(os.environ.get('CONCURRENT_DOWNLOADS', 3)),
    'chunk_size': int(os.environ.get('CHUNK_SIZE', 8192))
}

# Create temp directory
DOWNLOAD_CONFIG['temp_dir'].mkdir(exist_ok=True)

# Admin Configuration
ADMIN_IDS = list(map(int, os.environ.get('ADMIN_IDS', '').split(',') if os.environ.get('ADMIN_IDS') else []))

# Database Configuration
DATABASE_CONFIG = {
    'name': 'userbot_manager.db',
    'tables': {
        'users': '''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            user_id INTEGER UNIQUE,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            join_date TEXT,
            last_activity TEXT,
            is_premium BOOLEAN DEFAULT 0
        )''',
        'downloads': '''CREATE TABLE IF NOT EXISTS downloads (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            url TEXT,
            platform TEXT,
            media_type TEXT,
            file_size INTEGER,
            session_used TEXT,
            download_date TEXT,
            status TEXT,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )''',
        'sessions': '''CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY,
            session_name TEXT UNIQUE,
            phone_number TEXT,
            is_active BOOLEAN DEFAULT 1,
            last_used TEXT,
            usage_count INTEGER DEFAULT 0,
            created_at TEXT
        )''',
        'message_queue': '''CREATE TABLE IF NOT EXISTS message_queue (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            message_text TEXT,
            message_type TEXT,
            created_at TEXT,
            processed BOOLEAN DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )'''
    }
}

# Logging Configuration
LOGGING_CONFIG = {
    'level': os.environ.get('LOG_LEVEL', 'INFO'),
    'console_level': os.environ.get('CONSOLE_LOG_LEVEL', 'INFO'),
    'file_level': os.environ.get('FILE_LOG_LEVEL', 'DEBUG'),
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'file': 'bot.log',
    'log_dir': 'logs',
    'max_size': 10 * 1024 * 1024,  # 10MB
    'backup_count': 5
}

# Rate Limiting
RATE_LIMIT_CONFIG = {
    'enabled': True,
    'max_requests_per_minute': 30,
    'max_requests_per_hour': 100,
    'cooldown_period': 60  # seconds
}

# Quality Options
QUALITY_OPTIONS = {
    'youtube': {
        '4k': 'best[height<=2160][ext=mp4]/best[height<=2160]/best',
        '1440p': 'best[height<=1440][ext=mp4]/best[height<=1440]/best',
        '1080p': 'best[height<=1080][ext=mp4]/best[height<=1080]/best',
        'hd': 'best[height<=720][height>=720][ext=mp4]/best[height<=720][height>=720]/best[height<=720]',
        'sd': 'best[height<=480][height>=480][ext=mp4]/best[height<=480][height>=480]/best[height<=480]',
        '720p': 'best[height<=720][height>=720][ext=mp4]/best[height<=720][height>=720]/best[height<=720]',
        '480p': 'best[height<=480][height>=480][ext=mp4]/best[height<=480][height>=480]/best[height<=480]',
        '360p': 'best[height<=360][height>=360][ext=mp4]/best[height<=360][height>=360]/best[height<=360]',
        '240p': 'best[height<=240][ext=mp4]/best[height<=240]/worst[height>=240][ext=mp4]/worst[height>=240]/worst',
        '144p': 'best[height<=144][ext=mp4]/best[height<=144]/worst[height>=144][ext=mp4]/worst[height>=144]/worst',
        'audio': 'bestaudio[ext=m4a]/bestaudio[ext=mp3]/bestaudio/best',
        'thumbnail': 'thumbnail'
    },
    'instagram': {
        'best': 'best',
        'video': 'best[ext=mp4]',
        'image': 'best[ext=jpg]',
        'story': 'best'
    }
}

# Admin Panel Configuration
ADMIN_PANEL_CONFIG = {
    'main_admin': 79049016,
    'channel_locked': False,
    'maintenance_mode': False,
    'sponsor_channel_id': None,  # ایدی کانال اسپانسر
    'sponsor_channel_username': None,  # یوزرنیم کانال اسپانسر
    'force_join_enabled': False  # فعال/غیرفعال کردن اجباری جوین
}

# Messages - Persian
MESSAGES = {
    'start': '''🟢 به ربات دانلود از اینستاگرام و یوتیوب خوش آمدید 
  
🟠 برای دانلود از اینستاگرام کافی است لینک پست یا استوری مورد نظر را برای ما ارسال نمایید 
  
🟣 برای دانلود از یوتیوب نیز کافی است لینک مورد نظر را برای ارسال نمایید ؛ طبق دستور زیر، میتونی تو یوتیوب جستجو کنی: 
🔍 به عنوان مثال، برای جستجوی ویدئو ها با کلمه pitbull، تایپ کن 👇 
@vid pitbull''',
    
    'help': '''📋 **راهنمای استفاده:**

🎥 **یوتیوب:**
• هر لینک ویدیو یوتیوب را ارسال کنید
• کیفیت را انتخاب کنید: HD، SD یا فقط صدا
• دانلود خود را با پیگیری پیشرفت دریافت کنید

📸 **اینستاگرام:**
• لینک پست، ریل یا IGTV اینستاگرام ارسال کنید
• ویدیو یا تصاویر را دانلود کنید
• پشتیبانی از محتوای عمومی

⚙️ **دستورات مدیر:**
• `/sessions` - مشاهده جلسات فعال
• `/stats` - آمار ربات
• `/cleanup` - پاکسازی فایل‌های موقت

⚠️ **محدودیت‌ها:**
• حداکثر اندازه فایل: ۵۰ مگابایت
• دانلودهای همزمان: ۳
• محدودیت نرخ اعمال شده''',
    
    'invalid_link': '❌ لینک نامعتبر! لطفاً یک URL معتبر یوتیوب یا اینستاگرام ارسال کنید.',
    'processing': '🔄 در حال پردازش درخواست شما...',
    'downloading': '📥 در حال دانلود... {progress}%',
    'uploading': '📤 در حال آپلود به تلگرام...',
    'success': '✅ دانلود با موفقیت تکمیل شد!',
    'error': '❌ خطایی رخ داد. لطفاً دوباره تلاش کنید.',
    'rate_limited': '⏰ محدودیت نرخ تجاوز شد. لطفاً {seconds} ثانیه صبر کنید.',
    'file_too_large': '📏 فایل خیلی بزرگ است (حداکثر ۱.۵ گیگابایت). کیفیت پایین‌تری امتحان کنید.',
    'no_sessions': '🚫 هیچ جلسه Userbot فعالی در دسترس نیست.',
    'session_error': '⚠️ خطای جلسه. در حال امتحان جلسه دیگر...'
}
