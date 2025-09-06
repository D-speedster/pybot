#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Manual Cookie Extractor for YouTube
This script helps extract YouTube cookies manually without admin privileges
"""

import json
import os
from datetime import datetime

def create_sample_cookies():
    """Create a sample cookies.txt with proper format"""
    sample_content = '''# Netscape HTTP Cookie File
# Generated manually - Replace with your actual YouTube cookies
# Instructions:
# 1. Go to youtube.com in Chrome
# 2. Login to your account
# 3. Press F12 -> Application -> Cookies -> https://www.youtube.com
# 4. Find and copy these important cookies:
#    - SAPISID
#    - HSID  
#    - SSID
#    - APISID
#    - LOGIN_INFO
#    - session_token (if available)
# 5. Replace the values below with your actual cookie values

# IMPORTANT: Replace 'YOUR_VALUE_HERE' with actual cookie values from your browser
.youtube.com\tTRUE\t/\tTRUE\t1772648989\tSAPISID\tYOUR_SAPISID_VALUE_HERE
.youtube.com\tTRUE\t/\tTRUE\t1772648989\tHSID\tYOUR_HSID_VALUE_HERE
.youtube.com\tTRUE\t/\tTRUE\t1772648989\tSSID\tYOUR_SSID_VALUE_HERE
.youtube.com\tTRUE\t/\tTRUE\t1772648989\tAPISID\tYOUR_APISID_VALUE_HERE
.youtube.com\tTRUE\t/\tTRUE\t1772648989\tLOGIN_INFO\tYOUR_LOGIN_INFO_VALUE_HERE
.youtube.com\tTRUE\t/\tTRUE\t1772648989\tsession_token\tYOUR_SESSION_TOKEN_VALUE_HERE

# Basic cookies (these are usually fine)
.youtube.com\tTRUE\t/\tTRUE\t1772648989\tVISITOR_INFO1_LIVE\tYLKWCmbblws
.youtube.com\tTRUE\t/\tTRUE\t0\tYSC\twGOPqXD8gsg
.youtube.com\tTRUE\t/\tFALSE\t0\tPREF\tf4=4000000&hl=en&tz=UTC
.youtube.com\tTRUE\t/\tFALSE\t1788632925\tCONSENT\tYES+cb.20210328-17-p0.en+FX+1757096925
.youtube.com\tTRUE\t/\tTRUE\t0\tSOCS\tCAI
'''
    
    with open('cookies.txt', 'w', encoding='utf-8') as f:
        f.write(sample_content)
    
    print("✅ فایل cookies.txt با فرمت نمونه ایجاد شد.")
    print("📝 لطفاً مقادیر YOUR_VALUE_HERE را با کوکی‌های واقعی خود جایگزین کنید.")
    print("\n🔍 راهنمای استخراج کوکی:")
    print("1. به youtube.com بروید و وارد اکانت خود شوید")
    print("2. F12 را فشار دهید")
    print("3. Application -> Cookies -> https://www.youtube.com")
    print("4. کوکی‌های مهم را کپی کنید: SAPISID, HSID, SSID, APISID, LOGIN_INFO")
    print("5. در فایل cookies.txt جایگزین کنید")

def validate_cookies():
    """Check if cookies.txt has valid authentication cookies"""
    if not os.path.exists('cookies.txt'):
        print("❌ فایل cookies.txt یافت نشد.")
        return False
    
    with open('cookies.txt', 'r', encoding='utf-8') as f:
        content = f.read()
    
    required_cookies = ['SAPISID', 'HSID', 'SSID', 'APISID']
    missing_cookies = []
    
    for cookie in required_cookies:
        if f'\t{cookie}\t' not in content or 'YOUR_VALUE_HERE' in content:
            missing_cookies.append(cookie)
    
    if missing_cookies:
        print(f"❌ کوکی‌های مهم موجود نیستند یا جایگزین نشده‌اند: {', '.join(missing_cookies)}")
        print("📝 لطفاً کوکی‌های واقعی را از مرورگر کپی کنید.")
        return False
    
    print("✅ کوکی‌های احراز هویت موجود هستند.")
    return True

def main():
    print("🍪 استخراج کننده دستی کوکی‌های یوتیوب")
    print("="*50)
    
    choice = input("\n1. ایجاد فایل نمونه کوکی\n2. بررسی کوکی‌های موجود\nانتخاب کنید (1 یا 2): ")
    
    if choice == '1':
        create_sample_cookies()
    elif choice == '2':
        validate_cookies()
    else:
        print("❌ انتخاب نامعتبر.")

if __name__ == "__main__":
    main()