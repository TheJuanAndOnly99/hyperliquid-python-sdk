#!/bin/bash

# Quick start script for copy trading bot

echo "═══════════════════════════════════════════════════════════════"
echo "🚀 Starting Copy Trading Bot"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Check if account has funds
cd examples
poetry run python << 'EOF'
import json
from hyperliquid.info import Info
from hyperliquid.utils import constants

try:
    with open('config.json') as f:
        config = json.load(f)
    
    address = config.get("account_address")
    if not address:
        print("⚠️  No account address in config")
        exit()
    
    info = Info(base_url=constants.MAINNET_API_URL, skip_ws=True)
    user_state = info.user_state(address)
    account_value = float(user_state.get("marginSummary", {}).get("accountValue", "0"))
    
    if account_value == 0:
        print(f"⚠️  Your account has no funds (${account_value})")
        print("")
        print("Please fund your wallet at:")
        print("  https://hyperliquid.xyz")
        print("")
        print("Account: " + address)
        exit(1)
    else:
        print(f"✅ Account funded: ${account_value:,.2f}")
        print("🚀 Starting copy trading...")
except Exception as e:
    print(f"❌ Error: {e}")
    exit(1)
EOF

if [ $? -eq 0 ]; then
    echo ""
    poetry run python copy_trade.py
else
    echo ""
    echo "Please fund your wallet first, then run this script again."
fi

