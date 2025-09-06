# Telegram Video Downloader Bot

A powerful, multi-session Telegram bot for downloading videos from YouTube and Instagram with advanced features like load balancing, proxy support, and comprehensive admin controls.

## 🚀 Features

### Core Functionality
- **Multi-Platform Support**: Download from YouTube and Instagram
- **Quality Selection**: HD, SD, and Audio-only options
- **Progress Tracking**: Real-time download and upload progress
- **Multiple Sessions**: Load-balanced Userbot sessions to avoid rate limits
- **Network Reliability**: Proxy support with automatic failover

### Advanced Features
- **Session Management**: Add/remove Userbot sessions dynamically
- **Admin Panel**: Comprehensive administrative controls
- **Statistics**: Detailed usage and performance metrics
- **Health Monitoring**: Automatic session health checks
- **Database Integration**: SQLite database for user and download tracking
- **Logging System**: Comprehensive logging with rotation
- **Cleanup Tools**: Automatic temporary file management

### User Interface
- **Intuitive Commands**: Simple `/start` and `/help` commands
- **Interactive Menus**: Quality selection with inline keyboards
- **Progress Indicators**: Visual progress bars and status updates
- **Error Handling**: Clear error messages and troubleshooting

## 📋 Requirements

- Python 3.8+
- Telegram Bot Token
- Telegram API credentials (API_ID, API_HASH)
- At least one Telegram account for Userbot sessions

## 🚀 نصب و راه‌اندازی

### 🎯 راه‌اندازی سریع (یک دستور)

**Linux/macOS:**
```bash
# دانلود و راه‌اندازی با یک دستور
chmod +x quick-start.sh && ./quick-start.sh
```

**Windows:**
```cmd
# راه‌اندازی با Docker
deploy.bat start
```

### 📋 پیش‌نیازها
- Docker & Docker Compose
- حساب کاربری تلگرام
- Bot Token از @BotFather
- API credentials از my.telegram.org

### 🔧 راه‌اندازی دستی

#### 1. آماده‌سازی محیط
```bash
# کلون پروژه
git clone <repository-url>
cd telegram-userbot-downloader

# تنظیم متغیرهای محیطی
cp .env.example .env
nano .env  # ویرایش کردن
```

#### 2. تنظیم کانفیگ (.env)
```env
BOT_TOKEN=your_bot_token_here
API_ID=your_api_id_here
API_HASH=your_api_hash_here
ADMIN_IDS=123456789,987654321
```

#### 3. راه‌اندازی
```bash
# با Docker (توصیه شده)
./deploy.sh start

# یا به صورت مستقیم
pip install -r requirements.txt
python main.py
```

## 📱 استفاده از بات

### دستورات اصلی:
- `/start` - شروع بات و نمایش منوی اصلی
- `/help` - راهنمای استفاده
- `/status` - وضعیت بات و آمار
- `/sessions` - مدیریت جلسات Userbot
- `/settings` - تنظیمات بات

### دستورات ادمین:
- `/admin` - پنل مدیریت
- `/add_session` - اضافه کردن جلسه جدید
- `/remove_session` - حذف جلسه
- `/list_sessions` - لیست جلسات فعال
- `/stats` - آمار کامل سیستم
- `/logs` - مشاهده لاگ‌ها

### نحوه دانلود:
1. لینک ویدیو را در چت ارسال کنید
2. کیفیت مورد نظر را انتخاب کنید
3. منتظر تکمیل دانلود باشید
4. فایل به صورت خودکار ارسال می‌شود

## 🔧 مدیریت و نظارت

### دستورات مدیریت:
```bash
# شروع بات
./deploy.sh start

# توقف بات
./deploy.sh stop

# راه‌اندازی مجدد
./deploy.sh restart

# مشاهده لاگ‌ها
./deploy.sh logs

# وضعیت بات
./deploy.sh status

# به‌روزرسانی
./deploy.sh update

# پشتیبان‌گیری
./deploy.sh backup

# پاک‌سازی
./deploy.sh cleanup
```

### نظارت بر عملکرد:
```bash
# مشاهده منابع مصرفی
docker stats telegram-userbot-downloader

# بررسی سلامت کانتینر
docker inspect --format='{{.State.Health.Status}}' telegram-userbot-downloader

# مشاهده لاگ‌های زنده
docker-compose logs -f
```

### For Users

1. **Start the bot**: Send `/start` to get welcome message
2. **Get help**: Send `/help` for usage instructions
3. **Download videos**: Send a YouTube or Instagram URL
4. **Select quality**: Choose from HD, SD, or Audio-only options
5. **Wait for download**: Monitor progress and receive the file

### For Admins

#### Session Management
```
/admin - Access admin panel
/sessions - View all session status
/add_session - Add new Userbot session
/remove_session <name> - Remove a session
/test_session <name> - Test session connectivity
```

#### Monitoring
```
/stats - Bot usage statistics
/health - System health check
/system - System resource information
/logs - View log file information
```

#### Maintenance
```
/cleanup - Clean temporary files
/backup - Backup database
/restart - Restart bot (if supported)
```

## 🏗️ Project Structure

