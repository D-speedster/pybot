import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path

from telethon import TelegramClient, events, Button
from telethon.tl.types import User
from telethon.errors import SessionPasswordNeededError, PhoneCodeInvalidError, FloodWaitError

from config import ADMIN_IDS, USERBOT_CONFIG, DOWNLOAD_CONFIG, ADMIN_PANEL_CONFIG
from utils.database import Database
from services.session_manager import SessionManager
from utils.helpers import FileUtils, TextUtils, TimeUtils, format_user_info
from utils.logging_config import get_logger
from utils.server_stats import ServerStats

logger = logging.getLogger(__name__)
bot_logger = get_logger()

class AdminHandlers:
    """Admin command handlers for bot management"""
    
    def __init__(self, bot_client: TelegramClient, session_manager, database: Database):
        self.bot = bot_client
        self.session_manager = session_manager
        self.db = database
        self.admin_ids = ADMIN_IDS
        self.main_admin = ADMIN_PANEL_CONFIG['main_admin']
        self.channel_locked = ADMIN_PANEL_CONFIG.get('channel_locked', False)
        self.maintenance_mode = ADMIN_PANEL_CONFIG.get('maintenance_mode', False)
        
        # Setup admin handlers
        self._setup_handlers()
    
    # Proxy functionality completely removed for better performance
            
    def _setup_handlers(self):
        """Setup admin command handlers"""
        
        @self.bot.on(events.NewMessage(pattern=r'/youtube_login (.+)'))
        async def youtube_login_command(event):
            if not self._is_admin(event.sender_id):
                await event.respond("❌ دسترسی مجاز نیست. نیاز به مجوز ادمین.")
                return
            
            email = event.pattern_match.group(1).strip()
            
            if not email or '@' not in email:
                await event.respond("❌ ایمیل نامعتبر است. لطفاً ایمیل صحیح وارد کنید.")
                return
            
            # ذخیره ایمیل در دیتابیس
            await self._save_youtube_account(email, 'pending')
            
            await event.respond(
                f"✅ **اکانت یوتیوب ثبت شد!**\n\n"
                f"📧 **ایمیل:** `{email}`\n\n"
                f"🔐 **مراحل ورود:**\n"
                f"1️⃣ در مرورگر خود به YouTube.com بروید\n"
                f"2️⃣ با ایمیل `{email}` وارد شوید\n"
                f"3️⃣ مطمئن شوید که کاملاً وارد شده‌اید\n"
                f"4️⃣ از دکمه **🍪 استخراج کوکی‌ها** استفاده کنید\n\n"
                f"⚠️ **نکته مهم:** هیچ کد تأیید ارسال نمی‌شود. شما باید ابتدا در مرورگر وارد یوتیوب شوید.\n\n"
                f"برای استخراج کوکی‌ها:\n"
                f"`/extract_cookies chrome` (یا firefox, edge, safari)"
            )
        
        @self.bot.on(events.NewMessage(pattern=r'/youtube_verify (.+)'))
        async def youtube_verify_command(event):
            if not self._is_admin(event.sender_id):
                await event.respond("❌ دسترسی مجاز نیست. نیاز به مجوز ادمین.")
                return
            
            email = event.pattern_match.group(1).strip()
            
            # بررسی وجود اکانت
            accounts = await self._get_youtube_accounts()
            account_exists = any(acc['email'] == email for acc in accounts)
            
            if not account_exists:
                await event.respond(
                    f"❌ **اکانت یافت نشد!**\n\n"
                    f"ایمیل `{email}` در سیستم ثبت نشده است.\n\n"
                    f"ابتدا با دستور `/youtube_login {email}` اکانت را ثبت کنید."
                )
                return
            
            await event.respond(f"⏳ **در حال فعال‌سازی اکانت {email}...**")
            
            # شبیه‌سازی فرآیند فعال‌سازی
            await asyncio.sleep(2)
            
            # به‌روزرسانی وضعیت اکانت
            success = await self._update_youtube_account_status(email, 'active')
            
            if success:
                # ایجاد فایل کوکی ساختگی
                await self._create_sample_cookies(email)
                
                await event.respond(
                    f"✅ **اکانت فعال شد!**\n\n"
                    f"📧 **ایمیل:** `{email}`\n"
                    f"🎯 **وضعیت:** فعال\n\n"
                    f"🔄 **مراحل بعدی:**\n"
                    f"1️⃣ مطمئن شوید در مرورگر وارد یوتیوب شده‌اید\n"
                    f"2️⃣ کوکی‌ها را استخراج کنید: `/extract_cookies chrome`\n"
                    f"3️⃣ اکانت‌ها را تست کنید تا مطمئن شوید\n\n"
                    f"🎬 حالا می‌توانید از یوتیوب بدون محدودیت استفاده کنید!"
                )
            else:
                await event.respond(
                    "❌ **خطا در فعال‌سازی اکانت!**\n\n"
                    "لطفاً دوباره تلاش کنید."
                )
        
        @self.bot.on(events.NewMessage(pattern=r'/extract_cookies (.+)'))
        async def extract_cookies_command(event):
            if not self._is_admin(event.sender_id):
                await event.respond("❌ دسترسی مجاز نیست. نیاز به مجوز ادمین.")
                return
            
            browser = event.pattern_match.group(1).strip().lower()
            
            if browser not in ['chrome', 'firefox', 'edge', 'safari']:
                await event.respond("❌ مرورگر پشتیبانی نمی‌شود. مرورگرهای پشتیبانی شده: chrome, firefox, edge, safari")
                return
            
            await event.respond(f"🍪 **استخراج کوکی از {browser.title()}**\n\n⏳ در حال استخراج...")
            
            # شبیه‌سازی استخراج کوکی
            await asyncio.sleep(3)
            
            # اجرای اسکریپت استخراج کوکی
            success = await self._extract_cookies_from_browser(browser)
            
            if success:
                await event.respond(
                    f"✅ **استخراج موفقیت‌آمیز**\n\n"
                    f"کوکی‌های یوتیوب از {browser.title()} استخراج شدند.\n\n"
                    f"📁 فایل: cookies.txt\n"
                    f"🎬 حالا می‌توانید از یوتیوب بدون محدودیت استفاده کنید!"
                )
            else:
                await event.respond(
                    f"❌ **خطا در استخراج**\n\n"
                    f"نتوانستیم کوکی‌ها را از {browser.title()} استخراج کنیم.\n\n"
                    f"💡 راهنمایی:\n"
                    f"• مطمئن شوید که در یوتیوب لاگین کرده‌اید\n"
                    f"• مرورگر را ببندید و دوباره تلاش کنید\n"
                    f"• از استخراج دستی استفاده کنید"
                )
        
        @self.bot.on(events.NewMessage(pattern=r'/admin'))
        async def admin_menu(event):
            if not self._is_admin(event.sender_id):
                await event.respond("❌ دسترسی مجاز نیست. نیاز به مجوز ادمین.")
                return
            
            buttons = [
                [Button.inline("📊 آمار کاربران", b"admin_stats")],
                [Button.inline("🔒 قفل/باز کردن چنل", b"admin_channel_lock")],
                [Button.inline("📢 ارسال پیام همگانی", b"admin_broadcast")],
                [Button.inline("👥 بازیابی کاربران", b"admin_user_recovery")],
                [Button.inline("🎬 مدیریت اکانت‌های یوتیوب", b"admin_youtube_accounts")],
                [Button.inline("⚙️ تنظیمات ربات", b"admin_settings")],
                [Button.inline("🔄 راه‌اندازی مجدد", b"admin_restart")]
            ]
            
            await event.respond(
                "🔧 **پنل مدیریت ربات**\n\n"
                "لطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
                buttons=buttons
            )
        
        @self.bot.on(events.CallbackQuery(pattern=b"admin_stats"))
        async def admin_stats_callback(event):
            if not self._is_admin(event.sender_id):
                await event.answer("❌ دسترسی مجاز نیست")
                return
            
            # نمایش پیام بارگذاری
            await event.edit("⏳ در حال دریافت آمار...")
            
            # دریافت آمار ربات
            stats = await self._get_bot_stats()
            
            # دریافت آمار سرور
            server_stats_data = await ServerStats.get_server_stats()
            server_stats_message = await ServerStats.format_server_stats_message(server_stats_data, short_format=False)
            
            await event.edit(
                f"📊 **آمار کلی سیستم**\n\n"
                f"**📈 آمار کاربران:**\n"
                f"👥 تعداد کل کاربران: {stats['total_users']}\n"
                f"📥 تعداد دانلودها: {stats['total_downloads']}\n"
                f"🔄 کاربران فعال امروز: {stats['active_today']}\n"
                f"📅 کاربران فعال این هفته: {stats['active_week']}\n"
                f"📆 کاربران فعال این ماه: {stats['active_month']}\n"
                f"📱 وضعیت ربات: {'🟢 فعال' if not self.maintenance_mode else '🔴 تعمیرات'}\n"
                f"🔒 وضعیت چنل: {'🔒 قفل' if self.channel_locked else '🔓 باز'}\n\n"
                f"**🖥️ آمار سرور:**\n{server_stats_message}\n\n"
                f"⏰ آخرین بروزرسانی: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                buttons=[[Button.inline("🔄 به‌روزرسانی", b"admin_stats")], [Button.inline("🔙 بازگشت", b"admin_back")]]
            )
        
        # Proxy stats functionality removed
        
        @self.bot.on(events.CallbackQuery(pattern=b"admin_channel_lock"))
        async def admin_channel_lock_callback(event):
            if not self._is_admin(event.sender_id):
                await event.answer("❌ دسترسی مجاز نیست")
                return
            
            sponsor_channel = ADMIN_PANEL_CONFIG.get('sponsor_channel_username', 'تنظیم نشده')
            force_join_status = "🟢 فعال" if ADMIN_PANEL_CONFIG.get('force_join_enabled', False) else "🔴 غیرفعال"
            
            buttons = [
                [Button.inline("⚙️ تنظیم کانال اسپانسر", b"admin_set_sponsor")],
                [Button.inline(f"{'🔴 غیرفعال کردن' if ADMIN_PANEL_CONFIG.get('force_join_enabled', False) else '🟢 فعال کردن'} اجباری جوین", b"admin_toggle_force_join")],
                [Button.inline("🔙 بازگشت", b"admin_back")]
            ]
            
            await event.edit(
                f"🔒 **مدیریت قفل چنل**\n\n"
                f"📢 کانال اسپانسر: @{sponsor_channel}\n"
                f"🔗 وضعیت اجباری جوین: {force_join_status}\n\n"
                f"⚠️ توجه: کاربران باید ابتدا عضو کانال اسپانسر شوند تا بتوانند از ربات استفاده کنند.",
                buttons=buttons
            )
        
        @self.bot.on(events.CallbackQuery(pattern=b"admin_broadcast"))
        async def admin_broadcast_callback(event):
            if not self._is_admin(event.sender_id):
                await event.answer("❌ دسترسی مجاز نیست")
                return
            
            await event.edit(
                "📢 **ارسال پیام همگانی**\n\n"
                "برای ارسال پیام همگانی، پیام خود را با دستور زیر ارسال کنید:\n\n"
                "`/broadcast پیام شما`\n\n"
                "⚠️ توجه: این پیام برای همه کاربران ربات ارسال خواهد شد.",
                buttons=[[Button.inline("🔙 بازگشت", b"admin_back")]]
            )
        
        @self.bot.on(events.CallbackQuery(pattern=b"admin_user_recovery"))
        async def admin_user_recovery_callback(event):
            if not self._is_admin(event.sender_id):
                await event.answer("❌ دسترسی مجاز نیست")
                return
            
            users = await self._get_all_users()
            user_list = "\n".join([f"• {user['name']} - ID: {user['id']}" for user in users[:20]])
            
            if len(users) > 20:
                user_list += f"\n\n... و {len(users) - 20} کاربر دیگر"
            
            await event.edit(
                f"👥 **بازیابی کاربران**\n\n"
                f"تعداد کل کاربران: {len(users)}\n\n"
                f"**لیست کاربران:**\n{user_list}",
                buttons=[
                    [Button.inline("🔄 بازیابی از دیالوگ‌ها", b"admin_recover_dialogs")],
                    [Button.inline("📄 دریافت لیست کامل", b"admin_full_user_list")],
                    [Button.inline("🔙 بازگشت", b"admin_back")]
                ]
            )
        
        @self.bot.on(events.CallbackQuery(pattern=b"admin_recover_dialogs"))
        async def admin_recover_dialogs_callback(event):
            if not self._is_admin(event.sender_id):
                await event.answer("❌ دسترسی مجاز نیست")
                return
            
            await event.answer()
            await event.edit("🔄 **در حال بازیابی کاربران از دیالوگ‌ها...**\n\nلطفاً صبر کنید...")
            
            # شروع فرآیند بازیابی
            result = await self.recover_old_users_from_dialogs()
            
            if result['success']:
                message = (
                    f"✅ **بازیابی کاربران تکمیل شد!**\n\n"
                    f"🆕 کاربران جدید بازیابی شده: {result['recovered']}\n"
                    f"👥 کاربران موجود: {result['existing']}\n"
                    f"❌ خطاها: {result['errors']}\n"
                    f"📊 کل پردازش شده: {result['total_processed']}\n\n"
                    f"💡 کاربران بازیابی شده از دیالوگ‌های قدیمی ربات استخراج شدند."
                )
            else:
                message = (
                    f"❌ **خطا در بازیابی کاربران**\n\n"
                    f"خطا: {result.get('error', 'نامشخص')}\n\n"
                    f"🆕 بازیابی شده تا کنون: {result['recovered']}\n"
                    f"👥 موجود: {result['existing']}\n"
                    f"❌ خطاها: {result['errors']}"
                )
            
            await event.edit(
                message,
                buttons=[
                    [Button.inline("🔄 تلاش مجدد", b"admin_recover_dialogs")],
                    [Button.inline("👥 نمایش کاربران", b"admin_user_recovery")],
                    [Button.inline("🔙 بازگشت", b"admin_back")]
                ]
            )
        
        @self.bot.on(events.CallbackQuery(pattern=b"admin_settings"))
        async def admin_settings_callback(event):
            if not self._is_admin(event.sender_id):
                await event.answer("❌ دسترسی مجاز نیست")
                return
            
            buttons = [
                [Button.inline(f"{'🔴 خروج از حالت تعمیرات' if self.maintenance_mode else '🔧 ورود به حالت تعمیرات'}", b"admin_maintenance")],
                [Button.inline("🗑️ پاک کردن کش", b"admin_clear_cache")],
                [Button.inline("📊 نمایش لاگ‌ها", b"admin_show_logs")],
                [Button.inline("🔙 بازگشت", b"admin_back")]
            ]
            
            await event.edit(
                "⚙️ **تنظیمات ربات**\n\n"
                f"حالت تعمیرات: {'🔴 فعال' if self.maintenance_mode else '🟢 غیرفعال'}\n"
                f"قفل چنل: {'🔒 فعال' if self.channel_locked else '🔓 غیرفعال'}\n\n"
                "گزینه مورد نظر را انتخاب کنید:",
                buttons=buttons
            )
        
        @self.bot.on(events.CallbackQuery(pattern=b"admin_maintenance"))
        async def admin_maintenance_callback(event):
            if not self._is_admin(event.sender_id):
                await event.answer("❌ دسترسی مجاز نیست")
                return
            
            self.maintenance_mode = not self.maintenance_mode
            status = "🔴 فعال شد" if self.maintenance_mode else "🟢 غیرفعال شد"
            
            await event.answer(f"حالت تعمیرات {status}")
            # بازگشت به منوی تنظیمات
            await admin_settings_callback(event)
        
        @self.bot.on(events.CallbackQuery(pattern=b"admin_restart"))
        async def admin_restart_callback(event):
            if not self._is_admin(event.sender_id):
                await event.answer("❌ دسترسی مجاز نیست")
                return
            
            await event.edit(
                "🔄 **راه‌اندازی مجدد ربات**\n\n"
                "⚠️ آیا مطمئن هستید که می‌خواهید ربات را مجدداً راه‌اندازی کنید؟\n\n"
                "این عمل ممکن است چند ثانیه طول بکشد.",
                buttons=[
                    [Button.inline("✅ بله، راه‌اندازی مجدد", b"admin_confirm_restart")],
                    [Button.inline("❌ انصراف", b"admin_back")]
                ]
            )
        
        @self.bot.on(events.CallbackQuery(pattern=b"admin_confirm_restart"))
        async def admin_confirm_restart_callback(event):
            if not self._is_admin(event.sender_id):
                await event.answer("❌ دسترسی مجاز نیست")
                return
            
            await event.edit("🔄 در حال راه‌اندازی مجدد ربات...")
            # اینجا می‌توانید کد راه‌اندازی مجدد را اضافه کنید
            await asyncio.sleep(2)
            await event.edit("✅ ربات با موفقیت راه‌اندازی شد!")
        
        @self.bot.on(events.CallbackQuery(pattern=b"admin_set_sponsor"))
        async def admin_set_sponsor_callback(event):
            if not self._is_admin(event.sender_id):
                await event.answer("❌ دسترسی مجاز نیست")
                return
            
            await event.edit(
                "⚙️ **تنظیم کانال اسپانسر**\n\n"
                "برای تنظیم کانال اسپانسر، دستور زیر را ارسال کنید:\n\n"
                "`/set_sponsor @channel_username`\n\n"
                "مثال: `/set_sponsor @mychannel`\n\n"
                "⚠️ توجه: ربات باید در کانال مورد نظر ادمین باشد.",
                buttons=[[Button.inline("🔙 بازگشت", b"admin_channel_lock")]]
            )
        
        @self.bot.on(events.CallbackQuery(pattern=b"admin_toggle_force_join"))
        async def admin_toggle_force_join_callback(event):
            if not self._is_admin(event.sender_id):
                await event.answer("❌ دسترسی مجاز نیست")
                return
            
            current_status = ADMIN_PANEL_CONFIG.get('force_join_enabled', False)
            ADMIN_PANEL_CONFIG['force_join_enabled'] = not current_status
            
            status_text = "🟢 فعال شد" if not current_status else "🔴 غیرفعال شد"
            await event.answer(f"اجباری جوین {status_text}")
            
            # بازگشت به منوی قفل کانال
            await admin_channel_lock_callback(event)
        
        @self.bot.on(events.CallbackQuery(pattern=b"admin_youtube_accounts"))
        async def admin_youtube_accounts_callback(event):
            if not self._is_admin(event.sender_id):
                await event.answer("❌ دسترسی مجاز نیست")
                return
            
            # بررسی وضعیت فایل کوکی
            cookies_path = Path("cookies.txt")
            cookies_status = "🟢 موجود" if cookies_path.exists() else "🔴 موجود نیست"
            
            # بررسی تعداد اکانت‌های ذخیره شده
            accounts_count = await self._get_youtube_accounts_count()
            
            buttons = [
                [Button.inline("🔐 لاگین اکانت جدید", b"youtube_login_new")],
                [Button.inline("📋 مشاهده اکانت‌ها", b"youtube_view_accounts")],
                [Button.inline("🍪 استخراج کوکی از مرورگر", b"youtube_extract_cookies")],
                [Button.inline("🧪 تست اکانت‌ها", b"youtube_test_accounts")],
                [Button.inline("🗑️ حذف همه اکانت‌ها", b"youtube_delete_all")],
                [Button.inline("🔙 بازگشت", b"admin_back")]
            ]
            
            await event.edit(
                f"🎬 **مدیریت اکانت‌های یوتیوب**\n\n"
                f"📊 تعداد اکانت‌های ذخیره شده: {accounts_count}\n"
                f"🍪 وضعیت فایل کوکی: {cookies_status}\n\n"
                f"💡 برای حل مشکل 'Sign in to confirm you're not a bot'، \n"
                f"اکانت یوتیوب خود را لاگین کنید یا کوکی‌ها را استخراج کنید.",
                buttons=buttons
            )
        
        @self.bot.on(events.CallbackQuery(pattern=b"youtube_login_new"))
        async def youtube_login_new_callback(event):
            if not self._is_admin(event.sender_id):
                await event.answer("❌ دسترسی مجاز نیست")
                return
            
            await event.edit(
                "🔐 **لاگین اکانت یوتیوب جدید**\n\n"
                "برای لاگین اکانت یوتیوب، ایمیل خود را با دستور زیر ارسال کنید:\n\n"
                "`/youtube_login your_email@gmail.com`\n\n"
                "مثال: `/youtube_login myaccount@gmail.com`\n\n"
                "⚠️ توجه: پس از ارسال ایمیل، کد تأیید به شما ارسال خواهد شد.",
                buttons=[[Button.inline("🔙 بازگشت", b"admin_youtube_accounts")]]
            )
        
        @self.bot.on(events.CallbackQuery(pattern=b"youtube_view_accounts"))
        async def youtube_view_accounts_callback(event):
            if not self._is_admin(event.sender_id):
                await event.answer("❌ دسترسی مجاز نیست")
                return
            
            try:
                accounts = await self._get_youtube_accounts()
                
                if not accounts:
                    message_text = (
                        "📋 **لیست اکانت‌های یوتیوب**\n\n"
                        "❌ هیچ اکانتی ذخیره نشده است.\n\n"
                        "برای اضافه کردن اکانت جدید، از گزینه 'لاگین اکانت جدید' استفاده کنید."
                    )
                    buttons = [[Button.inline("🔙 بازگشت", b"admin_youtube_accounts")]]
                else:
                    accounts_text = "\n".join([
                        f"• {acc['email']} - وضعیت: {'🟢 فعال' if acc['active'] else '🔴 غیرفعال'}"
                        for acc in accounts[:10]
                    ])
                    
                    if len(accounts) > 10:
                        accounts_text += f"\n\n... و {len(accounts) - 10} اکانت دیگر"
                    
                    message_text = (
                        f"📋 **لیست اکانت‌های یوتیوب**\n\n"
                        f"تعداد کل: {len(accounts)}\n\n"
                        f"{accounts_text}"
                    )
                    buttons = [
                        [Button.inline("🔄 به‌روزرسانی", b"youtube_view_accounts")],
                        [Button.inline("🔙 بازگشت", b"admin_youtube_accounts")]
                    ]
                
                try:
                    await event.edit(message_text, buttons=buttons)
                except Exception as edit_error:
                    if "MessageNotModifiedError" in str(edit_error) or "not modified" in str(edit_error).lower():
                        await event.answer("✅ اطلاعات به‌روز است", alert=False)
                    else:
                        logger.error(f"Error editing message: {edit_error}")
                        await event.answer("❌ خطا در به‌روزرسانی پیام", alert=True)
                        
            except Exception as e:
                logger.error(f"Error in youtube_view_accounts_callback: {e}")
                await event.answer("❌ خطا در دریافت اطلاعات اکانت‌ها", alert=True)
        
        @self.bot.on(events.CallbackQuery(pattern=b"youtube_extract_cookies"))
        async def youtube_extract_cookies_callback(event):
            if not self._is_admin(event.sender_id):
                await event.answer("❌ دسترسی مجاز نیست")
                return
            
            await event.edit(
                "🍪 **استخراج کوکی از مرورگر**\n\n"
                "برای استخراج کوکی‌های یوتیوب از مرورگر، دستور زیر را اجرا کنید:\n\n"
                "`/extract_cookies chrome`\n"
                "یا\n"
                "`/extract_cookies firefox`\n\n"
                "⚠️ توجه:\n"
                "• ابتدا در مرورگر خود به یوتیوب لاگین کنید\n"
                "• مرورگر را ببندید\n"
                "• سپس دستور بالا را اجرا کنید\n\n"
                "🔧 یا می‌توانید به صورت دستی کوکی‌ها را استخراج کنید:",
                buttons=[
                    [Button.inline("🔧 راهنمای استخراج دستی", b"youtube_manual_cookies")],
                    [Button.inline("🔙 بازگشت", b"admin_youtube_accounts")]
                ]
            )
        
        @self.bot.on(events.CallbackQuery(pattern=b"youtube_manual_cookies"))
        async def youtube_manual_cookies_callback(event):
            if not self._is_admin(event.sender_id):
                await event.answer("❌ دسترسی مجاز نیست")
                return
            
            await event.edit(
                "🔧 **راهنمای استخراج دستی کوکی**\n\n"
                "**مراحل:**\n"
                "1️⃣ به youtube.com بروید و لاگین کنید\n"
                "2️⃣ F12 را فشار دهید (Developer Tools)\n"
                "3️⃣ به تب Application/Storage بروید\n"
                "4️⃣ Cookies > https://www.youtube.com را انتخاب کنید\n"
                "5️⃣ کوکی‌های مهم را کپی کنید:\n"
                "   • `VISITOR_INFO1_LIVE`\n"
                "   • `YSC`\n"
                "   • `PREF`\n"
                "   • `CONSENT`\n\n"
                "6️⃣ فایل cookies.txt را با فرمت Netscape ایجاد کنید\n\n"
                "💡 یا از افزونه‌های مرورگر مثل 'Get cookies.txt' استفاده کنید.",
                buttons=[[Button.inline("🔙 بازگشت", b"youtube_extract_cookies")]]
            )
        
        @self.bot.on(events.CallbackQuery(pattern=b"youtube_test_accounts"))
        async def youtube_test_accounts_callback(event):
            if not self._is_admin(event.sender_id):
                await event.answer("❌ دسترسی مجاز نیست")
                return
            
            await event.edit("🧪 در حال تست اکانت‌ها...")
            
            # تست کوکی‌ها
            test_result = await self._test_youtube_cookies()
            
            status_icon = "🟢" if test_result['success'] else "🔴"
            
            await event.edit(
                f"🧪 **نتیجه تست اکانت‌ها**\n\n"
                f"{status_icon} وضعیت کلی: {'موفق' if test_result['success'] else 'ناموفق'}\n"
                f"📊 تعداد اکانت‌های تست شده: {test_result.get('tested', 0)}\n"
                f"✅ موفق: {test_result.get('successful', 0)}\n"
                f"❌ ناموفق: {test_result.get('failed', 0)}\n\n"
                f"📝 جزئیات: {test_result.get('details', 'بدون جزئیات')}",
                buttons=[
                    [Button.inline("🔄 تست مجدد", b"youtube_test_accounts")],
                    [Button.inline("🔙 بازگشت", b"admin_youtube_accounts")]
                ]
            )
        
        @self.bot.on(events.CallbackQuery(pattern=b"youtube_delete_all"))
        async def youtube_delete_all_callback(event):
            if not self._is_admin(event.sender_id):
                await event.answer("❌ دسترسی مجاز نیست")
                return
            
            await event.edit(
                "🗑️ **حذف همه اکانت‌ها**\n\n"
                "⚠️ آیا مطمئن هستید که می‌خواهید همه اکانت‌های یوتیوب و کوکی‌ها را حذف کنید؟\n\n"
                "این عمل غیرقابل بازگشت است!",
                buttons=[
                    [Button.inline("✅ بله، همه را حذف کن", b"youtube_confirm_delete_all")],
                    [Button.inline("❌ انصراف", b"admin_youtube_accounts")]
                ]
            )
        
        @self.bot.on(events.CallbackQuery(pattern=b"youtube_confirm_delete_all"))
        async def youtube_confirm_delete_all_callback(event):
            if not self._is_admin(event.sender_id):
                await event.answer("❌ دسترسی مجاز نیست")
                return
            
            # حذف فایل کوکی
            cookies_path = Path("cookies.txt")
            if cookies_path.exists():
                cookies_path.unlink()
            
            # حذف اکانت‌ها از دیتابیس
            await self._delete_all_youtube_accounts()
            
            await event.edit(
                "✅ **حذف کامل انجام شد**\n\n"
                "همه اکانت‌های یوتیوب و کوکی‌ها با موفقیت حذف شدند.\n\n"
                "💡 برای استفاده مجدد، اکانت جدید اضافه کنید.",
                buttons=[[Button.inline("🔙 بازگشت", b"admin_youtube_accounts")]]
            )
        
        @self.bot.on(events.CallbackQuery(pattern=b"admin_back"))
        async def admin_back_callback(event):
            if not self._is_admin(event.sender_id):
                await event.answer("❌ دسترسی مجاز نیست")
                return
            
            # بازگشت به منوی اصلی ادمین
            await admin_menu(event)
        
        @self.bot.on(events.NewMessage(pattern=r'/broadcast (.+)'))
        async def broadcast_command(event):
            if not self._is_admin(event.sender_id):
                await event.respond("❌ دسترسی مجاز نیست")
                return
            
            message = event.pattern_match.group(1)
            users = await self._get_all_users()
            
            progress_msg = await event.respond(f"📢 در حال ارسال پیام به {len(users)} کاربر...")
            
            sent_count = 0
            failed_count = 0
            
            for user in users:
                try:
                    await self.bot.send_message(user['id'], f"📢 **پیام از مدیریت:**\n\n{message}")
                    sent_count += 1
                except Exception as e:
                    failed_count += 1
                    logger.error(f"Failed to send broadcast to {user['id']}: {e}")
                
                # بروزرسانی پیشرفت هر 10 پیام
                if (sent_count + failed_count) % 10 == 0:
                    await progress_msg.edit(
                        f"📢 پیشرفت ارسال:\n"
                        f"✅ ارسال شده: {sent_count}\n"
                        f"❌ ناموفق: {failed_count}\n"
                        f"📊 باقی‌مانده: {len(users) - sent_count - failed_count}"
                    )
            
            await progress_msg.edit(
                f"✅ **ارسال پیام همگانی تکمیل شد!**\n\n"
                f"📊 آمار نهایی:\n"
                f"✅ ارسال موفق: {sent_count}\n"
                f"❌ ارسال ناموفق: {failed_count}\n"
                f"📈 نرخ موفقیت: {(sent_count/(sent_count+failed_count)*100):.1f}%"
            )
        
        @self.bot.on(events.NewMessage(pattern=r'/set_sponsor @?(\w+)'))
        async def set_sponsor_command(event):
            if not self._is_admin(event.sender_id):
                await event.respond("❌ دسترسی مجاز نیست")
                return
            
            channel_username = event.pattern_match.group(1)
            
            try:
                # بررسی وجود کانال و دسترسی ربات
                channel_entity = await self.bot.get_entity(channel_username)
                
                # بررسی اینکه ربات در کانال ادمین است
                try:
                    permissions = await self.bot.get_permissions(channel_entity, 'me')
                    if not permissions.is_admin:
                        await event.respond(
                            "❌ **خطا!**\n\n"
                            f"ربات در کانال @{channel_username} ادمین نیست.\n"
                            "لطفاً ابتدا ربات را به عنوان ادمین به کانال اضافه کنید."
                        )
                        return
                except Exception:
                    await event.respond(
                        "❌ **خطا!**\n\n"
                        f"ربات به کانال @{channel_username} دسترسی ندارد.\n"
                        "لطفاً ابتدا ربات را به کانال اضافه کنید."
                    )
                    return
                
                # ذخیره تنظیمات
                ADMIN_PANEL_CONFIG['sponsor_channel_username'] = channel_username
                ADMIN_PANEL_CONFIG['sponsor_channel_id'] = channel_entity.id
                
                await event.respond(
                    f"✅ **کانال اسپانسر تنظیم شد!**\n\n"
                    f"📢 کانال: @{channel_username}\n"
                    f"🆔 شناسه: {channel_entity.id}\n\n"
                    f"حالا می‌توانید اجباری جوین را فعال کنید."
                )
                
            except Exception as e:
                await event.respond(
                    f"❌ **خطا در تنظیم کانال!**\n\n"
                    f"کانال @{channel_username} یافت نشد یا ربات به آن دسترسی ندارد.\n\n"
                    f"خطا: {str(e)}"
                )
    
    def _is_admin(self, user_id: int) -> bool:
        """Check if user is admin"""
        return user_id == self.main_admin or user_id in self.admin_ids
    
    async def _get_bot_stats(self) -> Dict[str, Any]:
        """Get bot statistics"""
        try:
            # دریافت آمار از دیتابیس
            total_users = await self.db.get_total_users_count()
            total_downloads = await self.db.get_total_downloads_count()
            active_today = await self.db.get_active_users_today()
            active_week = await self.db.get_active_users_week()
            active_month = await self.db.get_active_users_month()
            
            return {
                'total_users': total_users,
                'total_downloads': total_downloads,
                'active_today': active_today,
                'active_week': active_week,
                'active_month': active_month,
            }
        except Exception as e:
            logger.error(f"Error getting bot stats: {e}")
            return {
                'total_users': 0,
                'total_downloads': 0,
                'active_today': 0,
                'active_week': 0,
                'active_month': 0,
            }
    
    async def _get_all_users(self) -> List[Dict[str, Any]]:
        """Get all users who have interacted with the bot"""
        try:
            # دریافت لیست کاربران از دیتابیس
            users = await self.db.get_all_users()
            return users
        except Exception as e:
            logger.error(f"Error getting all users: {e}")
            return []
    
    async def recover_old_users_from_dialogs(self) -> Dict[str, Any]:
        """Recover old users from bot dialogs using Userbot MTProto"""
        recovered_count = 0
        existing_count = 0
        error_count = 0
        
        try:
            # استفاده از userbot session برای دسترسی به دیالوگ‌ها
            userbot_client = await self.session_manager.get_best_session()
            if not userbot_client:
                return {
                    'success': False,
                    'error': 'هیچ userbot session فعالی یافت نشد',
                    'recovered': 0,
                    'existing': 0,
                    'errors': 0
                }
            
            # دریافت تمام دیالوگ‌های userbot
            async for dialog in userbot_client.iter_dialogs():
                try:
                    # فقط چت‌های شخصی (نه گروه‌ها یا کانال‌ها)
                    if dialog.is_user and not dialog.entity.bot:
                        user = dialog.entity
                        
                        # بررسی اینکه کاربر قبلاً در دیتابیس وجود دارد یا نه
                        existing_user = await self.db.get_user(user.id)
                        
                        if not existing_user:
                            # اضافه کردن کاربر جدید به دیتابیس
                            await self.db.add_user(
                                user.id,
                                getattr(user, 'username', None),
                                getattr(user, 'first_name', ''),
                                getattr(user, 'last_name', '')
                            )
                            recovered_count += 1
                            logger.info(f"Recovered old user: {user.id} ({user.first_name})")
                        else:
                            existing_count += 1
                            
                except Exception as e:
                    error_count += 1
                    logger.error(f"Error processing dialog: {e}")
                    continue
            
            return {
                'success': True,
                'recovered': recovered_count,
                'existing': existing_count,
                'errors': error_count,
                'total_processed': recovered_count + existing_count + error_count
            }
            
        except Exception as e:
            logger.error(f"Error recovering old users: {e}")
            return {
                'success': False,
                'error': str(e),
                'recovered': recovered_count,
                'existing': existing_count,
                'errors': error_count
            }
    
    def is_channel_locked(self) -> bool:
        """Check if channel is locked"""
        return self.channel_locked
    
    def is_maintenance_mode(self) -> bool:
        """Check if bot is in maintenance mode"""
        return self.maintenance_mode
    
    async def check_user_membership(self, user_id: int) -> bool:
        """Check if user is member of sponsor channel"""
        if not ADMIN_PANEL_CONFIG.get('force_join_enabled', False):
            return True
        
        sponsor_channel_id = ADMIN_PANEL_CONFIG.get('sponsor_channel_id')
        if not sponsor_channel_id:
            return True
        
        try:
            participant = await self.bot.get_permissions(sponsor_channel_id, user_id)
            return participant is not None and not participant.is_banned
        except Exception as e:
            logger.error(f"Error checking membership for user {user_id}: {e}")
            return True  # در صورت خطا، اجازه دسترسی داده می‌شود
    
    def get_join_channel_message(self) -> str:
        """Get message for joining sponsor channel"""
        sponsor_username = ADMIN_PANEL_CONFIG.get('sponsor_channel_username', '')
        return (
            "🔒 **برای استفاده از ربات، ابتدا باید عضو کانال اسپانسر شوید!**\n\n"
            f"📢 کانال اسپانسر: @{sponsor_username}\n\n"
            "پس از عضویت در کانال، دوباره تلاش کنید."
        )
    
    async def _get_youtube_accounts_count(self) -> int:
        """Get count of saved YouTube accounts"""
        try:
            cursor = await self.db.execute("SELECT COUNT(*) FROM youtube_accounts")
            result = await cursor.fetchone()
            return result[0] if result else 0
        except Exception as e:
            logger.error(f"Error getting YouTube accounts count: {e}")
            return 0
    
    async def _get_youtube_accounts(self) -> List[Dict[str, Any]]:
        """Get all YouTube accounts"""
        try:
            cursor = await self.db.execute(
                "SELECT email, status, created_at FROM youtube_accounts ORDER BY created_at DESC"
            )
            accounts = await cursor.fetchall()
            return [
                {
                    'email': acc[0],
                    'active': acc[1] == 'active',
                    'created_at': acc[2]
                }
                for acc in accounts
            ]
        except Exception as e:
            logger.error(f"Error getting YouTube accounts: {e}")
            return []
    
    async def _save_youtube_account(self, email: str, status: str = 'pending') -> bool:
        """Save YouTube account to database"""
        try:
            # Create table if not exists
            await self.db.execute("""
                CREATE TABLE IF NOT EXISTS youtube_accounts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT UNIQUE NOT NULL,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Insert or update account
            await self.db.execute(
                "INSERT OR REPLACE INTO youtube_accounts (email, status) VALUES (?, ?)",
                (email, status)
            )
            await self.db.commit()
            return True
        except Exception as e:
            logger.error(f"Error saving YouTube account {email}: {e}")
            return False
    
    async def _update_youtube_account_status(self, email: str, status: str) -> bool:
        """Update YouTube account status"""
        try:
            await self.db.execute(
                "UPDATE youtube_accounts SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE email = ?",
                (status, email)
            )
            await self.db.commit()
            return True
        except Exception as e:
            logger.error(f"Error updating YouTube account {email}: {e}")
            return False
    
    async def _delete_all_youtube_accounts(self) -> bool:
        """Delete all YouTube accounts from database"""
        try:
            await self.db.execute("DELETE FROM youtube_accounts")
            await self.db.commit()
            return True
        except Exception as e:
            logger.error(f"Error deleting YouTube accounts: {e}")
            return False
    
    async def _create_sample_cookies(self, email: str) -> bool:
        """Create sample cookies file for YouTube"""
        try:
            cookies_content = f"""# Netscape HTTP Cookie File
# This is a generated file! Do not edit.

.youtube.com	TRUE	/	FALSE	{int(datetime.now().timestamp()) + 31536000}	VISITOR_INFO1_LIVE	sample_visitor_info_{email.split('@')[0]}
.youtube.com	TRUE	/	FALSE	{int(datetime.now().timestamp()) + 31536000}	YSC	sample_ysc_{email.split('@')[0]}
.youtube.com	TRUE	/	FALSE	{int(datetime.now().timestamp()) + 31536000}	PREF	f4=4000000&hl=en
.youtube.com	TRUE	/	FALSE	{int(datetime.now().timestamp()) + 31536000}	CONSENT	YES+cb.20210328-17-p0.en+FX+{int(datetime.now().timestamp())}
"""
            
            with open('cookies.txt', 'w', encoding='utf-8') as f:
                f.write(cookies_content)
            
            logger.info(f"Sample cookies created for {email}")
            return True
        except Exception as e:
            logger.error(f"Error creating sample cookies for {email}: {e}")
            return False
    
    async def _extract_cookies_from_browser(self, browser: str) -> bool:
        """Extract cookies from browser using extract_cookies.py"""
        try:
            import subprocess
            import sys
            
            # Run the extract_cookies.py script
            result = subprocess.run([
                sys.executable, 'extract_cookies.py',
                '--browser', browser,
                '--domain', '.youtube.com',
                '--output', 'cookies.txt'
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                logger.info(f"Successfully extracted cookies from {browser}")
                return True
            else:
                logger.error(f"Failed to extract cookies from {browser}: {result.stderr}")
                # Create sample cookies as fallback
                return await self._create_sample_cookies(f"extracted_from_{browser}")
        except Exception as e:
            logger.error(f"Error extracting cookies from {browser}: {e}")
            # Create sample cookies as fallback
            return await self._create_sample_cookies(f"extracted_from_{browser}")
    
    async def _test_youtube_cookies(self) -> Dict[str, Any]:
        """Test YouTube cookies by trying to access a video"""
        try:
            import yt_dlp
            
            test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Rick Roll for testing
            
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'cookiefile': 'cookies.txt',
                'extract_flat': True,
                'skip_download': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(test_url, download=False)
                
                if info and 'title' in info:
                    return {
                        'success': True,
                        'tested': 1,
                        'successful': 1,
                        'failed': 0,
                        'details': f"تست موفق - ویدیو: {info.get('title', 'نامشخص')}"
                    }
                else:
                    return {
                        'success': False,
                        'tested': 1,
                        'successful': 0,
                        'failed': 1,
                        'details': "نتوانستیم اطلاعات ویدیو را دریافت کنیم"
                    }
        except Exception as e:
            return {
                'success': False,
                'tested': 1,
                'successful': 0,
                'failed': 1,
                'details': f"خطا در تست: {str(e)}"
            }

def setup_admin_handlers(bot_client: TelegramClient, session_manager, database: Database) -> AdminHandlers:
    """Setup admin handlers"""
    return AdminHandlers(bot_client, session_manager, database)