# راهنمای نصب و اجرای ربات روی لینوکس

## 📋 پیش‌نیازها

### 1. به‌روزرسانی سیستم
```bash
# Ubuntu/Debian
sudo apt update && sudo apt upgrade -y

# CentOS/RHEL/Rocky Linux
sudo yum update -y
# یا برای نسخه‌های جدیدتر:
sudo dnf update -y

# Arch Linux
sudo pacman -Syu
```

### 2. نصب Python 3.8+
```bash
# Ubuntu/Debian
sudo apt install python3 python3-pip python3-venv python3-dev -y

# CentOS/RHEL/Rocky Linux
sudo yum install python3 python3-pip python3-devel -y
# یا:
sudo dnf install python3 python3-pip python3-devel -y

# Arch Linux
sudo pacman -S python python-pip
```

### 3. نصب Git
```bash
# Ubuntu/Debian
sudo apt install git -y

# CentOS/RHEL/Rocky Linux
sudo yum install git -y
# یا:
sudo dnf install git -y

# Arch Linux
sudo pacman -S git
```

### 4. نصب ابزارهای سیستمی مورد نیاز
```bash
# Ubuntu/Debian
sudo apt install build-essential libssl-dev libffi-dev wget curl -y

# CentOS/RHEL/Rocky Linux
sudo yum groupinstall "Development Tools" -y
sudo yum install openssl-devel libffi-devel wget curl -y

# Arch Linux
sudo pacman -S base-devel openssl libffi wget curl
```

## 🚀 مراحل نصب

### 1. کلون کردن پروژه
```bash
# رفتن به دایرکتوری مناسب
cd /opt
# یا
cd ~/

# کلون کردن پروژه
git clone <repository-url> telegram-bot
cd telegram-bot
```

### 2. ایجاد محیط مجازی Python
```bash
# ایجاد محیط مجازی
python3 -m venv venv

# فعال‌سازی محیط مجازی
source venv/bin/activate

# به‌روزرسانی pip
pip install --upgrade pip
```

### 3. نصب وابستگی‌ها
```bash
# نصب پکیج‌های مورد نیاز
pip install -r requirements.txt

# در صورت بروز خطا، نصب جداگانه:
pip install telethon pyrogram psutil asyncio aiofiles
```

### 4. تنظیم فایل محیطی
```bash
# کپی کردن فایل نمونه
cp .env.example .env

# ویرایش فایل تنظیمات
nano .env
# یا
vim .env
```

**محتوای فایل .env:**
```env
# Bot Configuration
BOT_TOKEN=YOUR_BOT_TOKEN_HERE
API_ID=YOUR_API_ID
API_HASH=YOUR_API_HASH

# Admin Configuration
ADMIN_IDS=123456789,987654321
MAIN_ADMIN_ID=123456789

# Database
DATABASE_URL=sqlite:///bot_db.sqlite

# Download Settings
MAX_FILE_SIZE=52428800
MAX_CONCURRENT_DOWNLOADS=3
DOWNLOAD_TIMEOUT=300

# Rate Limiting
RATE_LIMIT_REQUESTS=30
RATE_LIMIT_WINDOW=60

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/bot.log

# Proxy (اختیاری)
# PROXY_ENABLED=false
# PROXY_TYPE=socks5
# PROXY_HOST=127.0.0.1
# PROXY_PORT=1080
```

### 5. ایجاد Session برای Userbot
```bash
# اجرای اسکریپت ایجاد session
python session_creator.py

# وارد کردن شماره تلفن و کد تأیید
# فایل session در پوشه sessions/ ذخیره می‌شود
```

### 6. ایجاد دایرکتوری‌های مورد نیاز
```bash
# ایجاد پوشه‌های لازم
mkdir -p logs
mkdir -p Downloads
mkdir -p temp_downloads
mkdir -p sessions

# تنظیم مجوزها
chmod 755 logs Downloads temp_downloads sessions
```

## 🔧 اجرای ربات

### 1. اجرای دستی (برای تست)
```bash
# فعال‌سازی محیط مجازی
source venv/bin/activate

# اجرای ربات
python main.py
```

### 2. اجرا با Screen (برای اجرای پس‌زمینه)
```bash
# نصب screen
sudo apt install screen -y  # Ubuntu/Debian
sudo yum install screen -y  # CentOS/RHEL

# ایجاد session جدید
screen -S telegram-bot

# فعال‌سازی محیط مجازی و اجرا
source venv/bin/activate
python main.py

# خروج از screen (Ctrl+A سپس D)
# بازگشت به screen: screen -r telegram-bot
```

### 3. اجرا با tmux
```bash
# نصب tmux
sudo apt install tmux -y  # Ubuntu/Debian
sudo yum install tmux -y  # CentOS/RHEL

# ایجاد session جدید
tmux new-session -d -s telegram-bot

# اتصال به session
tmux attach-session -t telegram-bot

# اجرای ربات
source venv/bin/activate
python main.py

# خروج: Ctrl+B سپس D
```

## 🔄 تنظیم سرویس systemd (پیشنهادی)

### 1. ایجاد فایل سرویس
```bash
sudo nano /etc/systemd/system/telegram-bot.service
```

