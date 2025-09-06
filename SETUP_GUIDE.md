# Quick Setup Guide

## 🚀 Getting Started

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Bot Credentials

Edit `config.py` or set environment variables:

```python
# Bot Configuration
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"  # Get from @BotFather

# Telegram API Configuration  
API_ID = YOUR_API_ID  # Get from https://my.telegram.org
API_HASH = "YOUR_API_HASH"  # Get from https://my.telegram.org
```

### 3. Run the Bot
```bash
python main.py
```

## 🔧 Configuration Options

### Proxy Settings (Optional)
If you need to use a proxy:

```python
PROXY_CONFIG = {
    'enabled': True,
    'type': 'socks5',  # or 'http'
    'host': '127.0.0.1',
    'port': 1080,
    'username': 'your_username',  # optional
    'password': 'your_password'   # optional
}
```

### Admin Configuration
Set admin user IDs to access admin commands:

```python
ADMIN_IDS = [123456789, 987654321]  # Replace with your Telegram user IDs
```

## 📱 Bot Features

### User Commands
- `/start` - Start the bot and see welcome message
- `/help` - Show help and available commands
- Send YouTube or Instagram URL - Download media

### Admin Commands (for configured admins)
- `/sessions` - Manage userbot sessions
- `/stats` - View bot statistics
- `/cleanup` - Clean temporary files
- `/health` - Check system health

## 🔐 Security Notes

1. **Never share your bot token or API credentials**
2. **Use environment variables for production**
3. **Configure admin IDs carefully**
4. **Use proxy if needed for your region**

## 🛠️ Troubleshooting

### Connection Issues
- Check your internet connection
- Verify bot token is correct
- Try using a proxy if Telegram is blocked
- Check firewall settings

### Download Issues
- Ensure yt-dlp is up to date: `pip install -U yt-dlp`
- Check if the URL is supported
- Verify file size limits

### Session Issues
- Delete old session files if having problems
- Re-authenticate userbot sessions
- Check API credentials

## 📊 Monitoring

The bot creates logs in the `logs/` directory:
- `bot.log` - General bot logs
- `downloads.log` - Download activity
- `sessions.log` - Session management
- `errors.log` - Error tracking

## 🔄 Updates

To update dependencies:
```bash
pip install -r requirements.txt --upgrade
```

To update yt-dlp (recommended regularly):
```bash
pip install -U yt-dlp
```

---

**Need help?** Check the logs or create an issue with error details.