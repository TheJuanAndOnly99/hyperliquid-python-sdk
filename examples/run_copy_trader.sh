#!/bin/bash

#############################################################
# Auto-Restart Wrapper for Copy Trading Bot
# This script ensures the copy trading bot stays running 24/7
# with automatic restart on crashes or errors
#############################################################

# Configuration
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PYTHON_SCRIPT="$SCRIPT_DIR/copy_trade.py"
LOG_FILE="$SCRIPT_DIR/copy_trade.log"
ERROR_LOG="$SCRIPT_DIR/copy_trade_errors.log"
MAX_RESTARTS=100  # Maximum consecutive restarts before stopping
RESTART_DELAY=5   # Seconds to wait before restarting
CHECK_INTERVAL=5  # Check interval in seconds (update in Python script too)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to log messages
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $*" | tee -a "$ERROR_LOG"
    log "[ERROR] $*"
}

log_info() {
    echo -e "${GREEN}[INFO]${NC} $*" | tee -a "$LOG_FILE"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $*" | tee -a "$LOG_FILE"
}

# Create logs directory if it doesn't exist
mkdir -p "$SCRIPT_DIR/logs"

# Track restarts
restart_count=0
last_restart=0

# Main loop
while true; do
    # Check if we've hit max restarts
    current_time=$(date +%s)
    if [ $restart_count -ge $MAX_RESTARTS ]; then
        log_error "Maximum restart limit ($MAX_RESTARTS) reached. Stopping to prevent infinite loop."
        log_error "Please check the logs and fix any issues before restarting."
        exit 1
    fi
    
    # Reset restart count if 1 hour has passed
    if [ $((current_time - last_restart)) -gt 3600 ]; then
        restart_count=0
    fi
    
    log_info "Starting copy trading bot..."
    log_info "Restart count: $restart_count"
    
    # Run the Python script
    cd "$SCRIPT_DIR" || exit 1
    poetry run python "$PYTHON_SCRIPT" 2>&1 | tee -a "$LOG_FILE"
    
    # Capture exit code
    exit_code=$?
    
    # Log the exit
    log_info "Copy trading bot exited with code: $exit_code"
    
    # Check if it was a graceful shutdown (Ctrl+C)
    if [ $exit_code -eq 130 ]; then
        log_info "Graceful shutdown requested. Exiting."
        exit 0
    fi
    
    # Increment restart count
    restart_count=$((restart_count + 1))
    last_restart=$current_time
    
    # Log restart
    log_warn "Copy trading bot crashed. Restarting in $RESTART_DELAY seconds... (Restart #$restart_count)"
    
    # Wait before restarting
    sleep $RESTART_DELAY
done

