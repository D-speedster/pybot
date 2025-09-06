import os
import re
import asyncio
import hashlib
import mimetypes
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from urllib.parse import urlparse, parse_qs
import logging

logger = logging.getLogger(__name__)

class FileUtils:
    """File management utilities"""
    
    @staticmethod
    def ensure_dir(path: str) -> Path:
        """Ensure directory exists and return Path object"""
        dir_path = Path(path)
        dir_path.mkdir(parents=True, exist_ok=True)
        return dir_path
    
    @staticmethod
    def get_file_size(file_path: str) -> int:
        """Get file size in bytes"""
        try:
            return os.path.getsize(file_path)
        except (OSError, FileNotFoundError):
            return 0
    
    @staticmethod
    def format_file_size(size_bytes: int) -> str:
        """Format file size in human readable format"""
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        
        return f"{size_bytes:.1f} {size_names[i]}"
    
    @staticmethod
    def get_safe_filename(filename: str, max_length: int = 100) -> str:
        """Get safe filename for filesystem"""
        # Remove or replace invalid characters
        safe_chars = re.sub(r'[<>:"/\\|?*]', '_', filename)
        safe_chars = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', safe_chars)
        
        # Limit length
        if len(safe_chars) > max_length:
            name, ext = os.path.splitext(safe_chars)
            safe_chars = name[:max_length - len(ext)] + ext
        
        # Ensure it's not empty
        if not safe_chars.strip():
            safe_chars = "download"
        
        return safe_chars.strip()
    
    @staticmethod
    def get_file_hash(file_path: str, algorithm: str = 'md5') -> Optional[str]:
        """Get file hash"""
        try:
            hash_obj = hashlib.new(algorithm)
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_obj.update(chunk)
            return hash_obj.hexdigest()
        except Exception as e:
            logger.error(f"❌ Error calculating hash for {file_path}: {e}")
            return None
    
    @staticmethod
    def cleanup_temp_files(temp_dir: str, max_age_hours: int = 24) -> int:
        """Clean up old temporary files"""
        try:
            temp_path = Path(temp_dir)
            if not temp_path.exists():
                return 0
            
            cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
            cleaned_count = 0
            
            for file_path in temp_path.rglob('*'):
                if file_path.is_file():
                    file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if file_time < cutoff_time:
                        try:
                            file_path.unlink()
                            cleaned_count += 1
                        except Exception as e:
                            logger.warning(f"⚠️ Could not delete {file_path}: {e}")
            
            logger.info(f"🧹 Cleaned up {cleaned_count} temporary files")
            return cleaned_count
        
        except Exception as e:
            logger.error(f"❌ Error cleaning temp files: {e}")
            return 0
    
    @staticmethod
    def get_mime_type(file_path: str) -> Tuple[Optional[str], Optional[str]]:
        """Get MIME type and subtype"""
        mime_type, _ = mimetypes.guess_type(file_path)
        if mime_type:
            main_type, sub_type = mime_type.split('/', 1)
            return main_type, sub_type
        return None, None

