import asyncio
import logging
import re
from datetime import datetime
from typing import Optional, Dict, Any

from telethon import TelegramClient, events, Button
from telethon.tl.types import DocumentAttributeVideo, DocumentAttributeAudio

from config import (
    BOT_TOKEN, API_ID, API_HASH, MESSAGES, 
    ADMIN_IDS, QUALITY_OPTIONS, RATE_LIMIT_CONFIG, ADMIN_PANEL_CONFIG
)
from services.download_service import DownloadService
from services.session_manager import SessionManager
from utils.database import Database
from utils.rate_limiter import RateLimiter
from utils.helpers import FileUtils, TimeUtils

logger = logging.getLogger(__name__)

# URL patterns
YOUTUBE_PATTERN = re.compile(
    r'(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/'
    r'(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})'
)

INSTAGRAM_PATTERN = re.compile(
    r'https?://(?:www\.)?instagram\.com/(?:p|reel|tv)/([A-Za-z0-9_-]+)/?'
)

class BotHandlers:
    def __init__(self, session_manager: SessionManager, admin_handlers=None):
        self.session_manager = session_manager
        self.download_service = DownloadService(session_manager)
        self.db = Database()
        self.rate_limiter = RateLimiter()
        self.admin_handlers = admin_handlers
        self.bot: Optional[TelegramClient] = None
        self.bot_started = False
        self.message_queue = asyncio.Queue()
        self.processing_queue = False
        
    async def setup_bot(self) -> TelegramClient:
        """Setup and configure the bot client"""
        # Create bot client without proxy for better performance
        client_kwargs = {
            'session': 'bot_session',
            'api_id': API_ID,
            'api_hash': API_HASH,
            'connection_retries': 5,
            'retry_delay': 1,
            'timeout': 30
        }
        
        self.bot = TelegramClient(**client_kwargs)
        
        # Register event handlers
        self.bot.add_event_handler(self.start_handler, events.NewMessage(pattern='/start'))
        self.bot.add_event_handler(self.help_handler, events.NewMessage(pattern='/help'))
        self.bot.add_event_handler(self.sessions_handler, events.NewMessage(pattern='/sessions'))
        self.bot.add_event_handler(self.stats_handler, events.NewMessage(pattern='/stats'))
        self.bot.add_event_handler(self.cleanup_handler, events.NewMessage(pattern='/cleanup'))
        self.bot.add_event_handler(self.url_handler, events.NewMessage())
        self.bot.add_event_handler(self.callback_handler, events.CallbackQuery())
        
        # Start bot
        await self.bot.start(bot_token=BOT_TOKEN)
        logger.info("✅ Bot client started successfully")
        
        # Mark bot as fully started
        self.bot_started = True
        
        # Process queued messages when bot starts
        asyncio.create_task(self.process_message_queue())
        
        return self.bot
    
    async def process_message_queue(self):
        """Process queued messages when bot comes back online"""
        if self.processing_queue:
            return
            
        self.processing_queue = True
        try:
            # Get unprocessed messages
            queued_messages = await self.db.get_unprocessed_messages()
            
            if queued_messages:
                logger.info(f"📬 Processing {len(queued_messages)} queued messages")
                
                for message_data in queued_messages:
                    try:
                        user_id = message_data['user_id']
                        message_text = message_data['message_text']
                        message_type = message_data['message_type']
                        
                        # Send notification to user that their request is being processed
                        await self.bot.send_message(
                            user_id,
                            "🔄 **درخواست شما در حال پردازش است...**\n\n"
                            "ربات مجدداً آنلاین شده و درخواست قبلی شما را پردازش می‌کند."
                        )
                        
                        # Process the message based on type
                        if message_type == 'url':
                            # Create a mock event for URL processing
                            class MockEvent:
                                def __init__(self, user_id, text):
                                    self.sender_id = user_id
                                    self.text = text
                                    
                                async def get_sender(self):
                                    return type('User', (), {'id': self.sender_id})()
                                
                                async def respond(self, text, **kwargs):
                                    await self.bot.send_message(self.sender_id, text, **kwargs)
                            
                            mock_event = MockEvent(user_id, message_text)
                            await self.url_handler(mock_event)
                        
                        elif message_type == 'start':
                            # Create a mock event for start command processing
                            class MockEvent:
                                def __init__(self, user_id, text):
                                    self.sender_id = user_id
                                    self.text = text
                                    
                                async def get_sender(self):
                                    return type('User', (), {'id': self.sender_id, 'username': None, 'first_name': 'کاربر'})()
                                
                                async def respond(self, text, **kwargs):
                                    await self.bot.send_message(self.sender_id, text, **kwargs)
                            
                            mock_event = MockEvent(user_id, message_text)
                            await self.start_handler(mock_event)
                        
                        # Mark as processed
                        await self.db.mark_message_processed(message_data['id'])
                        
                        # Small delay between processing messages
                        await asyncio.sleep(1)
                        
                    except Exception as e:
                        logger.error(f"❌ Error processing queued message {message_data['id']}: {e}")
                        # Mark as processed even if failed to avoid infinite loop
                        await self.db.mark_message_processed(message_data['id'])
                
                logger.info("✅ Finished processing queued messages")
            
        except Exception as e:
            logger.error(f"❌ Error in process_message_queue: {e}")
        finally:
            self.processing_queue = False
    
    async def start_handler(self, event):
        """Handle /start command"""
        user = await event.get_sender()
        
        # Check if bot is starting up or not fully ready
        if not self.bot or not hasattr(self, 'bot_started') or not self.bot_started:
            # Queue the start command for later processing
            await self.db.add_message_to_queue(user.id, '/start', 'start')
            await event.respond(
                "🔄 **ربات در حال راه‌اندازی است...**\n\n"
                "درخواست شما در صف قرار گرفت و به محض آماده شدن ربات پردازش خواهد شد.\n\n"
                "⏳ لطفاً چند لحظه صبر کنید..."
            )
            return
        
        # Add user to database
        await self.db.add_user(
            user.id, 
            user.username, 
            user.first_name, 
            user.last_name
        )
        
        # Update user activity
        await self.db.update_user_activity(user.id)
        
        logger.info(f"User {user.id} ({user.first_name}) started the bot")
        
        # Check if user is member of sponsor channel (if force join is enabled)
        if hasattr(self, 'admin_handlers') and self.admin_handlers:
            is_member = await self.admin_handlers.check_user_membership(user.id)
            if not is_member:
                join_message = self.admin_handlers.get_join_channel_message()
                sponsor_username = ADMIN_PANEL_CONFIG.get('sponsor_channel_username', '')
                
                buttons = []
                if sponsor_username:
                    buttons.append([Button.url(f"📢 عضویت در کانال", f"https://t.me/{sponsor_username}")])
                    buttons.append([Button.inline("✅ عضو شدم، بررسی کن", b"check_membership")])
                
                await event.respond(join_message, buttons=buttons)
                return
        
        await event.respond(
            MESSAGES['start'],
            buttons=[
                [Button.inline('📋 راهنما', 'help'), Button.inline('📊 آمار', 'stats')]
            ],
            parse_mode='md'
        )
    
    async def help_handler(self, event):
        """Handle /help command"""
        await event.respond(MESSAGES['help'], parse_mode='md')
    
    async def sessions_handler(self, event):
        """Handle /sessions command (Admin only)"""
        user = await event.get_sender()
        if user.id not in ADMIN_IDS:
            await event.respond('❌ دسترسی مجاز نیست. فقط برای مدیر.')
            return
        
        sessions_info = await self.session_manager.get_sessions_status()
        if not sessions_info:
            await event.respond('🚫 هیچ جلسه فعالی یافت نشد.')
            return
        
        message = "📱 **جلسات فعال Userbot:**\n\n"
        for session_name, info in sessions_info.items():
            status = "🟢 فعال" if info['active'] else "🔴 غیرفعال"
            message += f"• **{session_name}**: {status}\n"
            message += f"  └ استفاده: {info['usage_count']} | آخرین استفاده: {info['last_used']}\n\n"
        
        await event.respond(message, parse_mode='md')
    
    async def stats_handler(self, event):
        """Handle /stats command"""
        user = await event.get_sender()
        if user.id not in ADMIN_IDS:
            # Show user stats
            user_stats = await self.db.get_user_stats(user.id)
            message = f"📊 **آمار شما:**\n\n"
            message += f"• دانلودها: {user_stats.get('downloads', 0)}\n"
            message += f"• تاریخ عضویت: {user_stats.get('join_date', 'نامشخص')}\n"
        else:
            # Show admin stats
            stats = await self.db.get_bot_stats()
            message = f"📊 **آمار ربات:**\n\n"
            message += f"• کل کاربران: {stats.get('total_users', 0)}\n"
            message += f"• کل دانلودها: {stats.get('total_downloads', 0)}\n"
            message += f"• جلسات فعال: {len(self.session_manager.active_sessions)}\n"
            message += f"• دانلودهای امروز: {stats.get('today_downloads', 0)}\n"
        
        await event.respond(message, parse_mode='md')
    
    async def cleanup_handler(self, event):
        """Handle /cleanup command (Admin only)"""
        user = await event.get_sender()
        if user.id not in ADMIN_IDS:
            await event.respond('❌ دسترسی مجاز نیست. فقط برای مدیر.')
            return
        
        cleaned_files = await self.download_service.cleanup_temp_files()
        await event.respond(f"🧹 {cleaned_files} فایل موقت پاکسازی شد.")
    
    async def url_handler(self, event):
        """Handle URL messages"""
        # Skip if it's a command
        if event.text.startswith('/'):
            return
        
        user = await event.get_sender()
        
        # Check if bot is starting up or not fully ready
        if not self.bot or not hasattr(self, 'bot_started') or not self.bot_started:
            # Queue the message for later processing
            await self.db.add_message_to_queue(user.id, event.text, 'url')
            await event.respond(
                "🔄 **ربات در حال راه‌اندازی است...**\n\n"
                "درخواست شما در صف قرار گرفت و به محض آماده شدن ربات پردازش خواهد شد.\n\n"
                "⏳ لطفاً چند لحظه صبر کنید..."
            )
            return
        
        # Check if user is member of sponsor channel (if force join is enabled)
        if hasattr(self, 'admin_handlers') and self.admin_handlers:
            is_member = await self.admin_handlers.check_user_membership(user.id)
            if not is_member:
                join_message = self.admin_handlers.get_join_channel_message()
                sponsor_username = ADMIN_PANEL_CONFIG.get('sponsor_channel_username', '')
                
                buttons = []
                if sponsor_username:
                    buttons.append([Button.url(f"📢 عضویت در کانال", f"https://t.me/{sponsor_username}")])
                    buttons.append([Button.inline("✅ عضو شدم، بررسی کن", b"check_membership")])
                
                await event.respond(join_message, buttons=buttons)
                return
        
        # Rate limiting
        if RATE_LIMIT_CONFIG['enabled']:
            if not await self.rate_limiter.is_allowed(user.id):
                cooldown = await self.rate_limiter.get_cooldown_time(user.id)
                await event.respond(
                    MESSAGES['rate_limited'].format(seconds=cooldown)
                )
                return
        
        # Check for YouTube URL
        youtube_match = YOUTUBE_PATTERN.search(event.text)
        if youtube_match:
            await self.handle_youtube_url(event, event.text)
            return
        
        # Check for Instagram URL
        instagram_match = INSTAGRAM_PATTERN.search(event.text)
        if instagram_match:
            await self.handle_instagram_url(event, event.text)
            return
        
        # If no valid URL found, ignore or send help
        if 'http' in event.text.lower():
            await event.respond(MESSAGES['invalid_link'])
    
    async def get_available_qualities(self, url: str) -> Dict[str, bool]:
        """Get available qualities for a YouTube video"""
        try:
            info = await self.download_service.get_download_info(url)
            if not info['success']:
                return {'audio': True}  # At least audio should be available
            
            available_qualities = {
                '4k': False,
                '1440p': False, 
                '1080p': False,
                'hd': False,  # 720p
                'sd': False,  # 480p
                '360p': False,
                '240p': False,
                '144p': False,
                'audio': True  # Audio is always available
            }
            
            # Check available formats
            for format_info in info.get('formats', []):
                height = format_info.get('height', 0)
                vcodec = format_info.get('vcodec', 'none')
                
                # Skip audio-only formats for video quality detection
                if vcodec == 'none' or height == 0:
                    continue
                    
                if height >= 2160:
                    available_qualities['4k'] = True
                elif height >= 1440:
                    available_qualities['1440p'] = True
                elif height >= 1080:
                    available_qualities['1080p'] = True
                elif height >= 720:
                    available_qualities['hd'] = True
                elif height >= 480:
                    available_qualities['sd'] = True
                elif height >= 360:
                    available_qualities['360p'] = True
                elif height >= 240:
                    available_qualities['240p'] = True
                elif height >= 144:
                    available_qualities['144p'] = True
            
            # If no video qualities found, enable basic qualities as fallback
            if not any(available_qualities.values()):
                available_qualities.update({
                    '1080p': True,
                    'hd': True,
                    'sd': True,
                    '360p': True
                })
            
            return available_qualities
            
        except Exception as e:
            logger.error(f"Error getting available qualities: {e}")
            return {'audio': True, '1080p': True, 'hd': True, 'sd': True}  # Fallback qualities
    
    async def handle_youtube_url(self, event, url: str):
        """Handle YouTube URL with dynamic quality selection"""
        user = await event.get_sender()
        
        # Check if it's a YouTube Short
        is_short = 'shorts/' in url or '/shorts/' in url
        
        # Show loading message
        loading_msg = await event.respond("🔍 **در حال بررسی کیفیت‌های موجود...**")
        
        try:
            # Get available qualities with timeout
            available_qualities = await asyncio.wait_for(
                self.get_available_qualities(url),
                timeout=120  # 120 seconds timeout
            )
            
            # Get video info for file sizes
            video_info = await self.download_service.get_download_info(url)
            
            # Check if video info extraction failed
            if not video_info.get('success'):
                await loading_msg.edit(
                    f"❌ **خطا در دریافت اطلاعات ویدیو:**\n\n{video_info.get('error', 'خطای نامشخص')}\n\n💡 لطفاً دوباره تلاش کنید یا لینک دیگری ارسال کنید."
                )
                return
            
            # Build dynamic buttons - each quality in separate row with file size
            quality_buttons = []
        
            # Quality order from highest to lowest
            quality_order = [
                ('4k', '4K Ultra HD'),
                ('1440p', '1440p QHD'),
                ('1080p', '1080p Full HD'),
                ('hd', '720p HD'),
                ('sd', '480p SD'),
                ('360p', '360p'),
                ('240p', '240p'),
                ('144p', '144p')
            ]
            
            for quality_key, quality_label in quality_order:
                if available_qualities.get(quality_key):
                    # Try to find file size for this quality
                    file_size_text = ""
                    if video_info.get('success') and video_info.get('formats'):
                        # Find matching format for this quality
                        target_height = {
                            '4k': 2160, '1440p': 1440, '1080p': 1080,
                            'hd': 720, 'sd': 480, '360p': 360, '240p': 240, '144p': 144
                        }.get(quality_key, 0)
                        
                        best_format = None
                        for fmt in video_info['formats']:
                            fmt_height = fmt.get('height', 0)
                            vcodec = fmt.get('vcodec', 'none')
                            
                            # Skip audio-only formats
                            if vcodec == 'none' or fmt_height == 0:
                                continue
                                
                            # Find closest match to target height (not exceeding it)
                            if fmt_height <= target_height:
                                if not best_format or abs(fmt_height - target_height) < abs(best_format.get('height', 0) - target_height):
                                    best_format = fmt
                        
                        if best_format:
                            # Use filesize or filesize_approx
                            filesize = best_format.get('filesize') or best_format.get('filesize_approx')
                            if filesize:
                                from utils.helpers import FileUtils
                                file_size_text = f" • {FileUtils.format_file_size(filesize)}"
                    
                    button_text = f"📹 {quality_label}{file_size_text}"
                    quality_buttons.append([Button.inline(button_text, f'yt_{quality_key}_{user.id}')])
            
            # Always add audio and thumbnail options in separate rows
            quality_buttons.append([Button.inline('🎵 فقط صدا (MP3)', f'yt_audio_{user.id}')])
            quality_buttons.append([Button.inline('🖼️ تامنیل', f'yt_thumbnail_{user.id}')])
        
            # Store URL temporarily
            await self.db.store_temp_url(user.id, url, 'youtube')
            
            video_type = "🩳 **یوتیوب شورت" if is_short else "🎬 **ویدیو یوتیوب"
            
            # Update the loading message with quality options
            await loading_msg.edit(
                f"{video_type} تشخیص داده شد!**\n\n🎯 کیفیت‌های موجود را انتخاب کنید:",
                buttons=quality_buttons,
                parse_mode='md'
            )
            
        except asyncio.TimeoutError:
            await loading_msg.edit(
                "⏰ **زمان انتظار تمام شد!**\n\n"
                "❌ بررسی کیفیت‌ها زمان زیادی طول کشید.\n\n"
                "💡 **راه‌حل‌ها:**\n"
                "• دوباره لینک را ارسال کنید\n"
                "• از لینک کوتاه‌تر استفاده کنید\n"
                "• چند دقیقه صبر کنید و مجدداً تلاش کنید"
            )
        except Exception as e:
            logger.error(f"Error in handle_youtube_url: {e}")
            await loading_msg.edit(
                "❌ **خطا در پردازش لینک یوتیوب!**\n\n"
                "💡 لطفاً دوباره تلاش کنید یا لینک دیگری ارسال کنید."
            )
    
    async def handle_instagram_url(self, event, url: str):
        """Handle Instagram URL with options"""
        user = await event.get_sender()
        
        # Check if it's a story
        is_story = '/stories/' in url or 'story' in url.lower()
        
        # Show download options
        if is_story:
            buttons = [
                [Button.inline('📹 دانلود استوری', f'ig_story_{user.id}')]
            ]
            content_type = "📖 **استوری اینستاگرام"
        else:
            buttons = [
                [Button.inline('📹 بهترین کیفیت', f'ig_best_{user.id}'), Button.inline('🎬 فقط ویدیو', f'ig_video_{user.id}')],
                [Button.inline('🖼️ فقط تصویر', f'ig_image_{user.id}')]
            ]
            content_type = "📱 **محتوای اینستاگرام"
        
        # Store URL temporarily
        await self.db.store_temp_url(user.id, url, 'instagram')
        
        await event.respond(
            f"{content_type} تشخیص داده شد!**\n\n📥 نوع دانلود را انتخاب کنید:",
            buttons=buttons,
            parse_mode='md'
        )
    
    async def callback_handler(self, event):
        """Handle callback queries"""
        data = event.data.decode('utf-8')
        user = await event.get_sender()
        
        if data == "check_membership":
            # بررسی عضویت کاربر
            if hasattr(self, 'admin_handlers') and self.admin_handlers:
                is_member = await self.admin_handlers.check_user_membership(user.id)
                if is_member:
                    await event.edit(
                        "✅ **عضویت تأیید شد!**\n\n"
                        "حالا می‌توانید از ربات استفاده کنید.\n"
                        "لینک یوتیوب یا اینستاگرام خود را ارسال کنید."
                    )
                else:
                    await event.answer(
                        "❌ هنوز عضو کانال نشده‌اید. لطفاً ابتدا عضو شوید.",
                        alert=True
                    )
            return
        
        if data == 'help':
            await event.answer()
            await event.respond(MESSAGES['help'], parse_mode='md')
            return
        
        if data == 'stats':
            await event.answer()
            await self.stats_handler(event)
            return
        
        if data == 'settings':
            await event.answer()
            await event.respond(
                "⚙️ **تنظیمات ربات:**\n\n🔧 در حال حاضر تنظیمات خاصی در دسترس نیست.\nبرای درخواست ویژگی جدید با مدیر تماس بگیرید.",
                parse_mode='md'
            )
            return
        
        if data == 'about':
            await event.answer()
            await event.respond(
                "ℹ️ **درباره ربات:**\n\n🤖 ربات دانلود پیشرفته یوتیوب و اینستاگرام\n📅 نسخه: 2.0\n👨‍💻 توسعه‌دهنده: تیم فنی\n\n✨ **ویژگی‌ها:**\n• دانلود با کیفیت بالا\n• پشتیبانی از چندین فرمت\n• رابط کاربری فارسی\n• سرعت بالا و پایداری",
                parse_mode='md'
            )
            return
        
        # Handle download callbacks
        if data.startswith(('yt_', 'ig_')):
            await self.handle_download_callback(event, data)
    
    async def handle_download_callback(self, event, callback_data: str):
        """Handle download callback with progress tracking"""
        await event.answer()
        
        user = await event.get_sender()
        parts = callback_data.split('_')
        platform = parts[0]  # 'yt' or 'ig'
        quality = parts[1]   # 'best', 'hd', 'sd', 'audio', etc.
        user_id = int(parts[2])
        
        if user.id != user_id:
            await event.respond('❌ این دکمه برای شما نیست!')
            return
        
        # Get stored URL
        url_data = await self.db.get_temp_url(user.id)
        if not url_data:
            await event.respond('❌ لینک منقضی شده. لطفاً دوباره لینک را ارسال کنید.')
            return
        
        url = url_data['url']
        platform_full = 'youtube' if platform == 'yt' else 'instagram'
        
        # Check if we have active sessions
        if not self.session_manager.active_sessions:
            await event.respond(MESSAGES['no_sessions'])
            return
        
        # Start download process
        progress_message = await event.respond(MESSAGES['processing'])
        
        try:
            # Get quality format
            quality_format = QUALITY_OPTIONS[platform_full].get(quality, 'best')
            
            # Download with progress tracking
            async def progress_callback(progress_data):
                await self.update_progress(progress_message, progress_data)
            
            result = await self.download_service.download_and_upload(
                url=url,
                platform=platform_full,
                quality=quality_format,
                progress_callback=progress_callback
            )
            
            if result['success']:
                # Send the file
                file_path = result['file_path']
                file_size = result['file_size']
                
                # Prepare file attributes
                attributes = []
                if result['media_type'] == 'video':
                    # Get video duration safely
                    duration = result.get('duration', 0)
                    if duration is None or duration <= 0:
                        try:
                            duration = TimeUtils.get_video_duration(file_path)
                        except:
                            duration = 0
                    
                    # Get video dimensions safely
                    width = result.get('width', 0)
                    height = result.get('height', 0)
                    if width is None or width <= 0:
                        width = 640
                    if height is None or height <= 0:
                        height = 480
                    
                    # Ensure all values are integers
                    duration = int(duration) if duration and duration > 0 else 0
                    width = int(width) if width and width > 0 else 640
                    height = int(height) if height and height > 0 else 480
                    
                    attributes.append(DocumentAttributeVideo(
                        duration=duration,
                        w=width,
                        h=height,
                        supports_streaming=True
                    ))
                elif result['media_type'] == 'audio':
                    duration = result.get('duration', 0)
                    if duration is None or duration <= 0:
                        duration = 0
                    duration = int(duration)
                    
                    attributes.append(DocumentAttributeAudio(
                        duration=duration,
                        title=result.get('title', ''),
                        performer=result.get('uploader', '')
                    ))
                
                # Upload using bot client (not userbot session)
                # Update progress to uploading with progress bar
                async def upload_progress_callback(current, total):
                    percent = int((current / total) * 100) if total > 0 else 0
                    bar_length = 15
                    filled_length = int(bar_length * percent // 100)
                    bar = '🟩' * filled_length + '⬜' * (bar_length - filled_length)
                    
                    progress_text = f"📤 **در حال آپلود به تلگرام...**\n\n"
                    progress_text += f"📊 **پیشرفت:** {percent}%\n"
                    progress_text += f"{bar}\n\n"
                    progress_text += f"📁 **اندازه:** {FileUtils.format_file_size(current)} / {FileUtils.format_file_size(total)}\n\n"
                    progress_text += f"⏳ *در حال ارسال...*"
                    
                    try:
                        await progress_message.edit(progress_text, parse_mode='md')
                    except:
                        pass
                
                try:
                    # Prepare quality info for caption
                    quality_info = ""
                    if quality != 'best':
                        if quality == 'audio':
                            quality_info = "🎵 صوتی"
                        elif quality in ['4k', '1440p', '1080p', 'hd', 'sd', '720p', '480p', '360p', '240p', '144p']:
                            quality_map = {
                                '4k': '4K (2160p)',
                                '1440p': '1440p QHD',
                                '1080p': '1080p Full HD',
                                'hd': '720p HD',
                                'sd': '480p SD',
                                '720p': '720p HD',
                                '480p': '480p',
                                '360p': '360p',
                                '240p': '240p',
                                '144p': '144p'
                            }
                            quality_info = f"🎥 {quality_map.get(quality, quality)}"
                        else:
                            quality_info = f"📹 {quality}"
                    else:
                        quality_info = "📹 بهترین کیفیت"
                    
                    # Send file using the main bot client with progress callback
                    await self.bot.send_file(
                        event.chat_id,
                        file_path,
                        caption=f"✅ **{result['title']}**\n\n📊 اندازه: {FileUtils.format_file_size(file_size)}\n{quality_info}\n🎬 پلتفرم: {platform_full.title()}\n🚀 دانلود شده توسط ربات",
                        attributes=attributes,
                        parse_mode='md',
                        progress_callback=upload_progress_callback
                    )
                    
                    # Log successful download only after successful send
                    await self.db.log_download(
                        user.id, url, platform_full, result['media_type'],
                        file_size, 'bot_client', 'success'
                    )
                    
                    # Show success message
                    await progress_message.edit(
                        f"🎉 **ارسال موفقیت‌آمیز!**\n\n"
                        f"✅ فایل **{result['title'][:50]}{'...' if len(result['title']) > 50 else ''}** با موفقیت ارسال شد.\n\n"
                        f"📊 **اطلاعات فایل:**\n"
                        f"• اندازه: {FileUtils.format_file_size(file_size)}\n"
                        f"• کیفیت: {quality_info.replace('🎥 ', '').replace('🎵 ', '').replace('📹 ', '')}\n"
                        f"• نوع: {result['media_type'].title()}\n"
                        f"• پلتفرم: {platform_full.title()}\n\n"
                        f"💫 *از استفاده از ربات متشکریم!*",
                        parse_mode='md'
                    )
                    
                except Exception as send_error:
                    logger.error(f"File send error: {send_error}")
                    await progress_message.edit(f"❌ خطا در ارسال فایل: {str(send_error)}")
                    
                    # Log failed send
                    await self.db.log_download(
                        user.id, url, platform_full, result['media_type'],
                        file_size, 'bot_client', 'send_failed'
                    )
                
                finally:
                    # Clean up temporary file after send attempt
                    try:
                        import os
                        if os.path.exists(file_path):
                            os.remove(file_path)
                            logger.debug(f"Cleaned up file: {file_path}")
                            # Also remove parent directory if empty
                            parent_dir = os.path.dirname(file_path)
                            if os.path.exists(parent_dir) and not os.listdir(parent_dir):
                                os.rmdir(parent_dir)
                                logger.debug(f"Cleaned up directory: {parent_dir}")
                    except Exception as cleanup_error:
                        logger.debug(f"Cleanup error: {cleanup_error}")
            else:
                await progress_message.edit(f"❌ Download failed: {result['error']}")
                
        except Exception as e:
            logger.error(f"Download error for user {user.id}: {e}")
            await progress_message.edit(MESSAGES['error'])
            
            # Log failed download
            await self.db.log_download(
                user.id, url, platform_full, 'unknown', 0, 'none', 'failed'
            )
    
    async def update_progress(self, message, progress_data):
        """Update progress message with detailed information"""
        try:
            if progress_data['status'] == 'downloading':
                percent = progress_data.get('percent', 0)
                speed = progress_data.get('speed', 'نامشخص')
                eta = progress_data.get('eta', 'نامشخص')
                
                # Create animated progress bar
                bar_length = 15
                filled_length = int(bar_length * percent // 100)
                bar = '🟩' * filled_length + '⬜' * (bar_length - filled_length)
                
                # Format speed nicely
                if speed != 'نامشخص' and speed != 'Unknown':
                    try:
                        # Clean up speed string
                        speed_clean = speed.replace('/s', '/ثانیه').replace('MiB', 'مگابایت').replace('KiB', 'کیلوبایت')
                    except:
                        speed_clean = speed
                else:
                    speed_clean = 'در حال محاسبه...'
                
                # Format ETA nicely
                if eta != 'نامشخص' and eta != 'Unknown':
                    try:
                        eta_clean = eta.replace('s', ' ثانیه').replace('m', ' دقیقه').replace('h', ' ساعت')
                    except:
                        eta_clean = eta
                else:
                    eta_clean = 'در حال محاسبه...'
                
                progress_text = f"📥 **در حال دانلود محتوا...**\n\n"
                progress_text += f"📊 **پیشرفت:** {percent}%\n"
                progress_text += f"{bar}\n\n"
                progress_text += f"⚡ **سرعت:** {speed_clean}\n"
                progress_text += f"⏰ **زمان باقی‌مانده:** {eta_clean}\n\n"
                progress_text += f"💡 *لطفاً صبر کنید...*"
                
            elif progress_data['status'] == 'uploading':
                progress_text = "📤 **در حال آپلود به تلگرام...**\n\n"
                progress_text += "🔄 فایل در حال ارسال است...\n"
                progress_text += "📊 آپلود از طریق سرورهای تلگرام\n\n"
                progress_text += "⏳ *تقریباً تمام شد!*"
            elif progress_data['status'] == 'finished':
                progress_text = "✅ **دانلود کامل شد!**\n\n"
                progress_text += "📤 در حال آپلود نهایی...\n\n"
                progress_text += "🎉 *چند لحظه دیگر آماده است!*"
            else:
                progress_text = "🔄 **در حال پردازش درخواست...**\n\n"
                progress_text += "🔍 تجزیه و تحلیل لینک...\n\n"
                progress_text += "⏳ *لطفاً کمی صبر کنید...*"
            
            await message.edit(progress_text, parse_mode='md')
        except Exception as e:
            logger.debug(f"Progress update error: {e}")

async def setup_bot_handlers(session_manager: SessionManager) -> TelegramClient:
    """Setup and return configured bot"""
    handlers = BotHandlers(session_manager)
    return await handlers.setup_bot()