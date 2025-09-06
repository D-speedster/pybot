# 🚀 راهنمای استقرار بات تلگرام

این راهنما به شما کمک می‌کند تا بات تلگرام را با یک دستور ساده روی سرور راه‌اندازی کنید.

## 📋 پیش‌نیازها

### 1. نصب Docker
```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# CentOS/RHEL
sudo yum install -y docker
sudo systemctl start docker
sudo systemctl enable docker
```

### 2. نصب Docker Compose
```bash
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

## 🔧 تنظیمات اولیه

### 1. آپلود پروژه به سرور
```bash
# با استفاده از git
git clone <repository-url>
cd telegram-userbot-downloader

# یا آپلود مستقیم فایل‌ها
scp -r ./amir user@server:/path/to/project
```

### 2. تنظیم متغیرهای محیطی
```bash
# کپی فایل نمونه
cp .env.example .env

# ویرایش فایل .env
nano .env
```

**متغیرهای ضروری:**
```env
BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
API_ID=12345678
API_HASH=abcdef1234567890abcdef1234567890
ADMIN_IDS=123456789,987654321
```

## 🚀 راه‌اندازی با یک دستور

### Linux/macOS:
```bash
# اجازه اجرا به اسکریپت
chmod +x deploy.sh

# شروع بات
./deploy.sh start
```

### Windows:
```cmd
# شروع بات
deploy.bat start
```

## 📊 مدیریت بات

### دستورات اصلی:
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

# پاک‌سازی
./deploy.sh cleanup

# پشتیبان‌گیری
./deploy.sh backup
```

## 🔍 نظارت و عیب‌یابی

### مشاهده لاگ‌ها:
```bash
# لاگ‌های زنده
docker-compose logs -f

# لاگ‌های اخیر
docker-compose logs --tail=100

# لاگ‌های خاص
docker-compose logs telegram-bot
```

### بررسی وضعیت:
```bash
# وضعیت کانتینر
docker-compose ps

# استفاده از منابع
docker stats

# سلامت کانتینر
docker inspect --format='{{.State.Health.Status}}' telegram-userbot-downloader
```

## 🔧 تنظیمات پیشرفته

### 1. تنظیم Proxy
```env
PROXY_ENABLED=true
PROXY_TYPE=socks5
PROXY_HOST=your-proxy-host
PROXY_PORT=1080
PROXY_USERNAME=username
PROXY_PASSWORD=password
```

### 2. محدودیت منابع
```yaml
# در docker-compose.yml
deploy:
  resources:
    limits:
      memory: 1G
      cpus: '1.0'
```

### 3. تنظیم SSL (اختیاری)
```bash
# نصب Nginx
sudo apt install nginx

# تنظیم SSL با Let's Encrypt
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com
```

## 🔄 به‌روزرسانی خودکار

### تنظیم Cron Job:
```bash
# ویرایش crontab
crontab -e

# اضافه کردن خط زیر برای به‌روزرسانی روزانه در ساعت 3 صبح
0 3 * * * cd /path/to/project && ./deploy.sh update
```

## 📁 ساختار فایل‌ها

```
project/
├── Dockerfile              # تصویر Docker
├── docker-compose.yml      # تنظیمات سرویس‌ها
├── .env                    # متغیرهای محیطی
├── deploy.sh              # اسکریپت استقرار (Linux/Mac)
├── deploy.bat             # اسکریپت استقرار (Windows)
├── .dockerignore          # فایل‌های نادیده گرفته شده
├── sessions/              # فایل‌های جلسه
├── logs/                  # فایل‌های لاگ
├── temp_downloads/        # دانلودهای موقت
└── userbot_manager.db     # پایگاه داده
```

## 🛡️ امنیت

### 1. تنظیم Firewall:
```bash
# Ubuntu/Debian
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443
```

### 2. محدودیت دسترسی:
```bash
# تنظیم مالکیت فایل‌ها
sudo chown -R $USER:$USER /path/to/project
chmod 600 .env
```

### 3. پشتیبان‌گیری خودکار:
```bash
# اسکریپت پشتیبان‌گیری روزانه
0 2 * * * cd /path/to/project && ./deploy.sh backup
```

## ❗ عیب‌یابی رایج

### مشکل: کانتینر شروع نمی‌شود
```bash
# بررسی لاگ‌ها
docker-compose logs

# بررسی تنظیمات
docker-compose config
```

### مشکل: خطای اتصال به تلگرام
- بررسی صحت `BOT_TOKEN`, `API_ID`, `API_HASH`
- بررسی اتصال اینترنت
- بررسی تنظیمات Proxy

### مشکل: کمبود فضای دیسک
```bash
# پاک‌سازی فایل‌های اضافی
docker system prune -a

# پاک‌سازی لاگ‌های قدیمی
find logs/ -name "*.log" -mtime +7 -delete
```

## 📞 پشتیبانی

در صورت بروز مشکل:
1. لاگ‌ها را بررسی کنید
2. تنظیمات `.env` را چک کنید
3. وضعیت Docker را بررسی کنید
4. از دستور `./deploy.sh status` استفاده کنید

---

**نکته:** این بات به صورت خودکار راه‌اندازی می‌شود و نیازی به مداخله دستی ندارد. فقط کافی است متغیرهای محیطی را تنظیم کرده و دستور `./deploy.sh start` را اجرا کنید.