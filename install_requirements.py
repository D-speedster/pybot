import subprocess
import sys

def install_requirements():
    """نصب کتابخانه‌های مورد نیاز"""
    requirements = [
        'browser_cookie3',
    
        'PySocks'
    ]
    
    print("📦 در حال نصب کتابخانه‌های مورد نیاز...")
    
    for package in requirements:
        print(f"🔄 نصب {package}...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"✅ {package} با موفقیت نصب شد.")
        except subprocess.CalledProcessError as e:
            print(f"❌ خطا در نصب {package}: {str(e)}")
            return False
    
    print("\n✅ تمام کتابخانه‌های مورد نیاز با موفقیت نصب شدند.")
    print("\n💡 اکنون می‌توانید با اجرای دستور زیر کوکی‌های مرورگر خود را استخراج کنید:")
    print("   python extract_cookies.py --browser chrome --domain .youtube.com --output cookies.txt")
    return True

if __name__ == "__main__":
    install_requirements()