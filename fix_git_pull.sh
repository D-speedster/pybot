#!/bin/bash

# 🔧 اسکریپت حل مشکل Git Pull برای فایل cookies.txt
# این اسکریپت مشکل تداخل فایل cookies.txt هنگام git pull را حل می‌کند

echo "🔄 حل مشکل Git Pull برای cookies.txt"
echo "==========================================="

# بررسی وضعیت git
echo "📋 بررسی وضعیت فعلی git..."
git status

echo ""
echo "🤔 آیا می‌خواهید کوکی‌های فعلی را نگه دارید؟ (y/n)"
read -r keep_cookies

if [[ $keep_cookies == "y" || $keep_cookies == "Y" ]]; then
    echo "💾 ذخیره کوکی‌های فعلی..."
    
    # بک‌آپ گیری از کوکی‌های فعلی
    if [ -f "cookies.txt" ]; then
        cp cookies.txt "cookies.txt.backup.$(date +%Y%m%d_%H%M%S)"
        echo "✅ بک‌آپ در cookies.txt.backup.$(date +%Y%m%d_%H%M%S) ذخیره شد"
    fi
    
    # stash کردن تغییرات
    echo "📦 Stash کردن تغییرات محلی..."
    git stash push -m "backup cookies before pull $(date)" cookies.txt
    
    # pull کردن تغییرات جدید
    echo "⬇️ دریافت آخرین تغییرات..."
    git pull
    
    # بازگردانی کوکی‌های قدیمی
    echo "🔄 بازگردانی کوکی‌های شما..."
    git checkout stash@{0} -- cookies.txt
    
    echo "✅ کوکی‌های شما بازگردانده شد و تغییرات جدید دریافت شد"
    
else
    echo "🗑️ حذف تغییرات محلی و استفاده از نسخه جدید..."
    
    # بک‌آپ گیری (برای احتیاط)
    if [ -f "cookies.txt" ]; then
        cp cookies.txt "cookies.txt.old.$(date +%Y%m%d_%H%M%S)"
        echo "💾 بک‌آپ احتیاطی در cookies.txt.old.$(date +%Y%m%d_%H%M%S) ذخیره شد"
    fi
    
    # reset کردن فایل
    git checkout HEAD -- cookies.txt
    
    # pull کردن
    echo "⬇️ دریافت آخرین تغییرات..."
    git pull
    
    echo "✅ نسخه جدید cookies.txt دریافت شد"
    echo "📝 لطفاً کوکی‌های خود را مطابق راهنما وارد کنید"
fi

echo ""
echo "📊 وضعیت نهایی:"
git status

echo ""
echo "📋 فایل‌های بک‌آپ موجود:"
ls -la cookies.txt.* 2>/dev/null || echo "هیچ بک‌آپی یافت نشد"

echo ""
echo "🎉 عملیات تکمیل شد!"
echo "💡 نکته: اگر کوکی‌های جدید نیاز دارید، راهنمای LINUX_COOKIE_GUIDE.md را مطالعه کنید"