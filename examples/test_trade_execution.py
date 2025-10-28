#!/usr/bin/env python3
"""
Test Trade Execution
Execute a small test trade to verify everything works
"""

import json
import example_utils
from hyperliquid.utils import constants

def main():
    print("="*80)
    print("🧪 TESTING TRADE EXECUTION")
    print("="*80)
    print()
    
    # Get your account info
    address, info, exchange = example_utils.setup(base_url=constants.MAINNET_API_URL, skip_ws=True)
    
    # Get current account value
    user_state = info.user_state(address)
    account_value = float(user_state.get("marginSummary", {}).get("accountValue", "0"))
    
    print(f"Account: {address}")
    print(f"Account value: ${account_value:,.2f}")
    print()
    
    if account_value == 0:
        print("❌ No funds in account!")
        print("Please fund your account first at https://hyperliquid.xyz")
        return
    
    # Get current prices
    print("📊 Getting current prices...")
    mids = info.all_mids()
    
    # Ask user for trading parameters
    print()
    print("="*80)
    print("⚙️  TEST TRADE CONFIGURATION")
    print("="*80)
    print()
    
    # Available coins
    available_coins = ["BTC", "SOL", "ETH", "BNB", "HYPE", "DOGE", "XRP"]
    print("Available assets:")
    for i, coin in enumerate(available_coins, 1):
        if coin in info.name_to_coin:
            coin_data = info.name_to_coin[coin]
            price = mids.get(coin_data, "N/A")
            if price != "N/A":
                print(f"   {i}. {coin}: ${float(price):,.2f}")
            else:
                print(f"   {i}. {coin}: Not available")
    
    print()
    
    # Ask for asset
    while True:
        try:
            choice = input("Select asset (1-7) or type name (e.g. BTC): ").strip()
            if choice.isdigit():
                asset = available_coins[int(choice) - 1]
            else:
                asset = choice.upper()
            
            if asset in available_coins and asset in info.name_to_coin:
                test_coin = asset
                break
            else:
                print(f"❌ Invalid asset. Choose from: {', '.join(available_coins)}")
        except (ValueError, IndexError, KeyError):
            print(f"❌ Invalid choice. Try again.")
    
    print(f"✅ Selected: {test_coin}")
    
    coin_data = info.name_to_coin[test_coin]
    price = float(mids.get(coin_data, 0))
    
    if price == 0:
        print(f"❌ Could not get price for {test_coin}")
        return
    
    print()
    print(f"📊 {test_coin} Current Price: ${price:,.2f}")
    print()
    
    # Ask for leverage
    while True:
        try:
            lev_input = input("Leverage (1-50x, typical 10x): ").strip()
            leverage = float(lev_input)
            if 1 <= leverage <= 50:
                leverage = int(leverage)
                break
            else:
                print("❌ Leverage must be between 1-50")
        except ValueError:
            print("❌ Enter a valid number")
    
    print(f"✅ Leverage: {leverage}x")
    print()
    
    # Ask for position size (USD value)
    while True:
        try:
            value_input = input("Position size in USD (minimum $5): $").strip().replace('$', '').replace(',', '')
            test_value = float(value_input)
            if test_value >= 5:
                break
            else:
                print("❌ Minimum position size is $5")
        except ValueError:
            print("❌ Enter a valid number")
    
    # Calculate trade parameters
    test_size = test_value / price
    test_size = round(test_size, 4)
    margin_required = test_value / leverage
    liquidation_price_long = price * (1 - 1/leverage)
    liquidation_price_short = price * (1 + 1/leverage)
    
    print()
    print("="*80)
    print(f"📋 TRADE SUMMARY")
    print("="*80)
    print(f"   Coin: {test_coin}")
    print(f"   Position Size: {test_size}")
    print(f"   Leverage: {leverage}x")
    print(f"   Margin Required: ${margin_required:,.2f}")
    print(f"   Liquidation (long): ${liquidation_price_long:,.2f} (-{(1/leverage)*100:.1f}%)")
    print(f"   Liquidation (short): ${liquidation_price_short:,.2f} (+{(1/leverage)*100:.1f}%)")
    print("="*80)
    print()
    
    response = input("Execute this test trade? (yes/no): ").lower().strip()
    
    if response not in ['yes', 'y']:
        print("Test trade cancelled.")
        return
    
    print()
    print(f"📤 Setting leverage to {leverage}x...")
    
    try:
        # Set leverage for cross margin
        leverage_result = exchange.update_leverage(
            leverage=leverage,
            name=test_coin,
            is_cross=True
        )
        
        if leverage_result.get("status") == "ok":
            print(f"✅ Leverage set to {leverage}x")
        else:
            print(f"⚠️  Leverage update: {leverage_result.get('response', {}).get('data', {}).get('statuses', [{}])[0]}")
        
        print("📤 Placing test trade...")
        
        # Place market buy order
        result = exchange.market_open(
            test_coin,
            is_buy=True,
            sz=test_size,
            slippage=0.05  # 5% slippage for test
        )
        
        print()
        print("="*80)
        print("📊 TRADE RESULT")
        print("="*80)
        print()
        
        if result.get("status") == "ok":
            print("✅ Trade executed successfully!")
            print()
            print("Trade details:")
            status = result["response"]["data"]["statuses"][0]
            print(json.dumps(status, indent=2))
            print()
            print("This means:")
            print("✅ Your bot can execute trades")
            print("✅ API wallet has gas (HYPE)")
            print("✅ Account wallet has funds")
            print("✅ Everything is working!")
            print()
            print("You can now start copy trading!")
        else:
            print("❌ Trade failed:")
            print(json.dumps(result, indent=2))
            print()
            print("Common issues:")
            print("• API wallet needs HYPE for gas")
            print("• Insufficient balance")
            print("• Market closed or illiquid")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

