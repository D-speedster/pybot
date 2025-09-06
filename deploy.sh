#!/bin/bash

# Telegram Bot Deployment Script
# Usage: ./deploy.sh [start|stop|restart|logs|status]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project name
PROJECT_NAME="telegram-userbot-downloader"

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if Docker is installed
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
}

# Function to check environment file
check_env() {
    if [ ! -f ".env" ]; then
        print_warning ".env file not found. Creating from .env.example..."
        if [ -f ".env.example" ]; then
            cp .env.example .env
            print_warning "Please edit .env file with your bot credentials before starting!"
            print_warning "Required: BOT_TOKEN, API_ID, API_HASH, ADMIN_IDS"
            return 1
        else
            print_error ".env.example file not found!"
            exit 1
        fi
    fi
    return 0
}

# Function to start the bot
start_bot() {
    print_status "Starting Telegram Bot..."
    
    # Create necessary directories
    mkdir -p sessions logs temp_downloads
    
    # Build and start containers
    docker-compose up -d --build
    
    print_success "Bot started successfully!"
    print_status "Use 'docker-compose logs -f' to view logs"
    print_status "Use './deploy.sh logs' for formatted logs"
}

# Function to stop the bot
stop_bot() {
    print_status "Stopping Telegram Bot..."
    docker-compose down
    print_success "Bot stopped successfully!"
}

# Function to restart the bot
restart_bot() {
    print_status "Restarting Telegram Bot..."
    docker-compose down
    docker-compose up -d --build
    print_success "Bot restarted successfully!"
}

# Function to show logs
show_logs() {
    print_status "Showing bot logs (Press Ctrl+C to exit)..."
    docker-compose logs -f --tail=100
}

# Function to show status
show_status() {
    print_status "Bot Status:"
    docker-compose ps
    
    echo ""
    print_status "Container Health:"
    docker inspect --format='{{.State.Health.Status}}' telegram-userbot-downloader 2>/dev/null || echo "Health check not available"
    
    echo ""
    print_status "Resource Usage:"
    docker stats --no-stream telegram-userbot-downloader 2>/dev/null || echo "Container not running"
}

# Function to update the bot
update_bot() {
    print_status "Updating Telegram Bot..."
    
    # Pull latest changes (if using git)
    if [ -d ".git" ]; then
        git pull
    fi
    
    # Rebuild and restart
    docker-compose down
    docker-compose build --no-cache
    docker-compose up -d
    
    print_success "Bot updated successfully!"
}

# Function to clean up
cleanup() {
    print_status "Cleaning up Docker resources..."
    
    # Stop and remove containers
    docker-compose down --remove-orphans
    
    # Remove unused images
    docker image prune -f
    
    print_success "Cleanup completed!"
}

# Function to backup data
backup_data() {
    print_status "Creating backup..."
    
    BACKUP_DIR="backup_$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"
    
    # Backup important files
    cp -r sessions "$BACKUP_DIR/" 2>/dev/null || true
    cp -r logs "$BACKUP_DIR/" 2>/dev/null || true
    cp userbot_manager.db "$BACKUP_DIR/" 2>/dev/null || true
    cp .env "$BACKUP_DIR/" 2>/dev/null || true
    
    print_success "Backup created: $BACKUP_DIR"
}

# Function to show help
show_help() {
    echo "Telegram Bot Deployment Script"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  start     Start the bot"
    echo "  stop      Stop the bot"
    echo "  restart   Restart the bot"
    echo "  logs      Show bot logs"
    echo "  status    Show bot status"
    echo "  update    Update and restart the bot"
    echo "  cleanup   Clean up Docker resources"
    echo "  backup    Backup bot data"
    echo "  help      Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 start    # Start the bot"
    echo "  $0 logs     # View logs"
    echo "  $0 status   # Check status"
}

# Main script logic
main() {
    # Check if Docker is available
    check_docker
    
    # Parse command line arguments
    case "${1:-help}" in
        "start")
            if check_env; then
                start_bot
            else
                print_error "Please configure .env file first!"
                exit 1
            fi
            ;;
        "stop")
            stop_bot
            ;;
        "restart")
            if check_env; then
                restart_bot
            else
                print_error "Please configure .env file first!"
                exit 1
            fi
            ;;
        "logs")
            show_logs
            ;;
        "status")
            show_status
            ;;
        "update")
            update_bot
            ;;
        "cleanup")
            cleanup
            ;;
        "backup")
            backup_data
            ;;
        "help")
            show_help
            ;;
        *)
            print_error "Unknown command: $1"
            show_help
            exit 1
            ;;
    esac
}

# Run main function
main "$@"