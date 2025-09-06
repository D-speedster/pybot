#!/bin/bash

# Quick Start Script for Telegram Bot
# This script will set up everything with minimal user input

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# Print banner
print_banner() {
    echo -e "${PURPLE}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                    🤖 Telegram Bot Setup                    ║"
    echo "║              Quick Start - One Command Deployment           ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_step() {
    echo -e "${CYAN}[STEP]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[⚠]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_info() {
    echo -e "${BLUE}[ℹ]${NC} $1"
}

# Check system requirements
check_requirements() {
    print_step "Checking system requirements..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed!"
        print_info "Installing Docker..."
        
        # Install Docker based on OS
        if [[ "$OSTYPE" == "linux-gnu"* ]]; then
            curl -fsSL https://get.docker.com -o get-docker.sh
            sudo sh get-docker.sh
            sudo usermod -aG docker $USER
            rm get-docker.sh
        else
            print_error "Please install Docker manually for your OS"
            exit 1
        fi
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed!"
        print_info "Installing Docker Compose..."
        
        sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
        sudo chmod +x /usr/local/bin/docker-compose
    fi
    
    print_success "System requirements satisfied"
}

# Setup environment
setup_environment() {
    print_step "Setting up environment..."
    
    # Create .env if it doesn't exist
    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            cp .env.example .env
            print_success "Created .env file from template"
        else
            print_error ".env.example not found!"
            exit 1
        fi
    fi
    
    # Check if .env is configured
    if grep -q "your_bot_token_here" .env; then
        print_warning "Bot credentials not configured!"
        configure_bot_credentials
    else
        print_success "Environment already configured"
    fi
}

# Configure bot credentials interactively
configure_bot_credentials() {
    print_step "Configuring bot credentials..."
    
    echo -e "${YELLOW}Please provide your bot credentials:${NC}"
    echo -e "${BLUE}You can get these from:${NC}"
    echo -e "${BLUE}- Bot Token: @BotFather on Telegram${NC}"
    echo -e "${BLUE}- API ID/Hash: https://my.telegram.org${NC}"
    echo ""
    
    # Get Bot Token
    while true; do
        read -p "Enter Bot Token: " BOT_TOKEN
        if [[ $BOT_TOKEN =~ ^[0-9]+:[A-Za-z0-9_-]+$ ]]; then
            break
        else
            print_error "Invalid bot token format!"
        fi
    done
    
    # Get API ID
    while true; do
        read -p "Enter API ID: " API_ID
        if [[ $API_ID =~ ^[0-9]+$ ]]; then
            break
        else
            print_error "API ID must be numeric!"
        fi
    done
    
    # Get API Hash
    while true; do
        read -p "Enter API Hash: " API_HASH
        if [[ ${#API_HASH} -eq 32 ]]; then
            break
        else
            print_error "API Hash must be 32 characters long!"
        fi
    done
    
    # Get Admin IDs
    read -p "Enter Admin User IDs (comma-separated): " ADMIN_IDS
    
    # Update .env file
    sed -i "s/BOT_TOKEN=.*/BOT_TOKEN=$BOT_TOKEN/" .env
    sed -i "s/API_ID=.*/API_ID=$API_ID/" .env
    sed -i "s/API_HASH=.*/API_HASH=$API_HASH/" .env
    sed -i "s/ADMIN_IDS=.*/ADMIN_IDS=$ADMIN_IDS/" .env
    
    print_success "Bot credentials configured"
}

# Setup directories
setup_directories() {
    print_step "Creating necessary directories..."
    
    mkdir -p sessions logs temp_downloads
    chmod 755 sessions logs temp_downloads
    
    print_success "Directories created"
}

# Setup permissions
setup_permissions() {
    print_step "Setting up permissions..."
    
    # Make scripts executable
    chmod +x deploy.sh 2>/dev/null || true
    chmod +x quick-start.sh 2>/dev/null || true
    
    # Secure .env file
    chmod 600 .env
    
    print_success "Permissions configured"
}

# Start the bot
start_bot() {
    print_step "Starting Telegram Bot..."
    
    # Build and start
    docker-compose up -d --build
    
    if [ $? -eq 0 ]; then
        print_success "Bot started successfully!"
        
        # Wait a moment for startup
        sleep 5
        
        # Show status
        print_info "Bot Status:"
        docker-compose ps
        
        echo ""
        print_info "Useful commands:"
        echo -e "${BLUE}  ./deploy.sh logs    ${NC}# View logs"
        echo -e "${BLUE}  ./deploy.sh status  ${NC}# Check status"
        echo -e "${BLUE}  ./deploy.sh stop    ${NC}# Stop bot"
        echo -e "${BLUE}  ./deploy.sh restart ${NC}# Restart bot"
        
    else
        print_error "Failed to start bot!"
        print_info "Check logs with: docker-compose logs"
        exit 1
    fi
}

# Show final instructions
show_final_instructions() {
    echo ""
    echo -e "${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                    🎉 Setup Complete!                       ║${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${CYAN}Your Telegram Bot is now running!${NC}"
    echo ""
    echo -e "${YELLOW}Next steps:${NC}"
    echo -e "${BLUE}1.${NC} Go to your bot on Telegram and send /start"
    echo -e "${BLUE}2.${NC} Add userbot sessions using admin commands"
    echo -e "${BLUE}3.${NC} Test downloading with YouTube/Instagram URLs"
    echo ""
    echo -e "${YELLOW}Monitoring:${NC}"
    echo -e "${BLUE}• Logs:${NC} ./deploy.sh logs"
    echo -e "${BLUE}• Status:${NC} ./deploy.sh status"
    echo -e "${BLUE}• Stop:${NC} ./deploy.sh stop"
    echo ""
    echo -e "${YELLOW}Documentation:${NC}"
    echo -e "${BLUE}• Setup Guide:${NC} SETUP_GUIDE.md"
    echo -e "${BLUE}• Deployment Guide:${NC} DEPLOYMENT_GUIDE.md"
    echo -e "${BLUE}• README:${NC} README.md"
    echo ""
}

# Main execution
main() {
    print_banner
    
    # Check if running as root
    if [[ $EUID -eq 0 ]]; then
        print_warning "Running as root is not recommended!"
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
    
    # Execute setup steps
    check_requirements
    setup_environment
    setup_directories
    setup_permissions
    start_bot
    show_final_instructions
    
    print_success "Quick start completed successfully!"
}

# Handle interruption
trap 'echo -e "\n${RED}Setup interrupted!${NC}"; exit 1' INT

# Run main function
main "$@"