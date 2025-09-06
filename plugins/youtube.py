import os
import asyncio
from pytubefix import YouTube
from pytubefix.exceptions import VideoUnavailable, ExtractError, RegexMatchError
from telethon import events, Button
from telethon.tl.types import DocumentAttributeVideo, DocumentAttributeAudio
from utils.progress_manager import ProgressManager, TelethonProgressHook
from plugins.constant import TEXT, DATA
from config import BOT_TOKEN

class YouTubeDownloader:
    """کلاس دانلود از یوتیوب با Telethon"""
    
    def __init__(self, client):
        self.client = client
        self.downloads_path = "downloads"
        
        # ایجاد پوشه دانلود
        if not os.path.exists(self.downloads_path):
            os.makedirs(self.downloads_path)
    
    async def get_video_info(self, url: str) -> dict:
        """دریافت اطلاعات ویدیو با pytube"""
        try:
            # ایجاد شیء YouTube
            yt = YouTube(url)
            
            # استخراج فرمت‌های موجود
            formats = []
            for stream in yt.streams.filter(progressive=True, file_extension='mp4'):
                formats.append({
                    'format_id': str(stream.itag),
                    'ext': stream.mime_type.split('/')[-1],
                    'height': int(stream.resolution.replace('p', '')) if stream.resolution else None,
                    'filesize': stream.filesize,
                    'fps': stream.fps,
                    'vcodec': 'h264',
                    'acodec': 'aac'
                })
            
            # اضافه کردن فرمت‌های adaptive (کیفیت بالا)
            for stream in yt.streams.filter(adaptive=True, file_extension='mp4'):
                if stream.video_codec:  # فقط ویدیو
                    formats.append({
                        'format_id': str(stream.itag),
                        'ext': stream.mime_type.split('/')[-1],
                        'height': int(stream.resolution.replace('p', '')) if stream.resolution else None,
                        'filesize': stream.filesize,
                        'fps': stream.fps,
                        'vcodec': stream.video_codec,
                        'acodec': 'none'
                    })
            
            # اضافه کردن فرمت‌های صوتی
            for stream in yt.streams.filter(only_audio=True):
                formats.append({
                    'format_id': str(stream.itag),
                    'ext': stream.mime_type.split('/')[-1],
                    'height': None,
                    'filesize': stream.filesize,
                    'abr': stream.abr,
                    'vcodec': 'none',
                    'acodec': stream.audio_codec
                })
            
            return {
                'title': yt.title,
                'duration': yt.length,
                'view_count': yt.views,
                'uploader': yt.author,
                'thumbnail': yt.thumbnail_url,
                'formats': formats
            }
                
        except Exception as e:
            raise Exception(f"خطا در pytube: {str(e)}")
        except Exception as e:
            raise Exception(f"خطا در دریافت اطلاعات: {str(e)}")
    
    def create_quality_keyboard(self, video_info: dict, url: str) -> list:
        """ایجاد کیبورد انتخاب کیفیت"""
        buttons = []
        
        # دریافت فرمت‌های موجود
        formats = video_info.get('formats', [])
        
        # فیلتر کردن فرمت‌های ویدیویی
        video_formats = []
        for f in formats:
            if f.get('vcodec') != 'none' and f.get('height'):
                video_formats.append(f)
        
        # مرتب‌سازی بر اساس کیفیت
        video_formats.sort(key=lambda x: x.get('height', 0), reverse=True)
        
        # حذف تکراری‌ها
        seen_heights = set()
        unique_formats = []
        for f in video_formats:
            height = f.get('height')
            if height not in seen_heights:
                seen_heights.add(height)
                unique_formats.append(f)
        
        # ایجاد دکمه‌ها
        for f in unique_formats[:6]:  # حداکثر 6 کیفیت
            height = f.get('height', 'نامشخص')
            ext = f.get('ext', 'mp4')
            filesize = f.get('filesize')
            
            if filesize:
                size_mb = filesize / (1024 * 1024)
                size_text = f" ({size_mb:.1f} MB)"
            else:
                size_text = ""
            
            button_text = f"📹 {height}p {ext.upper()}{size_text}"
            callback_data = f"yt_video_{height}_{f.get('format_id')}_{hash(url) % 10000}"
            
            buttons.append([Button.inline(button_text, callback_data)])
        
        # دکمه صوت
        audio_formats = [f for f in formats if f.get('acodec') != 'none' and f.get('vcodec') == 'none']
        if audio_formats:
            best_audio = max(audio_formats, key=lambda x: x.get('abr', 0))
            filesize = best_audio.get('filesize')
            if filesize:
                size_mb = filesize / (1024 * 1024)
                size_text = f" ({size_mb:.1f} MB)"
            else:
                size_text = ""
            
            button_text = f"🎵 صوت MP3{size_text}"
            callback_data = f"yt_audio_{best_audio.get('format_id')}_{hash(url) % 10000}"
            buttons.append([Button.inline(button_text, callback_data)])
        
        # دکمه لغو
        buttons.append([Button.inline("❌ لغو", "cancel")])
        
        return buttons
    
    async def download_video(self, url: str, format_id: str, progress_manager: ProgressManager, audio_only: bool = False):
        """دانلود ویدیو یا صوت با pytube"""
        
        try:
            # ایجاد شیء YouTube
            yt = YouTube(url)
            
            # انتخاب stream بر اساس نوع دانلود
            if audio_only:
                stream = yt.streams.filter(only_audio=True).first()
                if not stream:
                    raise Exception("هیچ stream صوتی پیدا نشد")
            else:
                # پیدا کردن stream بر اساس format_id (itag)
                try:
                    itag = int(format_id)
                    stream = yt.streams.get_by_itag(itag)
                except (ValueError, TypeError):
                    # اگر format_id معتبر نیست، بهترین کیفیت را انتخاب کن
                    stream = yt.streams.get_highest_resolution()
                
                if not stream:
                    stream = yt.streams.get_highest_resolution()
                    if not stream:
                        raise Exception("هیچ stream ویدیویی پیدا نشد")
            
            # تنظیم progress callback
            def progress_callback(stream, chunk, bytes_remaining):
                total_size = stream.filesize
                bytes_downloaded = total_size - bytes_remaining
                percent = (bytes_downloaded / total_size) * 100
                
                # ارسال پیشرفت به progress manager
                if hasattr(progress_manager, 'update_progress'):
                    asyncio.create_task(progress_manager.update_progress(percent))
            
            # تنظیم callback
            yt.register_on_progress_callback(progress_callback)
            
            # دانلود فایل
            file_path = await asyncio.get_event_loop().run_in_executor(
                None, stream.download, self.downloads_path
            )
            
            if not os.path.exists(file_path):
                raise Exception("فایل دانلود شده پیدا نشد")
                
            return file_path
                
        except Exception as e:
            raise Exception(f"خطا در pytube: {str(e)}")
        except Exception as e:
            raise Exception(f"خطا در دانلود: {str(e)}")