### 2. محتوای فایل سرویس
```ini
[Unit]
Description=Telegram YouTube/Instagram Bot
After=network.target
Wants=network.target

[Service]
Type=simple
User=YOUR_USERNAME
Group=YOUR_GROUP
WorkingDirectory=/path/to/your/bot
Environment=PATH=/path/to/your/bot/venv/bin
ExecStart=/path/to/your/bot/venv/bin/python main.py
Restart=always
RestartSec=10
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true
NoNewPrivileges=true

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=telegram-bot

[Install]
WantedBy=multi-user.target
```

### 3. فعال‌سازی سرویس
```bash
# بارگذاری مجدد systemd
sudo systemctl daemon-reload

# فعال‌سازی سرویس
sudo systemctl enable telegram-bot.service

# شروع سرویس
sudo systemctl start telegram-bot.service

# بررسی وضعیت
sudo systemctl status telegram-bot.service

# مشاهده لاگ‌ها
sudo journalctl -u telegram-bot.service -f
```

## 🐳 اجرا با Docker (اختیاری)

### 1. نصب Docker
```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# راه‌اندازی مجدد یا logout/login
newgrp docker
```

### 2. ساخت و اجرای کانتینر
```bash
# ساخت image
docker build -t telegram-bot .

# اجرای کانتینر
docker run -d --name telegram-bot \
  --restart unless-stopped \
  -v $(pwd)/.env:/app/.env \
  -v $(pwd)/sessions:/app/sessions \
  -v $(pwd)/Downloads:/app/Downloads \
  -v $(pwd)/logs:/app/logs \
  telegram-bot

# مشاهده لاگ‌ها
docker logs -f telegram-bot
```

### 3. استفاده از Docker Compose
```bash
# اجرا با docker-compose
docker-compose up -d

# مشاهده لاگ‌ها
docker-compose logs -f

# توقف
docker-compose down
```

## 🔧 تنظیمات امنیتی

### 1. تنظیم Firewall
```bash
# Ubuntu/Debian (UFW)
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# CentOS/RHEL (firewalld)
sudo systemctl enable firewalld
sudo systemctl start firewalld
sudo firewall-cmd --permanent --add-service=ssh
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

### 2. ایجاد کاربر جداگانه
```bash
# ایجاد کاربر برای ربات
sudo useradd -m -s /bin/bash botuser
sudo passwd botuser

# انتقال فایل‌ها
sudo mv /path/to/bot /home/botuser/
sudo chown -R botuser:botuser /home/botuser/bot

# اجرا با کاربر جدید
sudo -u botuser -i
cd bot
```

## 📊 مانیتورینگ و نگهداری

### 1. مشاهده لاگ‌ها
```bash
# لاگ‌های سیستم
sudo journalctl -u telegram-bot.service -f

# لاگ‌های فایل
tail -f logs/bot.log
tail -f logs/errors.log
```

### 2. بک‌آپ
```bash
# اسکریپت بک‌آپ
#!/bin/bash
BACKUP_DIR="/backup/telegram-bot"
SOURCE_DIR="/path/to/bot"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR
tar -czf $BACKUP_DIR/bot_backup_$DATE.tar.gz \
  --exclude='venv' \
  --exclude='temp_downloads' \
  --exclude='__pycache__' \
  $SOURCE_DIR

# حذف بک‌آپ‌های قدیمی (بیش از 7 روز)
find $BACKUP_DIR -name "bot_backup_*.tar.gz" -mtime +7 -delete
```

### 3. به‌روزرسانی
```bash
# توقف سرویس
sudo systemctl stop telegram-bot.service

# بک‌آپ
cp -r /path/to/bot /path/to/bot_backup_$(date +%Y%m%d)

# به‌روزرسانی کد
cd /path/to/bot
git pull origin main

# به‌روزرسانی وابستگی‌ها
source venv/bin/activate
pip install -r requirements.txt --upgrade

# شروع مجدد سرویس
sudo systemctl start telegram-bot.service
```

## 🚨 عیب‌یابی

### مشکلات رایج:

1. **خطای Permission Denied:**
```bash
chmod +x main.py
chown -R $USER:$USER /path/to/bot
```

2. **خطای Python Module:**
```bash
source venv/bin/activate
pip install --upgrade -r requirements.txt
```

3. **خطای Database:**
```bash
rm bot_db.sqlite
python main.py  # دیتابیس جدید ایجاد می‌شود
```

4. **مشکل Session:**
```bash
rm sessions/*.session
python session_creator.py
```

### بررسی وضعیت سیستم:
```bash
# استفاده از حافظه
free -h

# استفاده از دیسک
df -h

# پردازش‌های در حال اجرا
ps aux | grep python

# پورت‌های باز
netstat -tlnp
```

## 📞 پشتیبانی

در صورت بروز مشکل:
1. لاگ‌های خطا را بررسی کنید
2. فایل تنظیمات را چک کنید
3. وضعیت شبکه را بررسی کنید
4. با مدیر سیستم تماس بگیرید

---

**نکته مهم:** این راهنما برای استفاده شخصی و آموزشی طراحی شده است. لطفاً قوانین و مقررات پلتفرم‌های مربوطه را رعایت کنید.