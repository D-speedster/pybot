import sqlite3
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from pathlib import Path

from config import DATABASE_CONFIG

logger = logging.getLogger(__name__)

class DatabaseCursor:
    """Wrapper for database cursor to handle connection management"""
    
    def __init__(self, cursor, connection):
        self.cursor = cursor
        self.connection = connection
        self._closed = False
    
    async def fetchall(self):
        """Fetch all results"""
        if self._closed:
            return []
        try:
            results = self.cursor.fetchall()
            return results
        finally:
            self._close_connection()
    
    async def fetchone(self):
        """Fetch one result"""
        if self._closed:
            return None
        try:
            result = self.cursor.fetchone()
            return result
        finally:
            self._close_connection()
    
    def _close_connection(self):
        """Close connection safely"""
        if not self._closed:
            try:
                self.connection.close()
            except:
                pass
            self._closed = True
    
    def __getattr__(self, name):
        """Delegate other attributes to the cursor"""
        return getattr(self.cursor, name)

class Database:
    """Database manager for the bot"""
    
    def __init__(self):
        self.db_path = DATABASE_CONFIG['name']
        self.lock = asyncio.Lock()
        self._init_db()
    
    async def initialize(self):
        """Async initialization method"""
        # Database is already initialized in __init__
        pass
    
    def _init_db(self):
        """Initialize database and create tables"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('PRAGMA foreign_keys = ON')
                
                # Create tables
                for table_name, create_sql in DATABASE_CONFIG['tables'].items():
                    conn.execute(create_sql)
                    logger.debug(f"✅ Table {table_name} ready")
                
                conn.commit()
                logger.info("✅ Database initialized successfully")
        
        except Exception as e:
            logger.error(f"❌ Database initialization error: {e}")
            raise
    
    async def add_user(
        self, 
        user_id: int, 
        username: str = None, 
        first_name: str = None, 
        last_name: str = None
    ) -> bool:
        """Add or update user in database"""
        async with self.lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute(
                        '''INSERT OR REPLACE INTO users 
                           (user_id, username, first_name, last_name, join_date, last_activity) 
                           VALUES (?, ?, ?, ?, ?, ?)''',
                        (
                            user_id, username, first_name, last_name,
                            datetime.now().isoformat(),
                            datetime.now().isoformat()
                        )
                    )
                    conn.commit()
                    logger.debug(f"✅ User {user_id} added/updated")
                    return True
            
            except Exception as e:
                logger.error(f"❌ Error adding user {user_id}: {e}")
                return False
    
    async def update_user_activity(self, user_id: int) -> bool:
        """Update user's last activity"""
        async with self.lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute(
                        'UPDATE users SET last_activity = ? WHERE user_id = ?',
                        (datetime.now().isoformat(), user_id)
                    )
                    conn.commit()
                    return True
            
            except Exception as e:
                logger.error(f"❌ Error updating activity for user {user_id}: {e}")
                return False
    
    async def get_user_stats(self, user_id: int) -> Dict[str, Any]:
        """Get user statistics"""
        async with self.lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    conn.row_factory = sqlite3.Row
                    
                    # Get user info
                    user_row = conn.execute(
                        'SELECT * FROM users WHERE user_id = ?',
                        (user_id,)
                    ).fetchone()
                    
                    if not user_row:
                        return {}
                    
                    # Get download count
                    download_count = conn.execute(
                        'SELECT COUNT(*) as count FROM downloads WHERE user_id = ?',
                        (user_id,)
                    ).fetchone()['count']
                    
                    # Get successful downloads
                    successful_downloads = conn.execute(
                        'SELECT COUNT(*) as count FROM downloads WHERE user_id = ? AND status = "success"',
                        (user_id,)
                    ).fetchone()['count']
                    
                    return {
                        'user_id': user_row['user_id'],
                        'username': user_row['username'],
                        'first_name': user_row['first_name'],
                        'join_date': user_row['join_date'],
                        'last_activity': user_row['last_activity'],
                        'downloads': download_count,
                        'successful_downloads': successful_downloads
                    }
            
            except Exception as e:
                logger.error(f"❌ Error getting user stats for {user_id}: {e}")
                return {}
    
    async def get_bot_stats(self) -> Dict[str, Any]:
        """Get bot statistics"""
        async with self.lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    conn.row_factory = sqlite3.Row
                    
                    # Total users
                    total_users = conn.execute(
                        'SELECT COUNT(*) as count FROM users'
                    ).fetchone()['count']
                    
                    # Total downloads
                    total_downloads = conn.execute(
                        'SELECT COUNT(*) as count FROM downloads'
                    ).fetchone()['count']
                    
                    # Today's downloads
                    today = datetime.now().date().isoformat()
                    today_downloads = conn.execute(
                        'SELECT COUNT(*) as count FROM downloads WHERE DATE(download_date) = ?',
                        (today,)
                    ).fetchone()['count']
                    
                    # Active users (last 7 days)
                    week_ago = (datetime.now() - timedelta(days=7)).isoformat()
                    active_users = conn.execute(
                        'SELECT COUNT(*) as count FROM users WHERE last_activity > ?',
                        (week_ago,)
                    ).fetchone()['count']
                    
                    # Platform statistics
                    platform_stats = {}
                    platforms = conn.execute(
                        'SELECT platform, COUNT(*) as count FROM downloads GROUP BY platform'
                    ).fetchall()
                    
                    for row in platforms:
                        platform_stats[row['platform']] = row['count']
                    
                    return {
                        'total_users': total_users,
                        'total_downloads': total_downloads,
                        'today_downloads': today_downloads,
                        'active_users': active_users,
                        'platform_stats': platform_stats
                    }
            
            except Exception as e:
                logger.error(f"❌ Error getting bot stats: {e}")
                return {}
    
    async def log_download(
        self,
        user_id: int,
        url: str,
        platform: str,
        media_type: str,
        file_size: int,
        session_used: str,
        status: str
    ) -> bool:
        """Log a download attempt"""
        async with self.lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute(
                        '''INSERT INTO downloads 
                           (user_id, url, platform, media_type, file_size, session_used, download_date, status) 
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                        (
                            user_id, url, platform, media_type, file_size,
                            session_used, datetime.now().isoformat(), status
                        )
                    )
                    conn.commit()
                    logger.debug(f"✅ Download logged for user {user_id}")
                    return True
            
            except Exception as e:
                logger.error(f"❌ Error logging download for user {user_id}: {e}")
                return False
    
    async def store_temp_url(self, user_id: int, url: str, platform: str) -> bool:
        """Store temporary URL for callback processing"""
        async with self.lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    # Create temp_urls table if not exists
                    conn.execute(
                        '''CREATE TABLE IF NOT EXISTS temp_urls (
                            user_id INTEGER,
                            url TEXT,
                            platform TEXT,
                            created_at TEXT,
                            PRIMARY KEY (user_id)
                        )'''
                    )
                    
                    conn.execute(
                        'INSERT OR REPLACE INTO temp_urls (user_id, url, platform, created_at) VALUES (?, ?, ?, ?)',
                        (user_id, url, platform, datetime.now().isoformat())
                    )
                    conn.commit()
                    return True
            
            except Exception as e:
                logger.error(f"❌ Error storing temp URL for user {user_id}: {e}")
                return False
    
    async def get_temp_url(self, user_id: int) -> Optional[Dict[str, str]]:
        """Get temporary URL for user"""
        async with self.lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    conn.row_factory = sqlite3.Row
                    
                    row = conn.execute(
                        'SELECT * FROM temp_urls WHERE user_id = ?',
                        (user_id,)
                    ).fetchone()
                    
                    if row:
                        # Check if not expired (1 hour)
                        created_at = datetime.fromisoformat(row['created_at'])
                        if datetime.now() - created_at < timedelta(hours=1):
                            return {
                                'url': row['url'],
                                'platform': row['platform'],
                                'created_at': row['created_at']
                            }
                        else:
                            # Remove expired URL
                            conn.execute('DELETE FROM temp_urls WHERE user_id = ?', (user_id,))
                            conn.commit()
                    
                    return None
            
            except Exception as e:
                logger.error(f"❌ Error getting temp URL for user {user_id}: {e}")
                return None
    
    async def cleanup_old_temp_urls(self, hours: int = 24) -> int:
        """Clean up old temporary URLs"""
        async with self.lock:
            try:
                cutoff_time = (datetime.now() - timedelta(hours=hours)).isoformat()
                
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.execute(
                        "DELETE FROM temp_urls WHERE created_at < ?",
                        (cutoff_time,)
                    )
                    deleted_count = cursor.rowcount
                    conn.commit()
                    
                    if deleted_count > 0:
                        logger.info(f"🧹 Cleaned up {deleted_count} old temp URLs")
                    
                    return deleted_count
                    
            except Exception as e:
                logger.error(f"❌ Error cleaning temp URLs: {e}")
                return 0
    
    async def add_message_to_queue(self, user_id: int, message_text: str, message_type: str = 'text') -> bool:
        """Add message to queue for processing when bot is back online"""
        async with self.lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute(
                        "INSERT INTO message_queue (user_id, message_text, message_type, created_at) VALUES (?, ?, ?, ?)",
                        (user_id, message_text, message_type, datetime.now().isoformat())
                    )
                    conn.commit()
                    logger.info(f"📝 Added message to queue for user {user_id}")
                    return True
            except Exception as e:
                logger.error(f"❌ Error adding message to queue: {e}")
                return False
    
    async def get_unprocessed_messages(self) -> List[Dict[str, Any]]:
        """Get all unprocessed messages from queue"""
        async with self.lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.execute(
                        "SELECT * FROM message_queue WHERE processed = 0 ORDER BY created_at ASC"
                    )
                    messages = [dict(row) for row in cursor.fetchall()]
                    return messages
            except Exception as e:
                logger.error(f"❌ Error getting unprocessed messages: {e}")
                return []
    
    async def mark_message_processed(self, message_id: int) -> bool:
        """Mark message as processed"""
        async with self.lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute(
                        "UPDATE message_queue SET processed = 1 WHERE id = ?",
                        (message_id,)
                    )
                    conn.commit()
                    return True
            except Exception as e:
                logger.error(f"❌ Error marking message as processed: {e}")
                return False
    
    async def cleanup_processed_messages(self, hours: int = 24) -> int:
        """Clean up old processed messages"""
        async with self.lock:
            try:
                cutoff_time = (datetime.now() - timedelta(hours=hours)).isoformat()
                
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.execute(
                        "DELETE FROM message_queue WHERE processed = 1 AND created_at < ?",
                        (cutoff_time,)
                    )
                    deleted_count = cursor.rowcount
                    conn.commit()
                    
                    if deleted_count > 0:
                        logger.info(f"🧹 Cleaned up {deleted_count} processed messages")
                    
                    return deleted_count
                    
            except Exception as e:
                logger.error(f"❌ Error cleaning processed messages: {e}")
                return 0
    
    async def update_session_status(
        self,
        session_name: str,
        phone_number: Optional[str],
        is_active: bool,
        last_used: Optional[str]
    ) -> bool:
        """Update session status in database"""
        async with self.lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    # Check if session exists
                    existing = conn.execute(
                        'SELECT id FROM sessions WHERE session_name = ?',
                        (session_name,)
                    ).fetchone()
                    
                    if existing:
                        # Update existing session
                        conn.execute(
                            '''UPDATE sessions 
                               SET phone_number = ?, is_active = ?, last_used = ?, usage_count = usage_count + 1
                               WHERE session_name = ?''',
                            (phone_number, is_active, last_used, session_name)
                        )
                    else:
                        # Insert new session
                        conn.execute(
                            '''INSERT INTO sessions 
                               (session_name, phone_number, is_active, last_used, usage_count, created_at) 
                               VALUES (?, ?, ?, ?, 0, ?)''',
                            (
                                session_name, phone_number, is_active, last_used,
                                datetime.now().isoformat()
                            )
                        )
                    
                    conn.commit()
                    return True
            
            except Exception as e:
                logger.error(f"❌ Error updating session status for {session_name}: {e}")
                return False
    
    async def get_session_stats(self) -> List[Dict[str, Any]]:
        """Get session statistics"""
        async with self.lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    conn.row_factory = sqlite3.Row
                    
                    rows = conn.execute(
                        'SELECT * FROM sessions ORDER BY created_at DESC'
                    ).fetchall()
                    
                    return [dict(row) for row in rows]
            
            except Exception as e:
                logger.error(f"❌ Error getting session stats: {e}")
                return []
    
    async def get_total_users_count(self) -> int:
        """Get total number of users"""
        async with self.lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    result = conn.execute('SELECT COUNT(*) FROM users').fetchone()
                    return result[0] if result else 0
            except Exception as e:
                logger.error(f"❌ Error getting total users count: {e}")
                return 0
    
    async def get_total_downloads_count(self) -> int:
        """Get total number of downloads"""
        async with self.lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    result = conn.execute('SELECT COUNT(*) FROM downloads').fetchone()
                    return result[0] if result else 0
            except Exception as e:
                logger.error(f"❌ Error getting total downloads count: {e}")
                return 0
    
    async def get_active_users_today(self) -> int:
        """Get number of active users today"""
        async with self.lock:
            try:
                today = datetime.now().date().isoformat()
                with sqlite3.connect(self.db_path) as conn:
                    result = conn.execute(
                        'SELECT COUNT(DISTINCT user_id) FROM users WHERE DATE(last_activity) = ?',
                        (today,)
                    ).fetchone()
                    return result[0] if result else 0
            except Exception as e:
                logger.error(f"❌ Error getting active users today: {e}")
                return 0
    
    async def get_active_users_week(self) -> int:
        """Get number of active users this week"""
        async with self.lock:
            try:
                week_ago = (datetime.now() - timedelta(days=7)).isoformat()
                with sqlite3.connect(self.db_path) as conn:
                    result = conn.execute(
                        'SELECT COUNT(DISTINCT user_id) FROM users WHERE last_activity >= ?',
                        (week_ago,)
                    ).fetchone()
                    return result[0] if result else 0
            except Exception as e:
                logger.error(f"❌ Error getting active users this week: {e}")
                return 0
    
    async def get_active_users_month(self) -> int:
        """Get number of active users this month"""
        async with self.lock:
            try:
                month_ago = (datetime.now() - timedelta(days=30)).isoformat()
                with sqlite3.connect(self.db_path) as conn:
                    result = conn.execute(
                        'SELECT COUNT(DISTINCT user_id) FROM users WHERE last_activity >= ?',
                        (month_ago,)
                    ).fetchone()
                    return result[0] if result else 0
            except Exception as e:
                logger.error(f"❌ Error getting active users this month: {e}")
                return 0
    
    async def get_all_users(self) -> List[Dict[str, Any]]:
        """Get all users from database"""
        async with self.lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    conn.row_factory = sqlite3.Row
                    rows = conn.execute(
                        'SELECT user_id, username, first_name, last_name FROM users ORDER BY join_date DESC'
                    ).fetchall()
                    
                    users = []
                    for row in rows:
                        name = row['first_name'] or 'Unknown'
                        if row['last_name']:
                            name += f" {row['last_name']}"
                        
                        users.append({
                            'id': row['user_id'],
                            'name': name,
                            'username': row['username'] or 'No username'
                        })
                    
                    return users
            except Exception as e:
                logger.error(f"❌ Error getting all users: {e}")
                return []
    
    async def execute(self, query: str, params: tuple = None):
        """Execute a database query"""
        async with self.lock:
            try:
                conn = sqlite3.connect(self.db_path, timeout=30.0)
                conn.row_factory = sqlite3.Row
                conn.execute('PRAGMA journal_mode=WAL')
                conn.execute('PRAGMA synchronous=NORMAL')
                conn.execute('PRAGMA cache_size=1000')
                conn.execute('PRAGMA temp_store=MEMORY')
                
                if params:
                    cursor = conn.execute(query, params)
                else:
                    cursor = conn.execute(query)
                
                # For INSERT/UPDATE/DELETE queries, commit immediately
                if query.strip().upper().startswith(('INSERT', 'UPDATE', 'DELETE', 'CREATE')):
                    conn.commit()
                
                # Return a wrapper that handles the connection
                return DatabaseCursor(cursor, conn)
            except Exception as e:
                logger.error(f"❌ Error executing query: {e}")
                raise
    
    async def commit(self):
        """Commit database changes"""
        # SQLite auto-commits with context manager
        pass
    
    async def close(self):
        """Close database connection"""
        # SQLite connections are closed automatically
        logger.info("✅ Database connections closed")