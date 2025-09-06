# Telegram Bot Makefile
# Simple commands for managing the bot

.PHONY: help install start stop restart logs status update backup cleanup test

# Default target
help:
	@echo "🤖 Telegram Bot Management Commands"
	@echo ""
	@echo "Available commands:"
	@echo "  make install    - Install dependencies and setup environment"
	@echo "  make start      - Start the bot"
	@echo "  make stop       - Stop the bot"
	@echo "  make restart    - Restart the bot"
	@echo "  make logs       - Show bot logs"
	@echo "  make status     - Show bot status"
	@echo "  make update     - Update and restart the bot"
	@echo "  make backup     - Create backup of bot data"
	@echo "  make cleanup    - Clean up Docker resources"
	@echo "  make test       - Run tests"
	@echo "  make quick      - Quick start (setup + start)"
	@echo ""
	@echo "Examples:"
	@echo "  make quick      # Setup and start everything"
	@echo "  make logs       # View live logs"
	@echo "  make status     # Check if bot is running"

# Quick start - setup and run everything
quick:
	@echo "🚀 Quick starting Telegram Bot..."
	@chmod +x quick-start.sh deploy.sh 2>/dev/null || true
	@./quick-start.sh

# Install dependencies and setup
install:
	@echo "📦 Installing dependencies..."
	@chmod +x deploy.sh 2>/dev/null || true
	@if [ ! -f ".env" ]; then \
		echo "⚠️  Creating .env from template..."; \
		cp .env.example .env; \
		echo "📝 Please edit .env file with your credentials"; \
	fi
	@mkdir -p sessions logs temp_downloads
	@echo "✅ Installation completed"

# Start the bot
start:
	@echo "🚀 Starting Telegram Bot..."
	@./deploy.sh start

# Stop the bot
stop:
	@echo "🛑 Stopping Telegram Bot..."
	@./deploy.sh stop

# Restart the bot
restart:
	@echo "🔄 Restarting Telegram Bot..."
	@./deploy.sh restart

# Show logs
logs:
	@echo "📋 Showing bot logs (Press Ctrl+C to exit)..."
	@./deploy.sh logs

# Show status
status:
	@echo "📊 Bot Status:"
	@./deploy.sh status

# Update the bot
update:
	@echo "⬆️  Updating Telegram Bot..."
	@./deploy.sh update

# Create backup
backup:
	@echo "💾 Creating backup..."
	@./deploy.sh backup

# Cleanup Docker resources
cleanup:
	@echo "🧹 Cleaning up Docker resources..."
	@./deploy.sh cleanup

# Run tests
test:
	@echo "🧪 Running tests..."
	@if [ -f "requirements.txt" ]; then \
		python -m pytest tests/ -v 2>/dev/null || echo "No tests found"; \
	else \
		echo "❌ requirements.txt not found"; \
	fi

# Development mode
dev:
	@echo "🔧 Starting in development mode..."
	@docker-compose -f docker-compose.yml -f docker-compose.dev.yml up --build

# Production deployment
prod:
	@echo "🏭 Deploying to production..."
	@docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

# Monitor resources
monitor:
	@echo "📈 Monitoring bot resources..."
	@docker stats telegram-userbot-downloader

# View specific logs
logs-error:
	@echo "❌ Showing error logs..."
	@docker-compose logs telegram-bot | grep -i error

logs-download:
	@echo "📥 Showing download logs..."
	@tail -f logs/downloads.log 2>/dev/null || echo "Download log not found"

logs-session:
	@echo "🔐 Showing session logs..."
	@tail -f logs/sessions.log 2>/dev/null || echo "Session log not found"

# Health check
health:
	@echo "🏥 Checking bot health..."
	@docker inspect --format='{{.State.Health.Status}}' telegram-userbot-downloader 2>/dev/null || echo "Health check not available"

# Shell access to container
shell:
	@echo "🐚 Accessing bot container shell..."
	@docker-compose exec telegram-bot /bin/bash

# Reset everything (dangerous)
reset:
	@echo "⚠️  This will delete all data! Are you sure? [y/N]"
	@read -r response; \
	if [ "$$response" = "y" ] || [ "$$response" = "Y" ]; then \
		echo "🗑️  Resetting everything..."; \
		docker-compose down -v; \
		docker system prune -af; \
		rm -rf sessions/* logs/* temp_downloads/* *.db *.session*; \
		echo "✅ Reset completed"; \
	else \
		echo "❌ Reset cancelled"; \
	fi

# Show configuration
config:
	@echo "⚙️  Current configuration:"
	@docker-compose config

# Update dependencies
update-deps:
	@echo "📦 Updating dependencies..."
	@docker-compose build --no-cache

# Generate documentation
docs:
	@echo "📚 Generating documentation..."
	@echo "Available documentation files:"
	@ls -la *.md 2>/dev/null || echo "No documentation found"

# Validate environment
validate:
	@echo "✅ Validating environment..."
	@if [ ! -f ".env" ]; then \
		echo "❌ .env file not found"; \
		exit 1; \
	fi
	@if ! command -v docker >/dev/null 2>&1; then \
		echo "❌ Docker not installed"; \
		exit 1; \
	fi
	@if ! command -v docker-compose >/dev/null 2>&1; then \
		echo "❌ Docker Compose not installed"; \
		exit 1; \
	fi
	@echo "✅ Environment is valid"

# Show help for specific command
help-%:
	@case $* in \
		start) echo "Start the Telegram bot using Docker Compose" ;; \
		stop) echo "Stop the running Telegram bot" ;; \
		restart) echo "Restart the Telegram bot (stop + start)" ;; \
		logs) echo "Show live logs from the bot container" ;; \
		status) echo "Display current status of the bot" ;; \
		update) echo "Pull latest changes and restart the bot" ;; \
		backup) echo "Create a backup of bot data (sessions, logs, db)" ;; \
		cleanup) echo "Remove unused Docker images and containers" ;; \
		*) echo "Unknown command: $*" ;; \
	esac