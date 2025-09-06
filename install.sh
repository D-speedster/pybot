#!/bin/bash

# 🚀 اسکریپت نصب خودکار ربات تلگرام
# نویسنده: تیم توسعه
# تاریخ: $(date +%Y-%m-%d)

set -e  # خروج در صورت بروز خطا

# رنگ‌ها برای خروجی
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# تابع چاپ پیام‌های رنگی
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# تابع تشخیص توزیع لینوکس
detect_os() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$NAME
        VER=$VERSION_ID
    elif type lsb_release >/dev/null 2>&1; then
        OS=$(lsb_release -si)
        VER=$(lsb_release -sr)
    elif [ -f /etc/lsb-release ]; then
        . /etc/lsb-release
        OS=$DISTRIB_ID
        VER=$DISTRIB_RELEASE
    elif [ -f /etc/debian_version ]; then
        OS=Debian
        VER=$(cat /etc/debian_version)
    elif [ -f /etc/SuSe-release ]; then
        OS=openSUSE
    elif [ -f /etc/redhat-release ]; then
        OS=RedHat
    else
        OS=$(uname -s)
        VER=$(uname -r)
    fi
}

# تابع نصب پکیج‌ها بر اساس توزیع
install_packages() {
    print_info "تشخیص توزیع لینوکس..."
    detect_os
    print_success "توزیع تشخیص داده شده: $OS $VER"
    
    if [[ "$OS" == *"Ubuntu"* ]] || [[ "$OS" == *"Debian"* ]]; then
        print_info "به‌روزرسانی فهرست پکیج‌ها..."
        sudo apt update
        
        print_info "نصب پکیج‌های مورد نیاز..."
        sudo apt install -y python3 python3-pip python3-venv python3-dev \
                           git build-essential libssl-dev libffi-dev \
                           wget curl screen tmux nano vim
                           
    elif [[ "$OS" == *"CentOS"* ]] || [[ "$OS" == *"Red Hat"* ]] || [[ "$OS" == *"Rocky"* ]]; then
        print_info "به‌روزرسانی سیستم..."
        if command -v dnf &> /dev/null; then
            sudo dnf update -y
            sudo dnf install -y python3 python3-pip python3-devel \
                               git gcc gcc-c++ make openssl-devel libffi-devel \
                               wget curl screen tmux nano vim
        else
            sudo yum update -y
            sudo yum groupinstall -y "Development Tools"
            sudo yum install -y python3 python3-pip python3-devel \
                               git openssl-devel libffi-devel \
                               wget curl screen tmux nano vim
        fi
        
    elif [[ "$OS" == *"Arch"* ]]; then
        print_info "به‌روزرسانی سیستم..."
        sudo pacman -Syu --noconfirm
        
        print_info "نصب پکیج‌های مورد نیاز..."
        sudo pacman -S --noconfirm python python-pip git base-devel \
                                   openssl libffi wget curl screen tmux nano vim
    else
        print_warning "توزیع شناخته شده نیست. سعی در نصب با pip..."
    fi
}

# تابع ایجاد محیط مجازی و نصب وابستگی‌ها
setup_python_env() {
    print_info "ایجاد محیط مجازی Python..."
    python3 -m venv venv
    
    print_info "فعال‌سازی محیط مجازی..."
    source venv/bin/activate
    
    print_info "به‌روزرسانی pip..."
    pip install --upgrade pip
    
    print_info "نصب وابستگی‌های Python..."
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
    else
        print_warning "فایل requirements.txt یافت نشد. نصب پکیج‌های اصلی..."
        pip install telethon pyrogram psutil asyncio aiofiles yt-dlp instaloader
    fi
}

# تابع تنظیم فایل محیطی
setup_env_file() {
    print_info "تنظیم فایل محیطی..."
    
    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            cp .env.example .env
            print_success "فایل .env از .env.example کپی شد"
        else
            print_info "ایجاد فایل .env جدید..."
            cat > .env << EOF
# Bot Configuration
BOT_TOKEN=YOUR_BOT_TOKEN_HERE
API_ID=YOUR_API_ID
API_HASH=YOUR_API_HASH

# Admin Configuration
ADMIN_IDS=123456789
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
EOF
        fi
        
        print_warning "لطفاً فایل .env را با اطلاعات ربات خود ویرایش کنید:"
        print_info "nano .env"
    else
        print_success "فایل .env موجود است"
    fi
}