```
amir/
├── main.py                 # Main entry point
├── config.py              # Configuration settings
├── requirements.txt       # Python dependencies
├── README.md             # This file
│
├── handlers/             # Command handlers
│   ├── __init__.py
│   ├── bot_handlers.py   # User command handlers
│   └── admin_handlers.py # Admin command handlers
│
├── services/             # Core services
│   ├── __init__.py
│   ├── session_manager.py # Userbot session management
│   └── download_service.py # Download handling
│
├── utils/                # Utility modules
│   ├── __init__.py
│   ├── database.py       # Database operations
│   ├── network.py        # Network utilities
│   ├── logging_config.py # Logging configuration
│   └── helpers.py        # Helper functions
│
├── sessions/             # Userbot session files
├── downloads/            # Temporary download directory
└── logs/                 # Log files
```

## 🔧 Configuration Options

### Database Configuration
```python
DATABASE_CONFIG = {
    'name': 'bot_database.db',
    'tables': {
        'users': 'CREATE TABLE IF NOT EXISTS users (...)',
        'downloads': 'CREATE TABLE IF NOT EXISTS downloads (...)',
        'sessions': 'CREATE TABLE IF NOT EXISTS sessions (...)'
    }
}
```

### Download Configuration
```python
DOWNLOAD_CONFIG = {
    'temp_dir': 'downloads',
    'max_file_size': 2 * 1024 * 1024 * 1024,  # 2GB
    'quality_options': ['hd', 'sd', 'audio'],
    'cleanup_after_hours': 24
}
```

### Session Configuration
```python
SESSION_CONFIG = {
    'sessions_dir': 'sessions',
    'max_sessions': 10,
    'load_balancing': 'round_robin',  # or 'least_used'
    'health_check_interval': 300
}
```

### Logging Configuration
```python
LOGGING_CONFIG = {
    'level': 'INFO',
    'log_dir': 'logs',
    'max_file_size': 10 * 1024 * 1024,  # 10MB
    'backup_count': 5
}
```

## 🔒 Security Features

- **Admin-only commands**: Restricted access to administrative functions
- **Session isolation**: Each Userbot session runs independently
- **Secure file handling**: Temporary files are automatically cleaned
- **Error logging**: Comprehensive error tracking without exposing sensitive data
- **Rate limiting**: Built-in protection against API rate limits

## 🛡️ امنیت و بهینه‌سازی

### تنظیمات امنیتی:
```bash
# محدودیت دسترسی به فایل‌های حساس
chmod 600 .env
chmod 700 sessions/

# تنظیم Firewall
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443
```

### بهینه‌سازی عملکرد:
```yaml
# در docker-compose.yml
deploy:
  resources:
    limits:
      memory: 1G
      cpus: '1.0'
    reservations:
      memory: 512M
      cpus: '0.5'
```

## ❗ عیب‌یابی

### مشکلات رایج:

**1. بات شروع نمی‌شود:**
```bash
# بررسی لاگ‌ها
./deploy.sh logs

# بررسی تنظیمات
docker-compose config

# بررسی وضعیت Docker
docker ps -a
```

**2. خطای اتصال به تلگرام:**
- بررسی صحت `BOT_TOKEN`, `API_ID`, `API_HASH`
- بررسی اتصال اینترنت
- بررسی تنظیمات Proxy در `.env`

**3. کمبود فضای دیسک:**
```bash
# پاک‌سازی فایل‌های اضافی
docker system prune -a

# پاک‌سازی دانلودهای قدیمی
find temp_downloads/ -mtime +1 -delete

# پاک‌سازی لاگ‌های قدیمی
find logs/ -name "*.log" -mtime +7 -delete
```

**4. مشکل در دانلود:**
- بررسی محدودیت‌های شبکه
- بررسی تنظیمات `MAX_FILE_SIZE`
- بررسی وضعیت جلسات Userbot

### لاگ‌های مفید:
```bash
# لاگ‌های عمومی
tail -f logs/bot.log

# لاگ‌های دانلود
tail -f logs/downloads.log

# لاگ‌های خطا
tail -f logs/errors.log

# لاگ‌های جلسات
tail -f logs/sessions.log
```

## 🚨 Troubleshooting

### Common Issues

#### Connection Errors
```
❌ ConnectionRefusedError: [WinError 1225]
```
**Solution**: Enable proxy in `config.py` or check network connectivity

#### Session Authorization
```
❌ Session not authorized
```
**Solution**: Use `/add_session` command to properly authorize Userbot sessions

#### Download Failures
```
❌ Download failed: Video unavailable
```
**Solution**: Check if the video is public and the URL is correct

### Network Issues

1. **Test connectivity**:
   ```bash
   python -c "from utils.network import NetworkUtils; import asyncio; asyncio.run(NetworkUtils.comprehensive_network_test())"
   ```

2. **Configure proxy** in `config.py` if behind firewall

3. **Check session health** using `/health` admin command

### Performance Optimization

- **Add more sessions**: Use `/add_session` to distribute load
- **Monitor resources**: Use `/system` to check memory and disk usage
- **Clean regularly**: Use `/cleanup` to remove old files
- **Check logs**: Use `/logs` to identify bottlenecks

## 📊 Monitoring and Analytics

### Built-in Statistics
- User activity tracking
- Download success/failure rates
- Session usage statistics
- Platform-specific metrics
- System resource monitoring

### Log Files
- `bot.log`: General bot operations
- `errors.log`: Error tracking
- `downloads.log`: Download activity
- `sessions.log`: Session management

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## ⚠️ Disclaimer

- This bot is for educational purposes only
- Respect platform terms of service
- Ensure you have rights to download content
- Use responsibly and ethically

## 🆘 Support

For support and questions:
1. Check the troubleshooting section
2. Review log files for errors
3. Use admin commands for diagnostics
4. Create an issue on GitHub

---

**Made with ❤️ for the Telegram community**#   p y b o t  
 