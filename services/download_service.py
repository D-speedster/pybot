import asyncio
import logging
import os
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, Callable
import tempfile

# جایگزینی yt-dlp با pytube
from pytube import YouTube, Stream
from pytube.exceptions import PytubeError

# برای پشتیبانی از انتقال، yt-dlp را هم نگه می‌داریم
import yt_dlp

from config import DOWNLOAD_CONFIG, QUALITY_OPTIONS
from services.session_manager import SessionManager
from utils.helpers import FileUtils, TextUtils

logger = logging.getLogger(__name__)

class ProgressHook:
    """Progress hook for yt-dlp downloads"""
    
    def __init__(self, callback: Optional[Callable] = None):
        self.callback = callback
        self.last_update = 0
    
    def __call__(self, d):
        if self.callback:
            current_time = datetime.now().timestamp()
            
            # Throttle updates to avoid spam
            if current_time - self.last_update < 1:  # Update every 1 second
                return
            
            self.last_update = current_time
            
            if d['status'] == 'downloading':
                percent = d.get('_percent_str', '0%').replace('%', '')
                try:
                    percent_float = float(percent)
                except (ValueError, TypeError):
                    percent_float = 0
                
                progress_data = {
                    'status': 'downloading',
                    'percent': int(percent_float),
                    'speed': d.get('_speed_str', 'Unknown'),
                    'eta': d.get('_eta_str', 'Unknown')
                }
                
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        asyncio.create_task(self._safe_callback(progress_data))
                    else:
                        loop.run_until_complete(self._safe_callback(progress_data))
                except Exception as e:
                    logger.error(f"Error in progress callback: {e}")
    
    async def _safe_callback(self, data):
        try:
            await self.callback(data)
        except Exception as e:
            logger.error(f"Error in callback: {e}")


class PytubeProgressCallback:
    """Progress callback for pytube downloads"""
    
    def __init__(self, callback: Optional[Callable] = None):
        self.callback = callback
        self.last_update = 0
        self.filesize = 0
    
    def set_filesize(self, filesize: int):
        self.filesize = filesize
    
    def __call__(self, chunk, file_handle, bytes_remaining):
        if self.callback and self.filesize > 0:
            current_time = datetime.now().timestamp()
            
            # Throttle updates to avoid spam
            if current_time - self.last_update < 1:  # Update every 1 second
                return
            
            self.last_update = current_time
            
            bytes_downloaded = self.filesize - bytes_remaining
            percent = int((bytes_downloaded / self.filesize) * 100)
            
            progress_data = {
                'status': 'downloading',
                'percent': percent,
                'speed': 'Unknown',  # pytube doesn't provide speed info
                'eta': 'Unknown'     # pytube doesn't provide ETA info
            }
            
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.create_task(self._safe_callback(progress_data))
                else:
                    loop.run_until_complete(self._safe_callback(progress_data))
            except Exception as e:
                logger.error(f"Error in progress callback: {e}")
    
    async def _safe_callback(self, data):
        try:
            await self.callback(data)
        except Exception as e:
            logger.error(f"Error in callback: {e}")