# تابع ایجاد دایرکتوری‌ها
create_directories() {
    print_info "ایجاد دایرکتوری‌های مورد نیاز..."
    
    directories=("logs" "Downloads" "temp_downloads" "sessions")
    
    for dir in "${directories[@]}"; do
        if [ ! -d "$dir" ]; then
            mkdir -p "$dir"
            chmod 755 "$dir"
            print_success "دایرکتوری $dir ایجاد شد"
        else
            print_info "دایرکتوری $dir موجود است"
        fi
    done
}

# تابع ایجاد اسکریپت‌های کمکی
create_helper_scripts() {
    print_info "ایجاد اسکریپت‌های کمکی..."
    
    # اسکریپت شروع
    cat > start.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
python main.py
EOF
    chmod +x start.sh
    
    # اسکریپت توقف
    cat > stop.sh << 'EOF'
#!/bin/bash
pkill -f "python main.py"
echo "ربات متوقف شد"
EOF
    chmod +x stop.sh
    
    # اسکریپت restart
    cat > restart.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
./stop.sh
sleep 2
./start.sh
EOF
    chmod +x restart.sh
    
    # اسکریپت مشاهده لاگ
    cat > logs.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
if [ -f "logs/bot.log" ]; then
    tail -f logs/bot.log
else
    echo "فایل لاگ یافت نشد"
fi
EOF
    chmod +x logs.sh
    
    print_success "اسکریپت‌های کمکی ایجاد شدند"
}

# تابع ایجاد سرویس systemd
create_systemd_service() {
    read -p "آیا می‌خواهید سرویس systemd ایجاد کنید؟ (y/n): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_info "ایجاد سرویس systemd..."
        
        SERVICE_FILE="/etc/systemd/system/telegram-bot.service"
        CURRENT_USER=$(whoami)
        CURRENT_DIR=$(pwd)
        
        sudo tee $SERVICE_FILE > /dev/null << EOF
[Unit]
Description=Telegram YouTube/Instagram Bot
After=network.target
Wants=network.target

[Service]
Type=simple
User=$CURRENT_USER
Group=$CURRENT_USER
WorkingDirectory=$CURRENT_DIR
Environment=PATH=$CURRENT_DIR/venv/bin
ExecStart=$CURRENT_DIR/venv/bin/python main.py
Restart=always
RestartSec=10
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true
NoNewPrivileges=true

[Install]
WantedBy=multi-user.target
EOF
        
        sudo systemctl daemon-reload
        sudo systemctl enable telegram-bot.service
        
        print_success "سرویس systemd ایجاد و فعال شد"
        print_info "برای شروع سرویس: sudo systemctl start telegram-bot.service"
        print_info "برای مشاهده وضعیت: sudo systemctl status telegram-bot.service"
    fi
}

# تابع نمایش راهنمای نهایی
show_final_instructions() {
    print_success "🎉 نصب با موفقیت تکمیل شد!"
    echo
    print_info "مراحل بعدی:"
    echo "1. فایل .env را ویرایش کنید: nano .env"
    echo "2. Session ایجاد کنید: python session_creator.py"
    echo "3. ربات را اجرا کنید: ./start.sh"
    echo
    print_info "دستورات مفید:"
    echo "• شروع ربات: ./start.sh"
    echo "• توقف ربات: ./stop.sh"
    echo "• راه‌اندازی مجدد: ./restart.sh"
    echo "• مشاهده لاگ: ./logs.sh"
    echo
    if [ -f "/etc/systemd/system/telegram-bot.service" ]; then
        print_info "دستورات سرویس systemd:"
        echo "• شروع: sudo systemctl start telegram-bot.service"
        echo "• توقف: sudo systemctl stop telegram-bot.service"
        echo "• وضعیت: sudo systemctl status telegram-bot.service"
        echo "• لاگ: sudo journalctl -u telegram-bot.service -f"
    fi
}

# تابع اصلی
main() {
    clear
    echo "🚀 اسکریپت نصب خودکار ربات تلگرام"
    echo "======================================"
    echo
    
    # بررسی دسترسی root
    # if [ "$EUID" -eq 0 ]; then
    #     print_error "لطفاً این اسکریپت را با کاربر عادی اجرا کنید (نه root)"
    #     exit 1
    
    # بررسی اتصال اینترنت
    print_info "بررسی اتصال اینترنت..."
    if ! ping -c 1 google.com &> /dev/null; then
        print_error "اتصال اینترنت برقرار نیست"
        exit 1
    fi
    print_success "اتصال اینترنت برقرار است"
    
    # شروع نصب
    install_packages
    setup_python_env
    setup_env_file
    create_directories
    create_helper_scripts
    create_systemd_service
    
    show_final_instructions
}

# اجرای تابع اصلی
main "$@"