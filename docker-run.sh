#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}YouTube Downloader Docker Setup${NC}"
echo "------------------------------"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Docker is not installed. Please install Docker first.${NC}"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}Docker Compose is not installed. Please install Docker Compose first.${NC}"
    exit 1
fi

# Function to build and start containers
start_app() {
    echo -e "${YELLOW}Building and starting containers...${NC}"
    docker-compose up -d --build
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Application is running!${NC}"
        echo -e "Access the application at: ${GREEN}http://localhost:8000${NC}"
        echo -e "View logs with: ${YELLOW}docker-compose logs -f${NC}"
    else
        echo -e "${RED}Failed to start the application.${NC}"
    fi
}

# Function to stop containers
stop_app() {
    echo -e "${YELLOW}Stopping containers...${NC}"
    docker-compose down
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Containers stopped successfully.${NC}"
    else
        echo -e "${RED}Failed to stop containers.${NC}"
    fi
}

# Function to show logs
show_logs() {
    echo -e "${YELLOW}Showing application logs (press Ctrl+C to exit)...${NC}"
    docker-compose logs -f
}

# Function to show help
show_help() {
    echo "Usage: ./docker-run.sh [OPTION]"
    echo "Options:"
    echo "  start    Build and start the application"
    echo "  stop     Stop the application"
    echo "  restart  Restart the application"
    echo "  logs     Show application logs"
    echo "  help     Show this help message"
}

# Parse command line arguments
case "$1" in
    start)
        start_app
        ;;
    stop)
        stop_app
        ;;
    restart)
        stop_app
        start_app
        ;;
    logs)
        show_logs
        ;;
    help|*)
        show_help
        ;;
esac
