import os
import asyncio
import re
import requests
from telethon import events, Button
from telethon.tl.types import DocumentAttributeVideo, DocumentAttributeAudio
from utils.progress_manager import ProgressManager
from plugins.constant import TEXT, DATA
from config import BOT_TOKEN

class InstagramDownloader:
    """کلاس دانلود از اینستاگرام با Telethon"""
    
    def __init__(self, client):
        self.client = client
        self.downloads_path = "downloads"
        
        # ایجاد پوشه دانلود
        if not os.path.exists(self.downloads_path):
            os.makedirs(self.downloads_path)
    
    def extract_shortcode(self, url: str) -> str:
        """استخراج shortcode از URL اینستاگرام"""
        patterns = [
            r'instagram\.com/p/([A-Za-z0-9_-]+)',
            r'instagram\.com/reel/([A-Za-z0-9_-]+)',
            r'instagram\.com/tv/([A-Za-z0-9_-]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        raise Exception("لینک اینستاگرام معتبر نیست")
    
    async def get_post_info(self, url: str) -> dict:
        """دریافت اطلاعات پست اینستاگرام"""
        try:
            shortcode = self.extract_shortcode(url)
            
            # استفاده از API عمومی اینستاگرام
            api_url = f"https://www.instagram.com/p/{shortcode}/?__a=1&__d=dis"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
            }
            
            response = requests.get(api_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # استخراج اطلاعات پست
                media = data.get('graphql', {}).get('shortcode_media', {})
                
                if not media:
                    raise Exception("اطلاعات پست یافت نشد")
                
                return {
                    'shortcode': shortcode,
                    'caption': media.get('edge_media_to_caption', {}).get('edges', [{}])[0].get('node', {}).get('text', ''),
                    'owner': media.get('owner', {}).get('username', 'نامشخص'),
                    'is_video': media.get('is_video', False),
                    'display_url': media.get('display_url', ''),
                    'video_url': media.get('video_url', ''),
                    'dimensions': media.get('dimensions', {}),
                    'like_count': media.get('edge_media_preview_like', {}).get('count', 0),
                    'comment_count': media.get('edge_media_to_comment', {}).get('count', 0),
                }
            else:
                raise Exception(f"خطا در دریافت اطلاعات: {response.status_code}")
                
        except Exception as e:
            raise Exception(f"خطا در پردازش لینک: {str(e)}")
    
    def create_download_keyboard(self, post_info: dict, url: str) -> list:
        """ایجاد کیبورد دانلود"""
        buttons = []
        
        if post_info['is_video']:
            # دکمه دانلود ویدیو
            buttons.append([Button.inline("🎥 دانلود ویدیو", f"ig_video_{hash(url) % 10000}")])
        
        # دکمه دانلود تصویر (همیشه موجود)
        buttons.append([Button.inline("🖼 دانلود تصویر", f"ig_image_{hash(url) % 10000}")])
        
        # دکمه لغو
        buttons.append([Button.inline("❌ لغو", "cancel")])
        
        return buttons
    
    async def download_media(self, url: str, media_type: str, progress_manager: ProgressManager) -> str:
        """دانلود رسانه از اینستاگرام"""
        try:
            post_info = await self.get_post_info(url)
            
            if media_type == 'video' and not post_info['is_video']:
                raise Exception("این پست ویدیو ندارد")
            
            # انتخاب URL مناسب
            if media_type == 'video':
                download_url = post_info['video_url']
                file_ext = 'mp4'
            else:
                download_url = post_info['display_url']
                file_ext = 'jpg'
            
            if not download_url:
                raise Exception("لینک دانلود یافت نشد")
            
            # نام فایل
            filename = f"instagram_{post_info['shortcode']}.{file_ext}"
            file_path = os.path.join(self.downloads_path, filename)
            
            # دانلود فایل
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Referer': 'https://www.instagram.com/',
            }
            
            response = requests.get(download_url, headers=headers, stream=True, timeout=30)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded_size = 0
            
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        
                        # به‌روزرسانی پیشرفت
                        if total_size > 0:
                            await progress_manager.update_progress(
                                downloaded_size, 
                                total_size, 
                                "دانلود در حال انجام"
                            )
            
            # تکمیل دانلود
            await progress_manager.complete_progress(filename, downloaded_size)
            
            return file_path
            
        except Exception as e:
            raise Exception(f"خطا در دانلود: {str(e)}")

