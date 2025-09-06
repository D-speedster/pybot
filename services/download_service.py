import asyncio
import logging
import os
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, Callable
import tempfile

# استفاده از pytubefix برای دانلود یوتیوب
from pytubefix import YouTube, Stream
from pytubefix.exceptions import VideoUnavailable, ExtractError, RegexMatchError

from config import DOWNLOAD_CONFIG, QUALITY_OPTIONS
from services.session_manager import SessionManager
from utils.helpers import FileUtils, TextUtils

logger = logging.getLogger(__name__)

class ProgressHook:
    """Progress hook for pytube downloads"""
    
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
    
    def _get_stream_by_quality(self, yt: YouTube, quality: str) -> Optional[Stream]:
        """Get the best stream based on quality preference"""
        try:
            if quality == 'highest':
                return yt.streams.get_highest_resolution()
            elif quality == 'lowest':
                return yt.streams.get_lowest_resolution()
            elif quality == 'audio':
                return yt.streams.filter(only_audio=True).first()
            elif quality in ['720p', '480p', '360p', '240p', '144p']:
                # Try to get specific resolution
                stream = yt.streams.filter(res=quality, file_extension='mp4').first()
                if stream:
                    return stream
                # Fallback to best available
                return yt.streams.get_highest_resolution()
            else:
                return yt.streams.get_highest_resolution()
        except Exception as e:
            logger.error(f"Error getting stream: {e}")
            return yt.streams.first()  # Return any available stream as fallback
    
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
                'width': int(stream.resolution.split('x')[0]) if stream.resolution else 0,
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
        
        except Exception as e:
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
    

    
    async def _download_media(
        self,
        url: str,
        platform: str,
        quality: str,
        progress_hook: ProgressHook
    ) -> Dict[str, Any]:
        """Download media using pytube for YouTube"""
        
        if platform != 'youtube':
            return {'success': False, 'error': f'Platform {platform} not supported. Only YouTube is supported.'}
        
        logger.info(f"Using pytube downloader for URL: {url}")
        
        temp_download_dir = Path(tempfile.mkdtemp(dir=self.temp_dir))
        
        try:
            # Create progress callback
            progress_handler = PytubeProgressCallback(progress_hook.callback if hasattr(progress_hook, 'callback') else None)
            
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
            
            # Determine media type
            media_type = 'video' if stream.includes_video_track else 'audio'
            
            return {
                'success': True,
                'file_path': str(file_path),
                'file_size': file_size,
                'media_type': media_type,
                'title': yt.title,
                'uploader': yt.author,
                'duration': yt.length,
                'width': int(stream.resolution.split('x')[0]) if stream.resolution else 0,
                'height': int(stream.resolution.split('x')[1]) if stream.resolution else 0
            }
                
        except Exception as e:
            logger.error(f"Pytube error: {e}")
            return {'success': False, 'error': f'Pytube error: {str(e)}'}
        except Exception as e:
            logger.error(f"Download error: {e}")
            return {'success': False, 'error': str(e)}
        
        finally:
            # Schedule cleanup
            asyncio.create_task(self._cleanup_temp_dir(temp_download_dir))
    
    def _get_stream_by_quality(self, yt: YouTube, quality: str) -> Optional[Stream]:
        """Get the best stream based on quality preference"""
        try:
            if quality == 'highest':
                return yt.streams.get_highest_resolution()
            elif quality == 'lowest':
                return yt.streams.get_lowest_resolution()
            elif quality == 'audio':
                return yt.streams.filter(only_audio=True).first()
            elif quality in ['720p', '480p', '360p', '240p', '144p']:
                # Try to get specific resolution
                stream = yt.streams.filter(res=quality, file_extension='mp4').first()
                if stream:
                    return stream
                # Fallback to best available
                return yt.streams.get_highest_resolution()
            else:
                return yt.streams.get_highest_resolution()
        except Exception as e:
            logger.error(f"Error getting stream: {e}")
            return yt.streams.first()  # Return any available stream as fallback
    

    
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
        """Get detailed download information using pytube"""
        try:
            # Determine platform
            platform = self._get_platform(url)
            
            if platform != 'youtube':
                return {'success': False, 'error': f'Platform {platform} not supported. Only YouTube is supported.'}
            
            logger.info(f"Using pytube to extract info for URL: {url}")
            
            try:
                # Initialize YouTube object
                yt = YouTube(url)
                
                # Get available streams
                streams = yt.streams.all()
                formats = []
                
                for stream in streams:
                    format_info = {
                        'format_id': stream.itag,
                        'ext': stream.mime_type.split('/')[-1] if stream.mime_type else 'mp4',
                        'resolution': stream.resolution,
                        'fps': stream.fps,
                        'filesize': stream.filesize,
                        'abr': stream.abr,
                        'vcodec': stream.video_codec,
                        'acodec': stream.audio_codec,
                        'format_note': f"{stream.type} - {stream.mime_type}"
                    }
                    formats.append(format_info)
                
                return {
                    'success': True,
                    'title': yt.title,
                    'uploader': yt.author,
                    'duration': yt.length,
                    'thumbnail': yt.thumbnail_url,
                    'platform': platform,
                    'formats': formats,
                    'filesize': yt.streams.get_highest_resolution().filesize if yt.streams.get_highest_resolution() else 0
                }
                
            except Exception as e:
                logger.error(f"Pytube error: {e}")
                return {'success': False, 'error': f"Pytube error: {str(e)}"}
            except Exception as e:
                logger.error(f"Unexpected error during info extraction: {e}")
                return {'success': False, 'error': f"Unexpected error: {str(e)}"}
            
        except Exception as e:
            logger.error(f"Error getting download info: {e}")
            return {'success': False, 'error': str(e)}
    
    async def extract_info(self, url: str) -> Dict[str, Any]:
        """Extract information about a video without downloading"""
        try:
            # Determine platform
            platform = self._get_platform(url)
            
            if platform != 'youtube':
                return {'success': False, 'error': f'Platform {platform} not supported. Only YouTube is supported.'}
            
            # Use pytube for YouTube
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
            except Exception as e:
                logger.error(f"Pytube info extraction error: {e}")
                return {'success': False, 'error': f'Pytube error: {str(e)}'}
                
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