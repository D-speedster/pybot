# 🍪 راهنمای استخراج کوکی‌های یوتیوب در لینوکس/اوبونتو

## ⚠️ مشکل فعلی
خطای "Sign in to confirm you're not a bot" در سرور لینوکس به دلیل منقضی شدن کوکی‌های احراز هویت یوتیوب.

## 🐧 راه‌حل برای لینوکس/اوبونتو

### روش 1: استخراج از مرورگر Firefox (پیشنهادی)

#### مرحله 1: نصب Firefox و ورود به یوتیوب
```bash
# نصب Firefox (اگر نصب نیست)
sudo apt update
sudo apt install firefox

# اجرای Firefox
firefox &
```

#### مرحله 2: ورود به یوتیوب
1. به `https://www.youtube.com` بروید
2. وارد اکانت یوتیوب خود شوید
3. مطمئن شوید کاملاً وارد شده‌اید

#### مرحله 3: استخراج کوکی‌ها
1. کلید `F12` را فشار دهید
2. به تب **"Storage"** بروید
3. **"Cookies"** را گسترش دهید
4. روی `https://www.youtube.com` کلیک کنید

### روش 2: استخراج از Chrome در لینوکس

#### نصب Google Chrome:
```bash
# دانلود و نصب Chrome
wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" | sudo tee /etc/apt/sources.list.d/google-chrome.list
sudo apt update
sudo apt install google-chrome-stable

# اجرای Chrome
google-chrome &
```

#### استخراج کوکی‌ها:
1. به `https://www.youtube.com` بروید و وارد شوید
2. `F12` → **"Application"** → **"Cookies"** → `https://www.youtube.com`

### روش 3: استخراج خودکار با اسکریپت (پیشرفته)

#### نصب browser_cookie3:
```bash
pip3 install browser_cookie3
```

#### اجرای اسکریپت استخراج:
```bash
# اجرای اسکریپت موجود
python3 extract_cookies.py --browser firefox
# یا
python3 extract_cookies.py --browser chrome
```

### 🔑 کوکی‌های ضروری برای استخراج:
- **SAPISID** - مهمترین کوکی برای احراز هویت
- **HSID** - شناسه جلسه HTTP
- **SSID** - شناسه جلسه امن  
- **APISID** - شناسه جلسه API
- **LOGIN_INFO** - اطلاعات ورود
- **session_token** - توکن جلسه

### 📝 جایگزینی کوکی‌ها در سرور

#### مرحله 1: ویرایش فایل cookies.txt
```bash
# ویرایش فایل کوکی
nano cookies.txt
# یا
vim cookies.txt
```

#### مرحله 2: جایگزینی مقادیر
خطوط زیر را پیدا کرده و مقادیر را جایگزین کنید:
```
.youtube.com	TRUE	/	TRUE	1772648989	SAPISID	REPLACE_WITH_YOUR_SAPISID_VALUE
.youtube.com	TRUE	/	TRUE	1772648989	HSID	REPLACE_WITH_YOUR_HSID_VALUE
.youtube.com	TRUE	/	TRUE	1772648989	SSID	REPLACE_WITH_YOUR_SSID_VALUE
.youtube.com	TRUE	/	TRUE	1772648989	APISID	REPLACE_WITH_YOUR_APISID_VALUE
.youtube.com	TRUE	/	TRUE	1772648989	LOGIN_INFO	REPLACE_WITH_YOUR_LOGIN_INFO_VALUE
```

### 🔄 حل مشکل Git Pull

اگر هنگام `git pull` خطای تداخل فایل cookies.txt دریافت کردید:

```bash
# ذخیره تغییرات محلی
git stash push -m "backup local cookies" cookies.txt

# دریافت آخرین تغییرات
git pull

# بازگردانی کوکی‌های محلی (اختیاری)
git stash pop
# یا نگه داشتن نسخه جدید و ویرایش دستی
```

### 🚀 ری‌استارت سرویس

بعد از به‌روزرسانی کوکی‌ها:

```bash
# اگر از systemd استفاده می‌کنید
sudo systemctl restart youtube-bot

# اگر از Docker استفاده می‌کنید
docker-compose restart

# اگر به صورت دستی اجرا می‌کنید
pkill -f "python.*main.py"
python3 main.py &
```

### 🔍 تست کوکی‌ها

```bash
# تست دانلود یک ویدیو کوتاه
yt-dlp --cookies cookies.txt "https://www.youtube.com/watch?v=dQw4w9WgXcQ" --simulate
```

## ⚠️ نکات مهم برای سرور:

1. **امنیت کوکی‌ها:**
   ```bash
   # تنظیم مجوزهای فایل
   chmod 600 cookies.txt
   chown $USER:$USER cookies.txt
   ```

2. **بک‌آپ کوکی‌ها:**
   ```bash
   # بک‌آپ گیری
   cp cookies.txt cookies.txt.backup.$(date +%Y%m%d)
   ```

3. **مانیتورینگ انقضا:**
   ```bash
   # بررسی تاریخ انقضا کوکی‌ها
   grep -E "SAPISID|HSID|SSID|APISID" cookies.txt
   ```

## 🔧 عیب‌یابی:

### اگر همچنان خطا دریافت می‌کنید:

1. **بررسی فرمت فایل:**
   ```bash
   file cookies.txt
   # باید نتیجه: ASCII text باشد
   ```

2. **بررسی مجوزها:**
   ```bash
   ls -la cookies.txt
   ```

3. **بررسی لاگ‌ها:**
   ```bash
   tail -f logs/bot.log
   tail -f logs/errors.log
   ```

4. **تست اتصال:**
   ```bash
   curl -b cookies.txt "https://www.youtube.com" -I
   ```

### خطاهای رایج:

- **"Permission denied"**: `chmod 644 cookies.txt`
- **"Invalid cookie format"**: بررسی تب‌ها و فاصله‌ها
- **"Expired cookies"**: استخراج مجدد کوکی‌ها

## 📞 کمک اضافی:

اگر همچنان مشکل دارید:
1. اسکرین‌شات از کوکی‌های مرورگر بگیرید
2. محتوای فایل cookies.txt را بررسی کنید
3. لاگ‌های خطا را ارسال کنید