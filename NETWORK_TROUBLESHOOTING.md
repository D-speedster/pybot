# 🔧 راهنمای حل مشکل اتصال به تلگرام

## 🚨 مشکل اصلی: فیلتر بودن تلگرام در ایران

خطای `WinError 10061: No connection could be made because the target machine actively refused it` نشان‌دهنده فیلتر بودن دسترسی به سرورهای تلگرام است.

## ✅ راه‌حل‌های پیشنهادی (به ترتیب اولویت)

### 1. استفاده از VPN (بهترین راه‌حل)

**VPN های رایگان پیشنهادی:**
- Psiphon
- Windscribe
- ProtonVPN
- TunnelBear

**مراحل:**
1. یکی از VPN های بالا را نصب کنید
2. VPN را روشن کنید
3. بات را دوباره اجرا کنید:
   ```bash
   python __main__.py
   ```

### 2. استفاده از پروکسی محلی

اگر پروکسی محلی دارید:

1. در فایل `__main__.py` مقدار `USE_PROXY` را `True` کنید
2. تنظیمات پروکسی را اصلاح کنید:
   ```python
   proxies = dict(
       scheme="http",  # یا "socks5"
       hostname="127.0.0.1",
       port=8080,  # پورت پروکسی شما
   )
   ```

### 3. استفاده از DNS های آزاد

**تغییر DNS به:**
- Cloudflare: `1.1.1.1` و `1.0.0.1`
- Google: `8.8.8.8` و `8.8.4.4`
- Quad9: `9.9.9.9` و `149.112.112.112`

**مراحل تغییر DNS در ویندوز:**
1. Control Panel → Network and Internet → Network Connections
2. راست‌کلیک روی اتصال شبکه → Properties
3. Internet Protocol Version 4 (TCP/IPv4) → Properties
4. "Use the following DNS server addresses" را انتخاب کنید
5. DNS های بالا را وارد کنید

### 4. غیرفعال کردن فایروال و آنتی‌ویروس (موقت)

**هشدار:** این کار را فقط برای تست انجام دهید

1. Windows Defender Firewall را موقتاً غیرفعال کنید
2. آنتی‌ویروس را موقتاً غیرفعال کنید
3. بات را تست کنید
4. بعد از تست، فایروال و آنتی‌ویروس را دوباره فعال کنید

## 🔍 تست اتصال

برای تست سریع اتصال:

```bash
python simple_test.py
```

یا برای تست کامل:

```bash
python fix_connection.py
```

## ⚙️ تنظیمات اضافی

### نصب TgCrypto (اختیاری)

برای بهبود سرعت، TgCrypto را نصب کنید:

**پیش‌نیاز:** Microsoft Visual C++ Build Tools

1. [Microsoft C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/) را دانلود و نصب کنید
2. سپس TgCrypto را نصب کنید:
   ```bash
   pip install TgCrypto
   ```

### بررسی تنظیمات config.py

مطمئن شوید که:
- `BOT_TOKEN` صحیح است
- `API_ID` و `API_HASH` از my.telegram.org دریافت شده‌اند
- هیچ کاراکتر اضافی یا فاصله وجود ندارد

## 🌐 راه‌حل‌های جایگزین

### استفاده از Bot API به جای MTProto

اگر همچنان مشکل دارید، می‌توانید از Bot API استفاده کنید:

```python
import requests

def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": text
    }
    response = requests.post(url, data=data)
    return response.json()
```

### استفاده از سرور خارجی

اگر امکان دارد، بات را روی سرور خارجی (VPS) اجرا کنید.

## 🔧 ابزارهای کمکی

### تست اتصال به اینترنت

```bash
ping google.com
ping 8.8.8.8
```

### تست دسترسی به تلگرام

```bash
ping api.telegram.org
```

### بررسی پورت‌های باز

```bash
netstat -an | findstr :443
netstat -an | findstr :80
```

## 📞 پشتیبانی

اگر همچنان مشکل دارید:

1. فایل لاگ را بررسی کنید
2. خطاهای دقیق را یادداشت کنید
3. تنظیمات شبکه را بررسی کنید
4. از VPN معتبر استفاده کنید

## ⚠️ نکات امنیتی

- هرگز BOT_TOKEN را به اشتراک نگذارید
- از VPN های معتبر استفاده کنید
- فایروال را بعد از تست دوباره فعال کنید
- رمزهای عبور را در فایل‌های عمومی قرار ندهید

---

**نکته مهم:** در ایران به دلیل فیلتر بودن تلگرام، استفاده از VPN ضروری است.