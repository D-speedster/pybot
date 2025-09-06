# 🚀 راه‌اندازی با یک دستور

## ⚡ راه‌اندازی فوری (30 ثانیه)

### Linux/macOS:
```bash
curl -sSL https://raw.githubusercontent.com/your-repo/telegram-bot/main/quick-start.sh | bash
```

### یا دانلود و اجرا:
```bash
wget https://github.com/your-repo/telegram-bot/archive/main.zip
unzip main.zip
cd telegram-bot-main
chmod +x quick-start.sh
./quick-start.sh
```

### Windows:
```powershell
# دانلود و اجرا
Invoke-WebRequest -Uri "https://github.com/your-repo/telegram-bot/archive/main.zip" -OutFile "bot.zip"
Expand-Archive -Path "bot.zip" -DestinationPath "."
cd telegram-bot-main
.\deploy.bat start
```

## 🎯 دستورات سریع

### با Make (توصیه شده):
```bash
# راه‌اندازی کامل
make quick

# مدیریت
make start    # شروع
make stop     # توقف
make logs     # لاگ‌ها
make status   # وضعیت
```

### با اسکریپت Deploy:
```bash
# راه‌اندازی
./deploy.sh start

# مدیریت
./deploy.sh stop
./deploy.sh restart
./deploy.sh logs
./deploy.sh status
./deploy.sh backup
```

### با Docker Compose مستقیم:
```bash
# ساده
docker-compose up -d

# تولید
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

## ⚙️ تنظیم سریع

### 1. کپی و ویرایش .env:
```bash
cp .env.example .env
nano .env
```

### 2. تنظیم متغیرهای ضروری:
```env
BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
API_ID=12345678
API_HASH=abcdef1234567890abcdef1234567890
ADMIN_IDS=123456789,987654321
```

### 3. شروع:
```bash
./deploy.sh start
```

## 🔧 دستورات مفید

### نظارت:
```bash
# لاگ‌های زنده
docker-compose logs -f

# وضعیت منابع
docker stats

# سلامت بات
docker inspect --format='{{.State.Health.Status}}' telegram-userbot-downloader
```

### عیب‌یابی:
```bash
# بررسی تنظیمات
docker-compose config

# ورود به کانتینر
docker-compose exec telegram-bot bash

# مشاهده لاگ‌های خطا
docker-compose logs | grep -i error
```

### پشتیبان‌گیری:
```bash
# پشتیبان‌گیری خودکار
./deploy.sh backup

# یا دستی
tar -czf backup_$(date +%Y%m%d).tar.gz sessions/ logs/ userbot_manager.db .env
```

## 🌐 استقرار روی سرور

### VPS/Cloud Server:
```bash
# اتصال به سرور
ssh user@your-server.com

# نصب Docker (Ubuntu/Debian)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# دانلود پروژه
git clone https://github.com/your-repo/telegram-bot.git
cd telegram-bot

# راه‌اندازی
./quick-start.sh
```

### با Docker Machine:
```bash
# ایجاد ماشین
docker-machine create --driver digitalocean --digitalocean-access-token=YOUR_TOKEN telegram-bot

# تنظیم محیط
eval $(docker-machine env telegram-bot)

# استقرار
docker-compose up -d
```

## 🔄 به‌روزرسانی

### به‌روزرسانی ساده:
```bash
./deploy.sh update
```

### به‌روزرسانی دستی:
```bash
git pull
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

## 📊 مانیتورینگ

### نصب Portainer (اختیاری):
```bash
docker volume create portainer_data
docker run -d -p 8000:8000 -p 9000:9000 --name=portainer --restart=always -v /var/run/docker.sock:/var/run/docker.sock -v portainer_data:/data portainer/portainer-ce
```

### Grafana + Prometheus (پیشرفته):
```bash
# اضافه کردن به docker-compose.yml
services:
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
  
  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
```

## 🛡️ امنیت

### تنظیم Firewall:
```bash
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443
```

### SSL با Let's Encrypt:
```bash
sudo apt install certbot nginx
sudo certbot --nginx -d yourdomain.com
```

### محدودیت دسترسی:
```bash
chmod 600 .env
chmod 700 sessions/
sudo chown -R $USER:$USER .
```

## ❗ عیب‌یابی سریع

### بات شروع نمی‌شود:
```bash
# 1. بررسی Docker
docker --version
docker-compose --version

# 2. بررسی .env
cat .env | grep -E "BOT_TOKEN|API_ID|API_HASH"

# 3. بررسی لاگ‌ها
docker-compose logs --tail=50
```

### خطای اتصال:
```bash
# بررسی شبکه
ping telegram.org

# بررسی DNS
nslookup api.telegram.org

# تست پورت
telnet api.telegram.org 443
```

### کمبود منابع:
```bash
# بررسی فضای دیسک
df -h

# بررسی RAM
free -h

# پاک‌سازی
docker system prune -a
```

## 📞 پشتیبانی

### لاگ‌های مهم:
- `logs/bot.log` - لاگ‌های عمومی
- `logs/errors.log` - خطاها
- `logs/downloads.log` - دانلودها
- `logs/sessions.log` - جلسات

### دستورات تشخیصی:
```bash
# وضعیت کامل سیستم
./deploy.sh status

# تست اتصال
curl -s https://api.telegram.org/bot$BOT_TOKEN/getMe

# بررسی منابع
docker stats --no-stream
```

---

## 🎉 تبریک!

بات شما آماده است! 

**دستورات اصلی:**
- `./deploy.sh start` - شروع
- `./deploy.sh logs` - مشاهده لاگ‌ها  
- `./deploy.sh status` - وضعیت
- `./deploy.sh stop` - توقف

**مستندات:**
- [SETUP_GUIDE.md](SETUP_GUIDE.md) - راهنمای کامل
- [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) - راهنمای استقرار
- [README.md](README.md) - اطلاعات پروژه

**🚀 با یک دستور همه چیز آماده است!**