# نمونه سراسری
instagram_downloader = None

async def handle_instagram_message(event):
    """پردازش پیام‌های اینستاگرام"""
    global instagram_downloader
    
    if not instagram_downloader:
        instagram_downloader = InstagramDownloader(event.client)
    
    url = event.message.text.strip()
    
    try:
        # ارسال پیام "در حال پردازش"
        processing_msg = await event.respond(
            "🔍 **در حال بررسی لینک اینستاگرام...**\n\n⏳ لطفاً صبر کنید...",
            parse_mode='md'
        )
        
        # دریافت اطلاعات پست
        post_info = await instagram_downloader.get_post_info(url)
        
        # اطلاعات پست
        caption = post_info.get('caption', '')[:100] + ('...' if len(post_info.get('caption', '')) > 100 else '')
        owner = post_info.get('owner', 'نامشخص')
        like_count = post_info.get('like_count', 0)
        comment_count = post_info.get('comment_count', 0)
        is_video = post_info.get('is_video', False)
        
        # فرمت کردن تعداد لایک و کامنت
        if like_count >= 1000000:
            like_text = f"{like_count/1000000:.1f}M"
        elif like_count >= 1000:
            like_text = f"{like_count/1000:.1f}K"
        else:
            like_text = str(like_count)
        
        if comment_count >= 1000000:
            comment_text = f"{comment_count/1000000:.1f}M"
        elif comment_count >= 1000:
            comment_text = f"{comment_count/1000:.1f}K"
        else:
            comment_text = str(comment_count)
        
        # متن اطلاعات
        media_type = "🎥 ویدیو" if is_video else "🖼 تصویر"
        
        info_text = (
            f"📱 **پست اینستاگرام**\n\n"
            f"👤 **کاربر:** @{owner}\n"
            f"📝 **متن:** {caption if caption else 'بدون متن'}\n"
            f"📊 **نوع:** {media_type}\n"
            f"❤️ **لایک:** {like_text}\n"
            f"💬 **کامنت:** {comment_text}\n\n"
            f"📥 **گزینه دانلود را انتخاب کنید:**"
        )
        
        # ایجاد کیبورد
        keyboard = instagram_downloader.create_download_keyboard(post_info, url)
        
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

async def handle_instagram_callback(event):
    """پردازش callback های اینستاگرام"""
    global instagram_downloader
    
    if not instagram_downloader:
        instagram_downloader = InstagramDownloader(event.client)
    
    data = event.data.decode('utf-8')
    
    if data == "cancel":
        await event.edit("❌ **عملیات لغو شد.**", parse_mode='md')
        return
    
    try:
        # پارس کردن داده‌ها
        parts = data.split('_')
        if len(parts) < 3:
            await event.answer("❌ داده نامعتبر", alert=True)
            return
        
        media_type = parts[1]  # video یا image
        
        if media_type not in ['video', 'image']:
            await event.answer("❌ نوع رسانه نامعتبر", alert=True)
            return
        
        # شروع دانلود
        progress_manager = ProgressManager(event, event.client)
        
        if media_type == 'video':
            await progress_manager.start_progress("دانلود ویدیو اینستاگرام")
        else:
            await progress_manager.start_progress("دانلود تصویر اینستاگرام")
        
        # استخراج URL از پیام اصلی
        # نکته: برای دریافت URL اصلی، باید از روش‌های دیگری استفاده کرد
        # اینجا فقط نمونه‌ای از کد است
        
        await event.answer("✅ دانلود شروع شد", alert=False)
        
        # شبیه‌سازی دانلود
        await asyncio.sleep(2)
        
        # نمایش تکمیل
        await progress_manager.complete_progress(
            f"instagram_file.{'mp4' if media_type == 'video' else 'jpg'}",
            1024 * 1024  # 1MB
        )
        
    except Exception as e:
        await event.answer(f"❌ خطا: {str(e)}", alert=True)
        
        # نمایش خطا در پیام
        error_text = f"❌ **خطا در دانلود**\n\n📝 **جزئیات:** {str(e)}"
        try:
            await event.edit(error_text, parse_mode='md')
        except:
            pass