class URLUtils:
    """URL validation and parsing utilities"""
    
    # URL patterns
    YOUTUBE_PATTERNS = [
        r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=([\w-]+)',
        r'(?:https?://)?(?:www\.)?youtu\.be/([\w-]+)',
        r'(?:https?://)?(?:www\.)?youtube\.com/embed/([\w-]+)',
        r'(?:https?://)?(?:www\.)?youtube\.com/v/([\w-]+)',
        r'(?:https?://)?(?:m\.)?youtube\.com/watch\?v=([\w-]+)',
    ]
    
    INSTAGRAM_PATTERNS = [
        r'(?:https?://)?(?:www\.)?instagram\.com/p/([\w-]+)',
        r'(?:https?://)?(?:www\.)?instagram\.com/reel/([\w-]+)',
        r'(?:https?://)?(?:www\.)?instagram\.com/tv/([\w-]+)',
        r'(?:https?://)?(?:www\.)?instagram\.com/stories/[\w.-]+/([\d]+)',
    ]
    
    @staticmethod
    def is_youtube_url(url: str) -> bool:
        """Check if URL is a YouTube URL"""
        return any(re.search(pattern, url, re.IGNORECASE) for pattern in URLUtils.YOUTUBE_PATTERNS)
    
    @staticmethod
    def is_instagram_url(url: str) -> bool:
        """Check if URL is an Instagram URL"""
        return any(re.search(pattern, url, re.IGNORECASE) for pattern in URLUtils.INSTAGRAM_PATTERNS)
    
    @staticmethod
    def extract_video_id(url: str, platform: str) -> Optional[str]:
        """Extract video ID from URL"""
        patterns = URLUtils.YOUTUBE_PATTERNS if platform == 'youtube' else URLUtils.INSTAGRAM_PATTERNS
        
        for pattern in patterns:
            match = re.search(pattern, url, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    @staticmethod
    def normalize_url(url: str) -> str:
        """Normalize URL format"""
        url = url.strip()
        
        # Add https if no protocol
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        return url
    
    @staticmethod
    def get_platform_from_url(url: str) -> Optional[str]:
        """Determine platform from URL"""
        if URLUtils.is_youtube_url(url):
            return 'youtube'
        elif URLUtils.is_instagram_url(url):
            return 'instagram'
        return None
    
    @staticmethod
    def validate_url(url: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """Validate URL and return (is_valid, platform, video_id)"""
        try:
            normalized_url = URLUtils.normalize_url(url)
            platform = URLUtils.get_platform_from_url(normalized_url)
            
            if not platform:
                return False, None, None
            
            video_id = URLUtils.extract_video_id(normalized_url, platform)
            return True, platform, video_id
        
        except Exception as e:
            logger.error(f"❌ URL validation error: {e}")
            return False, None, None

class TextUtils:
    """Text formatting and processing utilities"""
    
    @staticmethod
    def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
        """Truncate text to specified length"""
        if len(text) <= max_length:
            return text
        return text[:max_length - len(suffix)] + suffix
    
    @staticmethod
    def escape_markdown(text: str) -> str:
        """Escape markdown special characters"""
        escape_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
        for char in escape_chars:
            text = text.replace(char, f'\\{char}')
        return text
    
    @staticmethod
    def format_duration(seconds: int) -> str:
        """Format duration in seconds to human readable format"""
        if seconds < 60:
            return f"{seconds}s"
        elif seconds < 3600:
            minutes = seconds // 60
            seconds = seconds % 60
            return f"{minutes}m {seconds}s"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            seconds = seconds % 60
            return f"{hours}h {minutes}m {seconds}s"
    
    @staticmethod
    def format_progress_bar(progress: float, width: int = 20) -> str:
        """Create a progress bar string"""
        filled = int(progress * width)
        bar = '█' * filled + '░' * (width - filled)
        return f"[{bar}] {progress:.1%}"
    
    @staticmethod
    def clean_filename_from_title(title: str) -> str:
        """Clean title to create a safe filename"""
        # Remove HTML tags
        title = re.sub(r'<[^>]+>', '', title)
        
        # Replace problematic characters
        title = re.sub(r'[<>:"/\\|?*]', '_', title)
        title = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', title)
        
        # Remove extra whitespace
        title = re.sub(r'\s+', ' ', title).strip()
        
        # Limit length
        if len(title) > 80:
            title = title[:80].rsplit(' ', 1)[0]
        
        return title or "download"

class TimeUtils:
    """Time and date utilities"""
    
    @staticmethod
    def get_timestamp() -> str:
        """Get current timestamp string"""
        return datetime.now().strftime("%Y%m%d_%H%M%S")
    
    @staticmethod
    def format_datetime(dt: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
        """Format datetime object"""
        return dt.strftime(format_str)
    
    @staticmethod
    def parse_datetime(dt_str: str, format_str: str = "%Y-%m-%d %H:%M:%S") -> Optional[datetime]:
        """Parse datetime string"""
        try:
            return datetime.strptime(dt_str, format_str)
        except ValueError:
            return None
    
    @staticmethod
    def time_ago(dt: datetime) -> str:
        """Get human readable time ago string"""
        now = datetime.now()
        diff = now - dt
        
        if diff.days > 0:
            return f"{diff.days} day{'s' if diff.days != 1 else ''} ago"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        else:
            return "Just now"
    
    @staticmethod
    def get_video_duration(file_path: str) -> Optional[int]:
        """Get video duration in seconds using ffprobe"""
        try:
            import subprocess
            import json
            
            cmd = [
                'ffprobe', '-v', 'quiet', '-print_format', 'json',
                '-show_format', '-show_streams', file_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                data = json.loads(result.stdout)
                duration = data.get('format', {}).get('duration')
                if duration:
                    return int(float(duration))
            
            return None
        except Exception as e:
            logger.warning(f"Could not get video duration: {e}")
            return None

class ValidationUtils:
    """Validation utilities"""
    
    @staticmethod
    def is_valid_telegram_user_id(user_id: int) -> bool:
        """Check if user ID is valid Telegram user ID"""
        return isinstance(user_id, int) and 1 <= user_id <= 2147483647
    
    @staticmethod
    def is_valid_file_size(size: int, max_size: int = 2 * 1024 * 1024 * 1024) -> bool:
        """Check if file size is within limits (default 2GB)"""
        return 0 < size <= max_size
    
    @staticmethod
    def validate_quality_option(quality: str, available_qualities: List[str]) -> bool:
        """Validate quality option"""
        return quality.lower() in [q.lower() for q in available_qualities]

class AsyncUtils:
    """Async utilities"""
    
    @staticmethod
    async def run_with_timeout(coro, timeout: float):
        """Run coroutine with timeout"""
        try:
            return await asyncio.wait_for(coro, timeout=timeout)
        except asyncio.TimeoutError:
            logger.warning(f"⏰ Operation timed out after {timeout}s")
            raise
    
    @staticmethod
    async def retry_async(
        func,
        max_attempts: int = 3,
        delay: float = 1.0,
        backoff: float = 2.0,
        exceptions: Tuple = (Exception,)
    ):
        """Retry async function with exponential backoff"""
        last_exception = None
        
        for attempt in range(max_attempts):
            try:
                return await func()
            except exceptions as e:
                last_exception = e
                if attempt < max_attempts - 1:
                    wait_time = delay * (backoff ** attempt)
                    logger.warning(f"⚠️ Attempt {attempt + 1} failed, retrying in {wait_time}s: {e}")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"❌ All {max_attempts} attempts failed")
        
        raise last_exception

# Convenience functions
def get_temp_filename(prefix: str = "download", suffix: str = "") -> str:
    """Generate temporary filename"""
    timestamp = TimeUtils.get_timestamp()
    return f"{prefix}_{timestamp}{suffix}"

def format_user_info(user_id: int, username: Optional[str] = None, first_name: Optional[str] = None) -> str:
    """Format user information for logging"""
    parts = [f"ID:{user_id}"]
    if username:
        parts.append(f"@{username}")
    if first_name:
        parts.append(f"({first_name})")
    return " ".join(parts)

def create_progress_message(current: int, total: int, operation: str = "Processing") -> str:
    """Create progress message"""
    if total > 0:
        progress = current / total
        bar = TextUtils.format_progress_bar(progress)
        return f"{operation}... {bar} ({current}/{total})"
    else:
        return f"{operation}... ({current})"