#!/bin/bash

#############################################################
# Setup Script for 24/7 Copy Trading Service
# This installs the copy trading bot as a macOS daemon
#############################################################

set -e

# Configuration
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PLIST_FILE="$SCRIPT_DIR/com.hyperliquid.copytrader.plist"
HOME_DIR=~
SERVICE_NAME="com.hyperliquid.copytrader"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "=================================================="
echo "🔧 Hyperliquid Copy Trading Service Setup"
echo "=================================================="
echo ""

# Check if running as root
if [ "$EUID" -eq 0 ]; then 
   echo -e "${RED}Error: Do not run as root. This script will handle permissions.${NC}"
   exit 1
fi

# Step 1: Update plist file with correct paths
echo "📝 Step 1: Configuring service paths..."
SED_ESCAPED_DIR=$(echo "$SCRIPT_DIR" | sed 's/\//\\\//g')
SED_ESCAPED_HOME=$(echo "$HOME_DIR" | sed 's/\//\\\//g')

sed -i.bak "s/\/Users\/juan\/Desktop\/hyperliquid-python-sdk\/examples/$SED_ESCAPED_DIR/g" "$PLIST_FILE"
sed -i.bak "s/\/Users\/juan/$SED_ESCAPED_HOME/g" "$PLIST_FILE"

echo "   ✅ Paths configured:"
echo "      - Script: $SCRIPT_DIR"
echo "      - Home: $HOME_DIR"

# Step 2: Create logs directory
echo ""
echo "📁 Step 2: Creating logs directory..."
mkdir -p "$SCRIPT_DIR/logs"
echo "   ✅ Logs directory: $SCRIPT_DIR/logs"

# Step 3: Test the configuration
echo ""
echo "🧪 Step 3: Testing configuration..."
if [ ! -f "$SCRIPT_DIR/copy_trade.py" ]; then
    echo -e "${RED}Error: copy_trade.py not found in $SCRIPT_DIR${NC}"
    exit 1
fi

if [ ! -f "$SCRIPT_DIR/run_copy_trader.sh" ]; then
    echo -e "${RED}Error: run_copy_trader.sh not found in $SCRIPT_DIR${NC}"
    exit 1
fi

echo "   ✅ All required files found"

# Step 4: Install the service
echo ""
echo "📥 Step 4: Installing the service..."

# Stop if already running
if launchctl list | grep -q "$SERVICE_NAME"; then
    echo "   ⏹️  Stopping existing service..."
    launchctl unload "$HOME_DIR/Library/LaunchAgents/$SERVICE_NAME.plist" 2>/dev/null || true
    launchctl remove "$SERVICE_NAME" 2>/dev/null || true
fi

# Copy plist to LaunchAgents
echo "   📋 Copying service file..."
cp "$PLIST_FILE" "$HOME_DIR/Library/LaunchAgents/"
chmod 644 "$HOME_DIR/Library/LaunchAgents/$SERVICE_NAME.plist"

# Load the service
echo "   🚀 Starting service..."
launchctl load "$HOME_DIR/Library/LaunchAgents/$SERVICE_NAME.plist"
sleep 2

# Check status
if launchctl list | grep -q "$SERVICE_NAME"; then
    echo -e "   ${GREEN}✅ Service installed and running!${NC}"
    echo ""
    echo "📊 Service Status:"
    launchctl list | grep "$SERVICE_NAME" || echo "   Status check..."
else
    echo -e "   ${YELLOW}⚠️  Service may still be starting...${NC}"
fi

# Step 5: Show commands
echo ""
echo "=================================================="
echo "✅ Setup Complete!"
echo "=================================================="
echo ""
echo "📋 Useful Commands:"
echo ""
echo "   View logs:"
echo "   tail -f $SCRIPT_DIR/logs/service_output.log"
echo ""
echo "   Check status:"
echo "   launchctl list | grep $SERVICE_NAME"
echo ""
echo "   Stop service:"
echo "   launchctl unload $HOME_DIR/Library/LaunchAgents/$SERVICE_NAME.plist"
echo ""
echo "   Start service:"
echo "   launchctl load $HOME_DIR/Library/LaunchAgents/$SERVICE_NAME.plist"
echo ""
echo "   Restart service:"
echo "   launchctl unload $HOME_DIR/Library/LaunchAgents/$SERVICE_NAME.plist && launchctl load $HOME_DIR/Library/LaunchAgents/$SERVICE_NAME.plist"
echo ""
echo "   Remove service:"
echo "   launchctl unload $HOME_DIR/Library/LaunchAgents/$SERVICE_NAME.plist && rm $HOME_DIR/Library/LaunchAgents/$SERVICE_NAME.plist"
echo ""

