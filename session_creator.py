#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Session Creator for Userbot
This script helps create new Telegram sessions for the bot
"""

import asyncio
import logging
from pathlib import Path
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError, PhoneCodeInvalidError

from config import API_ID, API_HASH, SESSIONS_DIR

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SessionCreator:
    """Helper class to create new Telegram sessions"""
    
    def __init__(self):
        self.sessions_dir = SESSIONS_DIR
        self.sessions_dir.mkdir(exist_ok=True)
    
    async def create_session(self, session_name: str, phone_number: str):
        """Create a new Telegram session"""
        session_path = self.sessions_dir / session_name
        
        # Create client without proxy for better performance
        client_kwargs = {
            'session': str(session_path),
            'api_id': API_ID,
            'api_hash': API_HASH
        }
        
        client = TelegramClient(**client_kwargs)
        
        try:
            await client.connect()
            
            # Check if already authorized
            if await client.is_user_authorized():
                me = await client.get_me()
                print(f"✅ Session {session_name} already exists for @{me.username}")
                return True
            
            # Send code request
            print(f"📱 Sending code to {phone_number}...")
            await client.send_code_request(phone_number)
            
            # Get code from user
            code = input("🔢 Enter the code you received: ")
            
            try:
                await client.sign_in(phone_number, code)
            except SessionPasswordNeededError:
                # Two-factor authentication enabled
                password = input("🔐 Enter your 2FA password: ")
                await client.sign_in(password=password)
            
            # Get user info
            me = await client.get_me()
            print(f"✅ Session created successfully for @{me.username} ({me.first_name})")
            print(f"📁 Session saved as: {session_path}.session")
            
            return True
            
        except PhoneCodeInvalidError:
            print("❌ Invalid code. Please try again.")
            return False
        except Exception as e:
            print(f"❌ Error creating session: {e}")
            return False
        finally:
            await client.disconnect()

async def main():
    """Main function to create sessions interactively"""
    creator = SessionCreator()
    
    print("🤖 Telegram Session Creator")
    print("=" * 30)
    
    while True:
        print("\n📋 Options:")
        print("1. Create new session")
        print("2. List existing sessions")
        print("3. Exit")
        
        choice = input("\n👉 Choose an option (1-3): ").strip()
        
        if choice == '1':
            session_name = input("📝 Enter session name (e.g., 'user1'): ").strip()
            if not session_name:
                print("❌ Session name cannot be empty!")
                continue
            
            phone_number = input("📱 Enter phone number (with country code, e.g., +1234567890): ").strip()
            if not phone_number.startswith('+'):
                print("❌ Phone number must start with + and country code!")
                continue
            
            print(f"\n🔄 Creating session '{session_name}' for {phone_number}...")
            success = await creator.create_session(session_name, phone_number)
            
            if success:
                print("\n🎉 Session created successfully!")
                print("💡 You can now restart your bot to use this session.")
            else:
                print("\n❌ Failed to create session. Please try again.")
        
        elif choice == '2':
            sessions = list(SESSIONS_DIR.glob("*.session"))
            if sessions:
                print("\n📱 Existing sessions:")
                for i, session in enumerate(sessions, 1):
                    print(f"  {i}. {session.stem}")
            else:
                print("\n📭 No sessions found.")
        
        elif choice == '3':
            print("\n👋 Goodbye!")
            break
        
        else:
            print("\n❌ Invalid choice. Please try again.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Session creator stopped by user.")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")