class PytubeDownloader:
    """YouTube downloader using pytube library"""
    
    def __init__(self):
        self.temp_dir = DOWNLOAD_CONFIG['temp_dir']
    
    async def download(self, url: str, quality: str, progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """Download a YouTube video using pytube"""
        temp_download_dir = Path(tempfile.mkdtemp(dir=self.temp_dir))
        
        try:
            # Create progress callback
            progress_handler = PytubeProgressCallback(progress_callback)
            
            # Initialize YouTube object
            yt = YouTube(url, on_progress_callback=progress_handler)
            
            # Get stream based on quality
            stream = self._get_stream_by_quality(yt, quality)
            if not stream:
                return {'success': False, 'error': f'No stream available for quality: {quality}'}
            
            # Set filesize for progress calculation
            progress_handler.set_filesize(stream.filesize)
            
            # Download the video
            file_path = Path(stream.download(output_path=str(temp_download_dir)))
            
            if not file_path.exists():
                return {'success': False, 'error': 'Download failed: File not found after download'}
            
            file_size = file_path.stat().st_size
            
            # Get video info
            info = {
                'title': yt.title,
                'uploader': yt.author,
                'duration': yt.length,
                'width': stream.resolution.split('x')[0] if stream.resolution else 0,
                'height': stream.resolution.split('x')[1] if stream.resolution else 0
            }
            
            media_type = 'video' if stream.includes_video_track else 'audio'
            
            return {
                'success': True,
                'file_path': str(file_path),
                'file_size': file_size,
                'media_type': media_type,
                'title': info.get('title', 'Unknown'),
                'uploader': info.get('uploader', 'Unknown'),
                'duration': info.get('duration', 0),
                'width': info.get('width', 0),
                'height': info.get('height', 0)
            }
        
        except PytubeError as e:
            logger.error(f"Pytube download error: {e}")
            return {'success': False, 'error': f'Download failed: {str(e)}'}
        
        except Exception as e:
            logger.error(f"Download error: {e}")
            return {'success': False, 'error': str(e)}
        
        finally:
            # Schedule cleanup
            asyncio.create_task(self._cleanup_temp_dir(temp_download_dir))
    
    def _get_stream_by_quality(self, yt: YouTube, quality: str) -> Optional[Stream]:
        """Get stream based on quality setting"""
        try:
            if quality == 'best':
                return yt.streams.get_highest_resolution()
            elif quality == 'worst':
                return yt.streams.get_lowest_resolution()
            elif 'audio' in quality:
                return yt.streams.get_audio_only()
            elif '720' in quality:
                return yt.streams.filter(res='720p').first() or yt.streams.get_highest_resolution()
            elif '480' in quality:
                return yt.streams.filter(res='480p').first() or yt.streams.get_highest_resolution()
            elif '360' in quality:
                return yt.streams.filter(res='360p').first() or yt.streams.get_highest_resolution()
            else:
                return yt.streams.get_highest_resolution()
        except Exception as e:
            logger.error(f"Error getting stream: {e}")
            return yt.streams.get_highest_resolution()
    
    async def _cleanup_temp_dir(self, temp_dir: Path):
        """Clean up temporary directory after download"""
        try:
            # Wait for a while to ensure file operations are complete
            await asyncio.sleep(60)
            if temp_dir.exists():
                shutil.rmtree(temp_dir, ignore_errors=True)
        except Exception as e:
            logger.error(f"Error cleaning up temp dir: {e}")


class DownloadService:
    """Service for downloading media from various platforms"""
    
    def __init__(self, session_manager: SessionManager):
        self.session_manager = session_manager
        self.temp_dir = Path(DOWNLOAD_CONFIG['temp_dir'])
        self.temp_dir.mkdir(exist_ok=True, parents=True)
        
        # Initialize pytube downloader
        self.pytube_downloader = PytubeDownloader()
        
        # Active downloads tracking
        self.active_downloads: Dict[str, Dict[str, Any]] = {}
        
        # Schedule cleanup of old temp files
        asyncio.create_task(self._cleanup_old_files())
    
    async def download_and_upload(
        self,
        url: str,
        platform: str,
        quality: str,
        progress_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """Download media and return file information"""
        
        download_id = f"{platform}_{hash(url)}_{datetime.now().timestamp()}"
        
        try:
            # Check if already downloading
            if download_id in self.active_downloads:
                return {'success': False, 'error': 'Already downloading'}
            
            # Mark as active
            self.active_downloads[download_id] = {
                'url': url,
                'platform': platform,
                'quality': quality,
                'started_at': datetime.now()
            }
            
            # Create progress hook
            progress_hook = ProgressHook(progress_callback)
            
            # Download the media
            result = await self._download_media(
                url, platform, quality, progress_hook
            )
            
            if result['success']:
                # Notify upload start
                if progress_callback:
                    await progress_callback({'status': 'uploading'})
            
            return result
            
        except Exception as e:
            logger.error(f"Download service error: {e}")
            return {'success': False, 'error': str(e)}
        
        finally:
            # Remove from active downloads
            if download_id in self.active_downloads:
                del self.active_downloads[download_id]
    
    def _get_ydl_opts(self, platform: str, quality: str, temp_download_dir: Path, progress_hook: ProgressHook) -> Dict[str, Any]:
        """Get yt-dlp options based on platform and quality"""
        
        # Base options
        ydl_opts = {
            'format': QUALITY_OPTIONS.get(quality, 'best'),
            'outtmpl': str(temp_download_dir / '%(title)s.%(ext)s'),
            'progress_hooks': [progress_hook],
            'quiet': True,
            'no_warnings': True,
            'ignoreerrors': True,
            'socket_timeout': 60,  # Increased timeout for better reliability
            'source_address': '0.0.0.0',  # Use any available network interface
            'force_ipv4': True,  # Force IPv4 to avoid IPv6 issues
            'geo_bypass': True,  # Bypass geo-restrictions
            'geo_bypass_country': 'US',
            'nocheckcertificate': True,  # Skip HTTPS certificate validation
            'simulate_browser': True,  # Simulate a browser to avoid detection
        }
        
        # Add cookies for YouTube authentication
        cookies_file = Path('cookies.txt')
        if cookies_file.exists():
            ydl_opts['cookiefile'] = str(cookies_file)
            logger.info(f"Using cookies file: {cookies_file}")
        
        # Platform-specific options
        if platform == 'youtube':
            ydl_opts.update({
                'writethumbnail': False,  # Don't download thumbnail
                'writesubtitles': False,  # Don't download subtitles
                'subtitleslangs': ['en'],  # English subtitles only
                'skip_download': False,  # Download the video
                'postprocessors': [],  # No post-processing
            })
            
            # Audio-only options
            if 'audio' in quality:
                ydl_opts.update({
                    'format': 'bestaudio/best',
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '192',
                    }],
                })
        
        # Instagram options
        elif platform == 'instagram':
            ydl_opts.update({
                'extract_flat': False,
                'dump_single_json': False,
                'force_generic_extractor': False,
            })
        
        return ydl_opts
    
    async def _download_media(
        self,
        url: str,
        platform: str,
        quality: str,
        progress_hook: ProgressHook
    ) -> Dict[str, Any]:
        """Download media using appropriate downloader based on platform"""
        
        # Use yt-dlp for all platforms including YouTube
        # This is more reliable than pytube which often gives HTTP 400 errors
        logger.info(f"Using yt-dlp downloader for URL: {url}")
        
        temp_download_dir = Path(tempfile.mkdtemp(dir=self.temp_dir))
        
        try:
            # Configure yt-dlp options
            ydl_opts = self._get_ydl_opts(platform, quality, temp_download_dir, progress_hook)
            
            # Download the media
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: ydl.extract_info(url, download=True)
                )
                
                if not info:
                    return {'success': False, 'error': 'Could not extract info'}
                
                # Find the downloaded file
                downloaded_files = list(temp_download_dir.glob('*'))
                if not downloaded_files:
                    return {'success': False, 'error': 'No files found after download'}
                
                file_path = downloaded_files[0]
                file_size = file_path.stat().st_size
                
                # Determine media type
                media_type = self._get_media_type(file_path, info)
                
                return {
                    'success': True,
                    'file_path': str(file_path),
                    'file_size': file_size,
                    'media_type': media_type,
                    'title': info.get('title', 'Unknown'),
                    'uploader': info.get('uploader', 'Unknown'),
                    'duration': info.get('duration', 0),
                    'width': info.get('width', 0),
                    'height': info.get('height', 0)
                }
                
        except Exception as e:
            logger.error(f"Download error: {e}")
            return {'success': False, 'error': str(e)}
        
        finally:
            # Schedule cleanup
            asyncio.create_task(self._cleanup_temp_dir(temp_download_dir))
        
        # All platforms are now handled by yt-dlp in the code above
    
    async def _get_ydl_options(self, platform: str, quality: str, output_dir: Path, progress_hook: ProgressHook) -> Dict[str, Any]:
        """Get yt-dlp options based on platform and quality"""
        
        # Base options
        ydl_opts = {
            'format': QUALITY_OPTIONS.get(quality, 'best'),
            'outtmpl': str(output_dir / '%(title)s.%(ext)s'),
            'progress_hooks': [progress_hook],
            'quiet': True,
            'no_warnings': True,
            'ignoreerrors': True,
            'socket_timeout': 60,  # Increased timeout for better reliability
            'source_address': '0.0.0.0',  # Use any available network interface
            'force_ipv4': True,  # Force IPv4 to avoid IPv6 issues
            'geo_bypass': True,  # Bypass geo-restrictions
            'geo_bypass_country': 'US',
            'nocheckcertificate': True,  # Skip HTTPS certificate validation
            'simulate_browser': True,  # Simulate a browser to avoid detection
        }
        
        # Add cookies for YouTube authentication
        cookies_file = Path('cookies.txt')
        if cookies_file.exists():
            ydl_opts['cookiefile'] = str(cookies_file)
            logger.info(f"Using cookies file: {cookies_file}")
        
        # Platform-specific options
        if platform == 'youtube':
            ydl_opts.update({
                'writethumbnail': False,  # Don't download thumbnail
                'writesubtitles': False,  # Don't download subtitles
                'subtitleslangs': ['en'],  # English subtitles only
                'skip_download': False,  # Download the video
                'postprocessors': [],  # No post-processing
            })
            
            # Audio-only options
            if 'audio' in quality:
                ydl_opts.update({
                    'format': 'bestaudio/best',
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '192',
                    }],
                })
        
        # Instagram options
        elif platform == 'instagram':
            ydl_opts.update({
                'extract_flat': False,
                'dump_single_json': False,
                'force_generic_extractor': False,
            })
        
        return ydl_opts
    
    def _get_platform(self, url: str) -> str:
        """Determine platform from URL"""
        if 'youtube.com' in url or 'youtu.be' in url:
            return 'youtube'
        elif 'instagram.com' in url:
            return 'instagram'
        elif 'tiktok.com' in url:
            return 'tiktok'
        elif 'twitter.com' in url or 'x.com' in url:
            return 'twitter'
        elif 'facebook.com' in url or 'fb.com' in url:
            return 'facebook'
        else:
            return 'generic'
    
    def _get_media_type(self, file_path: Path, info: Dict[str, Any]) -> str:
        """Determine media type from file extension and info"""
        ext = file_path.suffix.lower()
        
        # Check if audio-only based on extension
        if ext in ['.mp3', '.m4a', '.wav', '.ogg', '.opus']:
            return 'audio'
        
        # Check if audio-only based on info
        if info.get('vcodec') == 'none' or info.get('acodec') == 'none':
            return 'audio'
        
        # Default to video
        return 'video'
    
    async def get_download_info(self, url: str) -> Dict[str, Any]:
        """Get detailed download information including available formats"""
        try:
            # Determine platform
            platform = self._get_platform(url)
            
            # Use yt-dlp for all platforms including YouTube
            logger.info(f"Using yt-dlp to extract info for URL: {url}")
            
            # Use the _get_ydl_opts method to get options
            temp_dir = Path(tempfile.mkdtemp(dir=self.temp_dir))
            progress_hook = ProgressHook(None)
            
            try:
                # Get yt-dlp options
                ydl_opts = self._get_ydl_opts(platform, 'best', temp_dir, progress_hook)
                
                # Add additional options for info extraction
                ydl_opts.update({
                    'skip_download': True,
                    'format': 'best',
                    'retries': 10,
                    'fragment_retries': 10,
                })
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = await asyncio.get_event_loop().run_in_executor(
                        None, lambda: ydl.extract_info(url, download=False)
                    )
                    
                    if not info:
                        # Try with a different user agent if first attempt fails
                        ydl_opts['user_agent'] = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36'
                        if 'http_headers' in ydl_opts:
                            ydl_opts['http_headers']['User-Agent'] = ydl_opts['user_agent']
                        
                        with yt_dlp.YoutubeDL(ydl_opts) as ydl2:
                            info = await asyncio.get_event_loop().run_in_executor(
                                None, lambda: ydl2.extract_info(url, download=False)
                            )
                    
                    if not info:
                        return {'success': False, 'error': 'Could not extract info'}
                    
                    return {
                        'success': True,
                        'title': info.get('title', 'Unknown'),
                        'uploader': info.get('uploader', 'Unknown'),
                        'duration': info.get('duration', 0),
                        'thumbnail': info.get('thumbnail', ''),
                        'platform': platform,
                        'formats': info.get('formats', []),
                        'filesize': info.get('filesize') or info.get('filesize_approx') or 0
                    }
            except yt_dlp.utils.DownloadError as e:
                logger.error(f"yt-dlp download error: {e}")
                return {'success': False, 'error': f"Download error: {str(e)}"}
            except yt_dlp.utils.ExtractorError as e:
                logger.error(f"yt-dlp extractor error: {e}")
                return {'success': False, 'error': f"Extraction error: {str(e)}"}
            except Exception as e:
                logger.error(f"yt-dlp unexpected error: {e}")
                return {'success': False, 'error': f"Unexpected error: {str(e)}"}
            finally:
                # Schedule cleanup
                asyncio.create_task(self._cleanup_temp_dir(temp_dir))
                
        except Exception as e:
            logger.error(f"Info extraction error: {e}")
            return {'success': False, 'error': str(e)}
    
    async def extract_info(self, url: str) -> Dict[str, Any]:
        """Extract information about a video without downloading"""
        try:
            # Determine platform
            platform = self._get_platform(url)
            
            # Use pytube for YouTube
            if platform == 'youtube':
                try:
                    yt = YouTube(url)
                    stream = yt.streams.get_highest_resolution()
                    
                    return {
                        'success': True,
                        'title': yt.title,
                        'uploader': yt.author,
                        'duration': yt.length,
                        'thumbnail': yt.thumbnail_url,
                        'platform': platform,
                        'filesize': stream.filesize if stream else 0
                    }
                except PytubeError as e:
                    logger.error(f"Pytube info extraction error: {e}")
                    # Fall back to yt-dlp if pytube fails
            
            # For other platforms or as fallback, use yt-dlp
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'skip_download': True,
                'youtube_include_dash_manifest': False,
                'nocheckcertificate': True,
                'ignoreerrors': True,
                'user_agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1',
                'proxy': None,  # Disable proxy
                'socket_timeout': 60,  # Increased timeout for better reliability with DNS issues
                'source_address': '0.0.0.0',  # Use any available network interface
                'force_ipv4': True,  # Force IPv4 to avoid IPv6 issues
                'geo_bypass': True,  # Bypass geo-restrictions
                'geo_bypass_country': 'US',
                'cookiefile': None,  # No cookies
                'extractor_args': {'youtube': {'player_client': ['android']}},
                'timeout': 60  # Increased timeout for info extraction to handle DNS issues
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: ydl.extract_info(url, download=False)
                )
                
                if not info:
                    return {'success': False, 'error': 'Could not extract info'}
                
                return {
                    'success': True,
                    'title': info.get('title', 'Unknown'),
                    'uploader': info.get('uploader', 'Unknown'),
                    'duration': info.get('duration', 0),
                    'thumbnail': info.get('thumbnail', ''),
                    'platform': platform,
                    'filesize': info.get('filesize') or info.get('filesize_approx') or 0
                }
                
        except Exception as e:
            logger.error(f"Info extraction error: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _cleanup_temp_dir(self, temp_dir: Path):
        """Clean up temporary directory after download"""
        try:
            # Wait for a while to ensure file operations are complete
            await asyncio.sleep(60)
            if temp_dir.exists():
                shutil.rmtree(temp_dir, ignore_errors=True)
        except Exception as e:
            logger.error(f"Error cleaning up temp dir: {e}")
    
    async def _cleanup_old_files(self):
        """Clean up old temporary files"""
        try:
            while True:
                # Run cleanup every hour
                await asyncio.sleep(3600)
                
                # Find and delete files older than 24 hours
                now = datetime.now()
                cutoff = now - timedelta(hours=24)
                
                for item in self.temp_dir.glob('*'):
                    try:
                        # Get item modification time
                        mtime = datetime.fromtimestamp(item.stat().st_mtime)
                        
                        # Delete if older than cutoff
                        if mtime < cutoff:
                            if item.is_dir():
                                shutil.rmtree(item, ignore_errors=True)
                            else:
                                item.unlink()
                            
                            logger.info(f"Cleaned up old temp file: {item}")
                    except Exception as e:
                        logger.error(f"Error cleaning up {item}: {e}")
        
        except Exception as e:
            logger.error(f"Error in cleanup task: {e}")