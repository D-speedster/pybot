import asyncio
import time
import math
from telethon import Button

class ProgressManager:
    """مدیریت نمایش پیشرفت دانلود برای Telethon"""
    
    def __init__(self, event, client):
        self.event = event
        self.client = client
        self.message = None
        self.start_time = None
        self.last_update = 0
        self.update_interval = 2  # به‌روزرسانی هر 2 ثانیه
        
    async def start_progress(self, title: str):
        """شروع نمایش پیشرفت"""
        self.start_time = time.time()
        
        progress_text = (
            f"🔄 **{title}**\n\n"
            "📊 **پیشرفت:** 0%\n"
            "⏱ **زمان باقی‌مانده:** محاسبه...\n"
            "📦 **حجم:** محاسبه...\n\n"
            "⏳ لطفاً صبر کنید..."
        )
        
        # ارسال پیام جدید یا ویرایش پیام موجود
        if hasattr(self.event, 'query') and self.event.query:
            # اگر از callback query آمده
            self.message = await self.event.edit(progress_text, parse_mode='md')
        else:
            # اگر از پیام عادی آمده
            self.message = await self.event.respond(progress_text, parse_mode='md')
    
    async def update_progress(self, current: int, total: int, status: str = ""):
        """به‌روزرسانی پیشرفت"""
        current_time = time.time()
        
        # محدود کردن تعداد به‌روزرسانی‌ها
        if current_time - self.last_update < self.update_interval and current < total:
            return
            
        self.last_update = current_time
        
        # محاسبه درصد
        percentage = (current / total) * 100 if total > 0 else 0
        
        # محاسبه زمان باقی‌مانده
        elapsed_time = current_time - self.start_time
        if current > 0 and elapsed_time > 0:
            speed = current / elapsed_time
            remaining_bytes = total - current
            eta_seconds = remaining_bytes / speed if speed > 0 else 0
            eta_text = self._format_time(eta_seconds)
        else:
            eta_text = "محاسبه..."
        
        # ایجاد نوار پیشرفت
        progress_bar = self._create_progress_bar(percentage)
        
        # متن پیشرفت
        progress_text = (
            f"📥 **در حال دانلود**\n\n"
            f"{progress_bar}\n"
            f"📊 **پیشرفت:** {percentage:.1f}%\n"
            f"⏱ **زمان باقی‌مانده:** {eta_text}\n"
            f"📦 **حجم:** {self._format_size(current)} / {self._format_size(total)}\n"
        )
        
        if status:
            progress_text += f"\n🔄 **وضعیت:** {status}"
            
        progress_text += "\n\n⏳ لطفاً صبر کنید..."
        
        try:
            await self.message.edit(progress_text, parse_mode='md')
        except Exception:
            # اگر ویرایش ناموفق بود، پیام جدید ارسال کن
            pass
    
    async def complete_progress(self, file_info: str, file_size: int):
        """تکمیل پیشرفت"""
        elapsed_time = time.time() - self.start_time
        
        complete_text = (
            f"✅ **دانلود کامل شد!**\n\n"
            f"📁 **فایل:** {file_info}\n"
            f"📦 **حجم:** {self._format_size(file_size)}\n"
            f"⏱ **زمان:** {self._format_time(elapsed_time)}\n\n"
            f"📤 **در حال آپلود به تلگرام...**"
        )
        
        try:
            await self.message.edit(complete_text, parse_mode='md')
        except Exception:
            pass
    
    async def error_progress(self, error_message: str):
        """نمایش خطا"""
        error_text = (
            f"❌ **خطا در دانلود**\n\n"
            f"📝 **پیام خطا:** {error_message}\n\n"
            f"🔄 لطفاً دوباره تلاش کنید."
        )
        
        try:
            await self.message.edit(error_text, parse_mode='md')
        except Exception:
            pass
    
    def _create_progress_bar(self, percentage: float, length: int = 20) -> str:
        """ایجاد نوار پیشرفت"""
        filled_length = int(length * percentage / 100)
        bar = '█' * filled_length + '░' * (length - filled_length)
        return f"[{bar}] {percentage:.1f}%"
    
    def _format_size(self, bytes_size: int) -> str:
        """فرمت کردن حجم فایل"""
        if bytes_size == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = int(math.floor(math.log(bytes_size, 1024)))
        p = math.pow(1024, i)
        s = round(bytes_size / p, 2)
        return f"{s} {size_names[i]}"
    
    def _format_time(self, seconds: float) -> str:
        """فرمت کردن زمان"""
        if seconds < 60:
            return f"{int(seconds)} ثانیه"
        elif seconds < 3600:
            minutes = int(seconds / 60)
            return f"{minutes} دقیقه"
        else:
            hours = int(seconds / 3600)
            minutes = int((seconds % 3600) / 60)
            return f"{hours}:{minutes:02d} ساعت"

class TelethonProgressHook:
    """Hook برای نمایش پیشرفت دانلود pytube با Telethon"""
    
    def __init__(self, progress_manager: ProgressManager):
        self.progress_manager = progress_manager
        self.last_update = 0
    
    async def __call__(self, d):
        """فراخوانی hook"""
        if d['status'] == 'downloading':
            current_time = time.time()
            
            # محدود کردن به‌روزرسانی‌ها
            if current_time - self.last_update < 2:
                return
                
            self.last_update = current_time
            
            downloaded = d.get('downloaded_bytes', 0)
            total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
            
            if total > 0:
                await self.progress_manager.update_progress(
                    downloaded, 
                    total, 
                    "دانلود در حال انجام"
                )
        
        elif d['status'] == 'finished':
            filename = d.get('filename', 'فایل')
            file_size = d.get('total_bytes', 0)
            await self.progress_manager.complete_progress(
                filename.split('/')[-1], 
                file_size
            )