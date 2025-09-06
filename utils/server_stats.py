import time
import socket
import platform
import psutil
import logging
import subprocess
import asyncio
from typing import Dict, Any, Tuple

logger = logging.getLogger(__name__)

class ServerStats:
    """Class for monitoring server statistics including ping and performance"""
    
    @staticmethod
    async def get_ping(host: str = '8.8.8.8', count: int = 4) -> Dict[str, Any]:
        """Get ping statistics to a host (default: Google DNS)"""
        try:
            if platform.system().lower() == 'windows':
                # Windows ping command
                cmd = ['ping', '-n', str(count), host]
            else:
                # Linux/Unix ping command
                cmd = ['ping', '-c', str(count), host]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            output = stdout.decode('utf-8', errors='ignore')
            
            # Parse ping results
            if platform.system().lower() == 'windows':
                # Parse Windows ping output
                try:
                    # Look for lines containing time information
                    time_lines = [line for line in output.split('\n') if 'time=' in line or 'time<' in line]
                    if time_lines:
                        # Extract all ping times
                        ping_times = []
                        for line in time_lines:
                            if 'time=' in line:
                                time_part = line.split('time=')[1].split('ms')[0]
                                ping_times.append(float(time_part))
                            elif 'time<' in line:
                                time_part = line.split('time<')[1].split('ms')[0]
                                ping_times.append(float(time_part))
                        
                        if ping_times:
                            avg_ms = sum(ping_times) / len(ping_times)
                        else:
                            avg_ms = 999
                    else:
                        # Fallback: look for Average line
                        avg_lines = [line for line in output.split('\n') if 'Average' in line or 'میانگین' in line]
                        if avg_lines:
                            avg_line = avg_lines[0]
                            if '=' in avg_line:
                                avg_ms = float(avg_line.split('=')[1].strip().replace('ms', '').strip())
                            else:
                                avg_ms = 999
                        else:
                            avg_ms = 999
                except (IndexError, ValueError, AttributeError):
                    avg_ms = 999  # Error value
            else:
                # Parse Linux/Unix ping output
                try:
                    avg_line = [line for line in output.split('\n') if 'avg' in line][0]
                    avg_ms = float(avg_line.split('/')[4])
                except (IndexError, ValueError):
                    avg_ms = 999  # Error value
            
            # Determine status based on ping
            if avg_ms < 50:
                status = 'عالی'
                emoji = '🟢'
            elif avg_ms < 100:
                status = 'خوب'
                emoji = '🟡'
            elif avg_ms < 200:
                status = 'نرمال'
                emoji = '🟠'
            else:
                status = 'ضعیف'
                emoji = '🔴'
            
            return {
                'ping_ms': avg_ms,
                'status': status,
                'emoji': emoji,
                'host': host,
                'success': True
            }
            
        except Exception as e:
            logger.error(f"Error getting ping stats: {e}")
            return {
                'ping_ms': 999,
                'status': 'خطا',
                'emoji': '⚠️',
                'host': host,
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    async def get_server_stats() -> Dict[str, Any]:
        """Get comprehensive server statistics"""
        try:
            # Get system info
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Get network stats
            net_io = psutil.net_io_counters()
            
            # Get uptime
            uptime = time.time() - psutil.boot_time()
            days, remainder = divmod(uptime, 86400)
            hours, remainder = divmod(remainder, 3600)
            minutes, seconds = divmod(remainder, 60)
            
            # Format uptime string
            uptime_str = f"{int(days)}d {int(hours)}h {int(minutes)}m"
            
            # Get ping stats
            ping_stats = await ServerStats.get_ping()
            
            return {
                'cpu': {
                    'percent': cpu_percent,
                    'cores': psutil.cpu_count(logical=True)
                },
                'memory': {
                    'total': memory.total,
                    'available': memory.available,
                    'percent': memory.percent,
                    'used': memory.used,
                    'free': memory.free
                },
                'disk': {
                    'total': disk.total,
                    'used': disk.used,
                    'free': disk.free,
                    'percent': disk.percent
                },
                'network': {
                    'bytes_sent': net_io.bytes_sent,
                    'bytes_recv': net_io.bytes_recv,
                    'packets_sent': net_io.packets_sent,
                    'packets_recv': net_io.packets_recv
                },
                'system': {
                    'platform': platform.system(),
                    'release': platform.release(),
                    'version': platform.version(),
                    'hostname': socket.gethostname(),
                    'uptime': uptime_str
                },
                'ping': ping_stats
            }
        except Exception as e:
            logger.error(f"Error getting server stats: {e}")
            return {
                'error': str(e),
                'success': False
            }
    
    @staticmethod
    def format_bytes(bytes_value: int) -> str:
        """Format bytes to human-readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_value < 1024:
                return f"{bytes_value:.2f} {unit}"
            bytes_value /= 1024
        return f"{bytes_value:.2f} PB"
    
    @staticmethod
    async def format_server_stats_message(stats: Dict[str, Any], short_format: bool = False) -> str:
        """Format server stats into a readable message
        
        Args:
            stats: Server statistics dictionary
            short_format: If True, returns a shorter version of the stats
        """
        if 'error' in stats and stats.get('success') is False:
            return f"⚠️ خطا در دریافت آمار سرور: {stats['error']}"
        
        ping = stats.get('ping', {})
        cpu = stats.get('cpu', {})
        memory = stats.get('memory', {})
        disk = stats.get('disk', {})
        system = stats.get('system', {})
        network = stats.get('network', {})
        
        if short_format:
            # Short format for inline display
            message = f"{ping.get('emoji', '⚠️')} پینگ: {ping.get('ping_ms', 0):.1f}ms ({ping.get('status', 'نامشخص')})\n"
            message += f"💻 CPU: {cpu.get('percent', 0)}% | 🧠 RAM: {memory.get('percent', 0)}%\n"
            message += f"💾 دیسک: {disk.get('percent', 0)}% | ⏱️ آپتایم: {system.get('uptime', 'نامشخص')}"
            return message
        else:
            # Full detailed format
            message = "📊 **آمار سرور** 📊\n\n"
            
            # Ping status
            message += f"**پینگ سرور:** {ping.get('emoji', '⚠️')} {ping.get('status', 'نامشخص')} ({ping.get('ping_ms', 0):.1f} ms)\n\n"
            
            # System info
            message += f"**سیستم:** {system.get('platform', 'نامشخص')} {system.get('release', '')}\n"
            message += f"**زمان روشن بودن:** {system.get('uptime', 'نامشخص')}\n\n"
            
            # CPU and Memory
            message += f"**CPU:** {cpu.get('percent', 0)}% (هسته‌ها: {cpu.get('cores', 0)})\n"
            message += f"**حافظه:** {memory.get('percent', 0)}% استفاده شده\n"
            message += f"**دیسک:** {disk.get('percent', 0)}% استفاده شده\n\n"
            
            # Network stats
            message += f"**شبکه:**\n"
            message += f"↑ ارسال: {ServerStats.format_bytes(network.get('bytes_sent', 0))}\n"
            message += f"↓ دریافت: {ServerStats.format_bytes(network.get('bytes_recv', 0))}\n"
            
            return message