import logging
import logging.handlers
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from config import LOGGING_CONFIG

class ColoredFormatter(logging.Formatter):
    """Colored formatter for console output"""
    
    # Color codes
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
        'RESET': '\033[0m'       # Reset
    }
    
    def format(self, record):
        # Add color to levelname
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{self.COLORS['RESET']}"
        
        # Format the message
        formatted = super().format(record)
        
        # Reset levelname for other formatters
        record.levelname = levelname
        
        return formatted

class BotLogger:
    """Centralized logging configuration for the bot"""
    
    def __init__(self):
        self.log_dir = Path(LOGGING_CONFIG['log_dir'])
        self.log_dir.mkdir(exist_ok=True)
        self._setup_logging()
    
    def _setup_logging(self):
        """Setup logging configuration"""
        # Get root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, LOGGING_CONFIG['level'].upper()))
        
        # Clear existing handlers
        root_logger.handlers.clear()
        
        # Console handler with colors
        if LOGGING_CONFIG.get('console_enabled', True):
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(getattr(logging, LOGGING_CONFIG['console_level'].upper()))
            
            console_formatter = ColoredFormatter(
                fmt='%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s',
                datefmt='%H:%M:%S'
            )
            console_handler.setFormatter(console_formatter)
            root_logger.addHandler(console_handler)
        
        # File handler for general logs
        if LOGGING_CONFIG.get('file_enabled', True):
            file_handler = logging.handlers.RotatingFileHandler(
                filename=self.log_dir / 'bot.log',
                maxBytes=LOGGING_CONFIG.get('max_file_size', 10 * 1024 * 1024),  # 10MB
                backupCount=LOGGING_CONFIG.get('backup_count', 5),
                encoding='utf-8'
            )
            file_handler.setLevel(getattr(logging, LOGGING_CONFIG['file_level'].upper()))
            
            file_formatter = logging.Formatter(
                fmt='%(asctime)s | %(levelname)-8s | %(name)-20s | %(funcName)-15s | %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(file_formatter)
            root_logger.addHandler(file_handler)
        
        # Error file handler
        if LOGGING_CONFIG.get('error_file_enabled', True):
            error_handler = logging.handlers.RotatingFileHandler(
                filename=self.log_dir / 'errors.log',
                maxBytes=LOGGING_CONFIG.get('max_file_size', 10 * 1024 * 1024),
                backupCount=LOGGING_CONFIG.get('backup_count', 5),
                encoding='utf-8'
            )
            error_handler.setLevel(logging.ERROR)
            
            error_formatter = logging.Formatter(
                fmt='%(asctime)s | %(levelname)-8s | %(name)-20s | %(funcName)-15s | %(lineno)d | %(message)s\n%(exc_info)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            error_handler.setFormatter(error_formatter)
            root_logger.addHandler(error_handler)
        
        # Downloads log handler
        if LOGGING_CONFIG.get('downloads_log_enabled', True):
            downloads_handler = logging.handlers.RotatingFileHandler(
                filename=self.log_dir / 'downloads.log',
                maxBytes=LOGGING_CONFIG.get('max_file_size', 10 * 1024 * 1024),
                backupCount=LOGGING_CONFIG.get('backup_count', 5),
                encoding='utf-8'
            )
            downloads_handler.setLevel(logging.INFO)
            
            downloads_formatter = logging.Formatter(
                fmt='%(asctime)s | %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            downloads_handler.setFormatter(downloads_formatter)
            
            # Create downloads logger
            downloads_logger = logging.getLogger('downloads')
            downloads_logger.addHandler(downloads_handler)
            downloads_logger.setLevel(logging.INFO)
            downloads_logger.propagate = False
        
        # Sessions log handler
        if LOGGING_CONFIG.get('sessions_log_enabled', True):
            sessions_handler = logging.handlers.RotatingFileHandler(
                filename=self.log_dir / 'sessions.log',
                maxBytes=LOGGING_CONFIG.get('max_file_size', 10 * 1024 * 1024),
                backupCount=LOGGING_CONFIG.get('backup_count', 5),
                encoding='utf-8'
            )
            sessions_handler.setLevel(logging.INFO)
            
            sessions_formatter = logging.Formatter(
                fmt='%(asctime)s | %(levelname)-8s | %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            sessions_handler.setFormatter(sessions_formatter)
            
            # Create sessions logger
            sessions_logger = logging.getLogger('sessions')
            sessions_logger.addHandler(sessions_handler)
            sessions_logger.setLevel(logging.INFO)
            sessions_logger.propagate = False
        
        # Suppress noisy third-party loggers
        self._configure_third_party_loggers()
        
        logging.info("✅ Logging system initialized")
    
    def _configure_third_party_loggers(self):
        """Configure third-party library loggers"""
        # Telethon
        telethon_logger = logging.getLogger('telethon')
        telethon_logger.setLevel(logging.WARNING)
        
        # yt-dlp
        ytdlp_logger = logging.getLogger('yt_dlp')
        ytdlp_logger.setLevel(logging.WARNING)
        
        # aiohttp
        aiohttp_logger = logging.getLogger('aiohttp')
        aiohttp_logger.setLevel(logging.WARNING)
        
        # urllib3
        urllib3_logger = logging.getLogger('urllib3')
        urllib3_logger.setLevel(logging.WARNING)
    
    def get_downloads_logger(self) -> logging.Logger:
        """Get downloads logger"""
        return logging.getLogger('downloads')
    
    def get_sessions_logger(self) -> logging.Logger:
        """Get sessions logger"""
        return logging.getLogger('sessions')
    
    def log_download(
        self,
        user_id: int,
        username: Optional[str],
        url: str,
        platform: str,
        media_type: str,
        quality: str,
        file_size: Optional[int],
        session_used: str,
        status: str,
        error: Optional[str] = None
    ):
        """Log download activity"""
        downloads_logger = self.get_downloads_logger()
        
        log_data = {
            'user_id': user_id,
            'username': username or 'Unknown',
            'url': url,
            'platform': platform,
            'media_type': media_type,
            'quality': quality,
            'file_size': file_size or 0,
            'session_used': session_used,
            'status': status
        }
        
        if error:
            log_data['error'] = error
        
        # Format log message
        message_parts = []
        for key, value in log_data.items():
            message_parts.append(f"{key}={value}")
        
        message = " | ".join(message_parts)
        
        if status == 'success':
            downloads_logger.info(f"✅ DOWNLOAD_SUCCESS | {message}")
        elif status == 'failed':
            downloads_logger.error(f"❌ DOWNLOAD_FAILED | {message}")
        else:
            downloads_logger.info(f"📥 DOWNLOAD_{status.upper()} | {message}")
    
    def log_session_activity(
        self,
        session_name: str,
        action: str,
        details: Optional[str] = None,
        user_id: Optional[int] = None
    ):
        """Log session activity"""
        sessions_logger = self.get_sessions_logger()
        
        message_parts = [f"session={session_name}", f"action={action}"]
        
        if user_id:
            message_parts.append(f"user_id={user_id}")
        
        if details:
            message_parts.append(f"details={details}")
        
        message = " | ".join(message_parts)
        
        if action in ['connected', 'authorized', 'success']:
            sessions_logger.info(f"✅ SESSION_{action.upper()} | {message}")
        elif action in ['disconnected', 'failed', 'error']:
            sessions_logger.warning(f"⚠️ SESSION_{action.upper()} | {message}")
        else:
            sessions_logger.info(f"📱 SESSION_{action.upper()} | {message}")
    
    def cleanup_old_logs(self, days: int = 30):
        """Clean up old log files"""
        try:
            import time
            
            cutoff_time = time.time() - (days * 24 * 60 * 60)
            cleaned_count = 0
            
            for log_file in self.log_dir.glob('*.log*'):
                if log_file.stat().st_mtime < cutoff_time:
                    log_file.unlink()
                    cleaned_count += 1
            
            if cleaned_count > 0:
                logging.info(f"🧹 Cleaned up {cleaned_count} old log files")
        
        except Exception as e:
            logging.error(f"❌ Error cleaning up logs: {e}")
    
    def get_log_stats(self) -> dict:
        """Get logging statistics"""
        try:
            stats = {
                'log_dir': str(self.log_dir),
                'log_files': [],
                'total_size': 0
            }
            
            for log_file in self.log_dir.glob('*.log*'):
                file_stat = log_file.stat()
                file_info = {
                    'name': log_file.name,
                    'size': file_stat.st_size,
                    'modified': datetime.fromtimestamp(file_stat.st_mtime).isoformat()
                }
                stats['log_files'].append(file_info)
                stats['total_size'] += file_stat.st_size
            
            return stats
        
        except Exception as e:
            logging.error(f"❌ Error getting log stats: {e}")
            return {}

# Global logger instance
_bot_logger = None

def setup_logging() -> BotLogger:
    """Setup and return global logger instance"""
    global _bot_logger
    if _bot_logger is None:
        _bot_logger = BotLogger()
    return _bot_logger

def get_logger() -> BotLogger:
    """Get global logger instance"""
    global _bot_logger
    if _bot_logger is None:
        _bot_logger = setup_logging()
    return _bot_logger