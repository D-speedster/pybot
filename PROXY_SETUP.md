# 🌐 راهنمای تنظیم پروکسی

این راهنما نحوه تنظیم انواع مختلف پروکسی برای بات تلگرام را توضیح می‌دهد.

## 📋 انواع پروکسی پشتیبانی شده

### 1. MTProto Proxy (توصیه شده)
بهترین گزینه برای اتصال به تلگرام در ایران

```env
PROXY_ENABLED=true
PROXY_TYPE=mtproto
PROXY_HOST=14.102.10.175
PROXY_PORT=8443
PROXY_SECRET=eeNEgYdJvXrFGRMCIMJdCQ
```

### 2. SOCKS5 Proxy
```env
PROXY_ENABLED=true
PROXY_TYPE=socks5
PROXY_HOST=127.0.0.1
PROXY_PORT=1080
PROXY_USERNAME=your_username
PROXY_PASSWORD=your_password
```

### 3. HTTP Proxy
```env
PROXY_ENABLED=true
PROXY_TYPE=http
PROXY_HOST=proxy.example.com
PROXY_PORT=8080
PROXY_USERNAME=your_username
PROXY_PASSWORD=your_password
```

## 🔧 نحوه تنظیم

### روش 1: ویرایش فایل .env
1. فایل `.env` را باز کنید
2. تنظیمات پروکسی را مطابق نوع پروکسی خود تغییر دهید
3. بات را مجدداً راه‌اندازی کنید

### روش 2: متغیرهای محیطی
```bash
export PROXY_ENABLED=true
export PROXY_TYPE=mtproto
export PROXY_HOST=14.102.10.175
export PROXY_PORT=8443
export PROXY_SECRET=eeNEgYdJvXrFGRMCIMJdCQ
```

### روش 3: Docker Compose
```yaml
environment:
  - PROXY_ENABLED=true
  - PROXY_TYPE=mtproto
  - PROXY_HOST=14.102.10.175
  - PROXY_PORT=8443
  - PROXY_SECRET=eeNEgYdJvXrFGRMCIMJdCQ
```

## 🔍 تست اتصال پروکسی

### بررسی وضعیت پروکسی
```bash
# لینوکس/مک
./deploy.sh logs

# ویندوز
deploy.bat logs
```

### پیام‌های مربوط به پروکسی در لاگ
- `✅ MTProto proxy configured` - پروکسی MTProto تنظیم شده
- `✅ Proxy connection working` - پروکسی SOCKS5/HTTP کار می‌کند
- `❌ Proxy connection test failed` - خطا در اتصال پروکسی

## 🚨 عیب‌یابی

### مشکلات رایج

#### 1. خطای اتصال به پروکسی
```
❌ Proxy connection test failed
```
**راه‌حل:**
- آدرس و پورت پروکسی را بررسی کنید
- اطمینان حاصل کنید پروکسی فعال است
- فایروال را بررسی کنید

#### 2. خطای MTProto Secret
```
❌ Invalid MTProto secret
```
**راه‌حل:**
- Secret را بدون فاصله و کاراکتر اضافی وارد کنید
- از لینک پروکسی تلگرام Secret را کپی کنید

#### 3. خطای Timeout
```
❌ Connection timeout
```
**راه‌حل:**
- پروکسی دیگری امتحان کنید
- تنظیمات شبکه را بررسی کنید

## 📱 دریافت پروکسی MTProto

### از کانال‌های تلگرام
1. به کانال‌های پروکسی تلگرام مراجعه کنید
2. روی لینک پروکسی کلیک کنید
3. اطلاعات پروکسی را کپی کنید

### فرمت لینک پروکسی تلگرام
```
https://t.me/proxy?server=HOST&port=PORT&secret=SECRET
```

### استخراج اطلاعات از لینک
- `server` → `PROXY_HOST`
- `port` → `PROXY_PORT`  
- `secret` → `PROXY_SECRET`

## ⚡ بهینه‌سازی عملکرد

### تنظیمات پیشرفته
```env
# تعداد تلاش مجدد اتصال
CONNECTION_RETRIES=5

# تاخیر بین تلاش‌ها (ثانیه)
RETRY_DELAY=2

# Timeout اتصال (ثانیه)
CONNECTION_TIMEOUT=30
```

### انتخاب بهترین پروکسی
1. **MTProto**: سریع‌ترین برای تلگرام
2. **SOCKS5**: سازگاری بالا
3. **HTTP**: برای شبکه‌های محدود

## 🔒 امنیت

### نکات امنیتی
- هرگز اطلاعات پروکسی را در کد منبع قرار ندهید
- از متغیرهای محیطی استفاده کنید
- پروکسی‌های قابل اعتماد استفاده کنید
- به‌طور منظم پروکسی را تغییر دهید

### حفاظت از اطلاعات
```bash
# مخفی کردن فایل .env
chmod 600 .env

# اضافه کردن به .gitignore
echo ".env" >> .gitignore
```

## 📞 پشتیبانی

اگر مشکلی در تنظیم پروکسی دارید:
1. لاگ‌های بات را بررسی کنید
2. تنظیمات را دوباره چک کنید
3. پروکسی دیگری امتحان کنید
4. در صورت نیاز، Issue ایجاد کنید

---

**نکته:** پس از تغییر تنظیمات پروکسی، حتماً بات را مجدداً راه‌اندازی کنید.