# نمونه سراسری
youtube_downloader = None

async def handle_youtube_message(event):
    """پردازش پیام‌های یوتیوب"""
    global youtube_downloader
    
    if not youtube_downloader:
        youtube_downloader = YouTubeDownloader(event.client)
    
    url = event.message.text.strip()
    
    try:
        # ارسال پیام "در حال پردازش"
        processing_msg = await event.respond(
            "🔍 **در حال بررسی لینک...**\n\n⏳ لطفاً صبر کنید...",
            parse_mode='md'
        )
        
        # دریافت اطلاعات ویدیو
        video_info = await youtube_downloader.get_video_info(url)
        
        # اطلاعات ویدیو
        title = video_info.get('title', 'نامشخص')
        duration = video_info.get('duration', 0)
        uploader = video_info.get('uploader', 'نامشخص')
        view_count = video_info.get('view_count', 0)
        
        # فرمت کردن مدت زمان
        if duration:
            minutes = duration // 60
            seconds = duration % 60
            duration_text = f"{minutes}:{seconds:02d}"
        else:
            duration_text = "نامشخص"
        
        # فرمت کردن تعداد بازدید
        if view_count:
            if view_count >= 1000000:
                view_text = f"{view_count/1000000:.1f}M"
            elif view_count >= 1000:
                view_text = f"{view_count/1000:.1f}K"
            else:
                view_text = str(view_count)
        else:
            view_text = "نامشخص"
        
        # متن اطلاعات
        info_text = (
            f"📹 **{title[:50]}{'...' if len(title) > 50 else ''}**\n\n"
            f"👤 **کانال:** {uploader}\n"
            f"⏱ **مدت زمان:** {duration_text}\n"
            f"👁 **بازدید:** {view_text}\n\n"
            f"📥 **کیفیت مورد نظر را انتخاب کنید:**"
        )
        
        # ایجاد کیبورد
        keyboard = youtube_downloader.create_quality_keyboard(video_info, url)
        
        # ویرایش پیام
        await processing_msg.edit(
            info_text,
            buttons=keyboard,
            parse_mode='md'
        )
        
    except Exception as e:
        error_text = f"❌ **خطا در پردازش لینک**\n\n📝 **جزئیات:** {str(e)}"
        try:
            await processing_msg.edit(error_text, parse_mode='md')
        except:
            await event.respond(error_text, parse_mode='md')

async def handle_youtube_callback(event):
    """پردازش callback های یوتیوب"""
    global youtube_downloader
    
    if not youtube_downloader:
        youtube_downloader = YouTubeDownloader(event.client)
    
    data = event.data.decode('utf-8')
    
    if data == "cancel":
        await event.edit("❌ **عملیات لغو شد.**", parse_mode='md')
        return
    
    try:
        # پارس کردن داده‌ها
        parts = data.split('_')
        if len(parts) < 4:
            await event.answer("❌ داده نامعتبر", alert=True)
            return
        
        download_type = parts[1]  # video یا audio
        
        if download_type == "video":
            quality = parts[2]
            format_id = parts[3]
            audio_only = False
        elif download_type == "audio":
            format_id = parts[2]
            audio_only = True
        else:
            await event.answer("❌ نوع دانلود نامعتبر", alert=True)
            return
        
        # شروع دانلود
        progress_manager = ProgressManager(event, event.client)
        
        if audio_only:
            await progress_manager.start_progress("دانلود صوت")
        else:
            await progress_manager.start_progress(f"دانلود ویدیو {quality}p")
        
        # استخراج URL از پیام اصلی
        original_message = event.message.message
        # فرض می‌کنیم URL در پیام قبلی ذخیره شده
        # برای سادگی، از یک روش ساده استفاده می‌کنیم
        
        # دانلود فایل
        # نکته: برای دریافت URL اصلی، باید از روش‌های دیگری استفاده کرد
        # اینجا فقط نمونه‌ای از کد است
        
        await event.answer("✅ دانلود شروع شد", alert=False)
        
    except Exception as e:
        await event.answer(f"❌ خطا: {str(e)}", alert=True)
        
        # نمایش خطا در پیام
        error_text = f"❌ **خطا در دانلود**\n\n📝 **جزئیات:** {str(e)}"
        try:
            await event.edit(error_text, parse_mode='md')
        except:
            pass
