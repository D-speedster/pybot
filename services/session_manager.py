import asyncio
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import random

from telethon import TelegramClient
from telethon.errors import (
    SessionPasswordNeededError, PhoneCodeInvalidError,
    PhoneNumberInvalidError, FloodWaitError, AuthKeyUnregisteredError
)

from config import (
    API_ID, API_HASH, SESSIONS_DIR, USERBOT_CONFIG,
    DATABASE_CONFIG
)
from utils.database import Database

logger = logging.getLogger(__name__)

class SessionManager:
    """Manages multiple Userbot sessions with load balancing"""
    
    def __init__(self):
        self.active_sessions: Dict[str, TelegramClient] = {}
        self.session_stats: Dict[str, Dict[str, Any]] = {}
        self.db = Database()
        self.current_session_index = 0
        self.last_cleanup = datetime.now()
        
    async def initialize(self):
        """Initialize session manager and load existing sessions"""
        logger.info("🔄 Initializing Session Manager...")
        
        # Create sessions directory if not exists
        SESSIONS_DIR.mkdir(exist_ok=True)
        
        # Load existing sessions
        await self.load_existing_sessions()
        
        # Start session health monitor
        asyncio.create_task(self.session_health_monitor())
        
        logger.info(f"✅ Session Manager initialized with {len(self.active_sessions)} sessions")
    
    async def load_existing_sessions(self):
        """Load and validate existing session files"""
        session_files = list(SESSIONS_DIR.glob("*.session"))
        
        for session_file in session_files:
            session_name = session_file.stem
            try:
                await self.load_session(session_name)
            except Exception as e:
                logger.error(f"❌ Failed to load session {session_name}: {e}")
    
    async def load_session(self, session_name: str) -> bool:
        """Load a specific session"""
        session_path = SESSIONS_DIR / session_name
        
        try:
            # Configure proxy if enabled
            proxy = None
            client_kwargs = {
                'session': str(session_path),
                'api_id': API_ID,
                'api_hash': API_HASH,
                'connection_retries': 3,
                'retry_delay': 1,
                'timeout': 30
            }
            
            # Proxy functionality removed for better performance
            
            # Create client
            client = TelegramClient(**client_kwargs)
            
            # Connect and validate
            await client.connect()
            
            if await client.is_user_authorized():
                # Get user info
                me = await client.get_me()
                
                self.active_sessions[session_name] = client
                self.session_stats[session_name] = {
                    'user_id': me.id,
                    'username': me.username,
                    'phone': me.phone,
                    'usage_count': 0,
                    'last_used': datetime.now(),
                    'created_at': datetime.now(),
                    'active': True,
                    'errors': 0
                }
                
                # Update database
                await self.db.update_session_status(
                    session_name, me.phone, True, datetime.now().isoformat()
                )
                
                logger.info(f"✅ Session {session_name} loaded successfully (@{me.username})")
                return True
            else:
                logger.warning(f"⚠️ Session {session_name} is not authorized")
                await client.disconnect()
                return False
                
        except AuthKeyUnregisteredError:
            logger.error(f"❌ Session {session_name} is invalid (auth key unregistered)")
            # Remove invalid session file
            if session_path.with_suffix('.session').exists():
                session_path.with_suffix('.session').unlink()
            return False
        except Exception as e:
            logger.error(f"❌ Error loading session {session_name}: {e}")
            return False
    
    async def create_new_session(self, session_name: str, phone_number: str) -> bool:
        """Create a new Userbot session"""
        if len(self.active_sessions) >= USERBOT_CONFIG['max_sessions']:
            logger.warning("⚠️ Maximum sessions limit reached")
            return False
        
        session_path = SESSIONS_DIR / session_name
        
        try:
            # Configure proxy if enabled
            client_kwargs = {
                'session': str(session_path),
                'api_id': API_ID,
                'api_hash': API_HASH
            }
            
            # Proxy functionality removed for better performance
            
            client = TelegramClient(**client_kwargs)
            
            await client.connect()
            
            # Send code request
            await client.send_code_request(phone_number)
            logger.info(f"📱 Code sent to {phone_number} for session {session_name}")
            
            # Note: In a real implementation, you'd need to handle the code input
            # This is a simplified version - you'd need a proper interface for this
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error creating session {session_name}: {e}")
            return False
    
    async def get_best_session(self) -> Optional[TelegramClient]:
        """Get the best available session based on load balancing method"""
        if not self.active_sessions:
            return None
        
        method = USERBOT_CONFIG['load_balance_method']
        
        if method == 'round_robin':
            return await self._get_round_robin_session()
        elif method == 'least_used':
            return await self._get_least_used_session()
        else:
            # Random selection as fallback
            return random.choice(list(self.active_sessions.values()))
    
    async def _get_round_robin_session(self) -> Optional[TelegramClient]:
        """Get session using round-robin method"""
        session_names = list(self.active_sessions.keys())
        if not session_names:
            return None
        
        session_name = session_names[self.current_session_index % len(session_names)]
        self.current_session_index += 1
        
        # Update usage stats
        self.session_stats[session_name]['usage_count'] += 1
        self.session_stats[session_name]['last_used'] = datetime.now()
        
        return self.active_sessions[session_name]
    
    async def _get_least_used_session(self) -> Optional[TelegramClient]:
        """Get the least used session"""
        if not self.session_stats:
            return None
        
        # Find session with minimum usage count
        least_used = min(
            self.session_stats.items(),
            key=lambda x: x[1]['usage_count']
        )
        
        session_name = least_used[0]
        
        # Update usage stats
        self.session_stats[session_name]['usage_count'] += 1
        self.session_stats[session_name]['last_used'] = datetime.now()
        
        return self.active_sessions[session_name]
    
    async def remove_session(self, session_name: str) -> bool:
        """Remove a session"""
        if session_name in self.active_sessions:
            try:
                await self.active_sessions[session_name].disconnect()
                del self.active_sessions[session_name]
                
                if session_name in self.session_stats:
                    del self.session_stats[session_name]
                
                # Update database
                await self.db.update_session_status(session_name, None, False, None)
                
                logger.info(f"🗑️ Session {session_name} removed")
                return True
            except Exception as e:
                logger.error(f"❌ Error removing session {session_name}: {e}")
                return False
        return False
    
    async def get_sessions_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all sessions"""
        status = {}
        
        for session_name, stats in self.session_stats.items():
            status[session_name] = {
                'active': session_name in self.active_sessions,
                'usage_count': stats['usage_count'],
                'last_used': stats['last_used'].strftime('%Y-%m-%d %H:%M:%S'),
                'username': stats.get('username', 'Unknown'),
                'phone': stats.get('phone', 'Unknown'),
                'errors': stats.get('errors', 0)
            }
        
        return status
    
    async def session_health_monitor(self):
        """Monitor session health and reconnect if needed"""
        while True:
            try:
                await asyncio.sleep(300)  # Check every 5 minutes
                
                current_time = datetime.now()
                
                # Check each session
                sessions_to_remove = []
                for session_name, client in self.active_sessions.items():
                    try:
                        # Test connection
                        if not client.is_connected():
                            logger.warning(f"⚠️ Session {session_name} disconnected, reconnecting...")
                            await client.connect()
                        
                        # Test authorization
                        if not await client.is_user_authorized():
                            logger.error(f"❌ Session {session_name} lost authorization")
                            sessions_to_remove.append(session_name)
                            continue
                        
                        # Reset error count on successful check
                        self.session_stats[session_name]['errors'] = 0
                        
                    except Exception as e:
                        logger.error(f"❌ Health check failed for session {session_name}: {e}")
                        
                        # Increment error count
                        self.session_stats[session_name]['errors'] += 1
                        
                        # Remove session if too many errors
                        if self.session_stats[session_name]['errors'] >= 3:
                            sessions_to_remove.append(session_name)
                
                # Remove problematic sessions
                for session_name in sessions_to_remove:
                    await self.remove_session(session_name)
                
                # Cleanup old temporary data
                if current_time - self.last_cleanup > timedelta(hours=1):
                    await self.cleanup_old_data()
                    self.last_cleanup = current_time
                
            except Exception as e:
                logger.error(f"❌ Session health monitor error: {e}")
    
    async def cleanup_old_data(self):
        """Cleanup old temporary data"""
        try:
            # Clean old temporary URLs
            await self.db.cleanup_old_temp_urls()
            logger.debug("🧹 Cleaned up old temporary data")
        except Exception as e:
            logger.error(f"❌ Cleanup error: {e}")
    
    async def handle_flood_wait(self, session_name: str, wait_time: int):
        """Handle flood wait for a specific session"""
        logger.warning(f"⏰ Session {session_name} hit flood wait: {wait_time}s")
        
        # Temporarily disable session
        if session_name in self.active_sessions:
            self.session_stats[session_name]['active'] = False
            
            # Re-enable after wait time
            async def re_enable():
                await asyncio.sleep(wait_time + 10)  # Add 10s buffer
                if session_name in self.session_stats:
                    self.session_stats[session_name]['active'] = True
                    logger.info(f"✅ Session {session_name} re-enabled after flood wait")
            
            asyncio.create_task(re_enable())
    
    async def shutdown(self):
        """Shutdown all sessions"""
        logger.info("🛑 Shutting down all sessions...")
        
        for session_name, client in self.active_sessions.items():
            try:
                await client.disconnect()
                logger.info(f"✅ Session {session_name} disconnected")
            except Exception as e:
                logger.error(f"❌ Error disconnecting session {session_name}: {e}")
        
        self.active_sessions.clear()
        self.session_stats.clear()
        
        logger.info("✅ All sessions shut down")