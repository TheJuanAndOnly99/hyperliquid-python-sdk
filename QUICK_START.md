# 🚀 Quick Start - Copy Trading 24/7

Follow these steps to get your copy trading bot running 24/7.

## Prerequisites ✅

- Python 3.9+ installed
- Poetry installed
- Hyperliquid account with funds
- Target wallet address to copy

## Step 1: Test Your Configuration (Optional but Recommended)

```bash
cd /Users/juan/Desktop/hyperliquid-python-sdk
poetry run python examples/test_copy_trader.py
```

Expected: All 5 tests should pass ✅

## Step 2: Configure Your Target Wallet

Edit `examples/copy_trade.py`:

```python
# ===== CONFIGURATION =====
TARGET_WALLET = "0xc20ac4dc4188660cbf555448af52694ca62b0734"  # Already set
AUTO_CALCULATE = True   # Automatically calculate copy percentage
CHECK_INTERVAL = 5      # Check every 5 seconds for best sync
```

**Note**: The wallet `0xc20ac4dc4188660cbf555448af52694ca62b0734` is already configured.

## Step 3: Fund Your Wallet

Visit [Hyperliquid](https://hyperliquid.xyz) and deposit funds to your account.

**Recommended**: Start with $100-500 for testing.

## Step 4: Install and Start the 24/7 Service

```bash
cd /Users/juan/Desktop/hyperliquid-python-sdk
./examples/setup_24_7_service.sh
```

This will:
- ✅ Create logs directory
- ✅ Install the macOS background service
- ✅ Start the bot automatically
- ✅ Configure auto-restart on crashes

## Step 5: Verify It's Running

Check status:
```bash
launchctl list | grep com.hyperliquid.copytrader
```

View logs:
```bash
tail -f examples/logs/service_output.log
```

## Step 6: Monitor Your Account

Track the target wallet:
```bash
poetry run python examples/track_wallet.py
```

This shows you what the target is doing and what you're copying.

## 📱 Notifications

You'll receive macOS notifications for:
- 🎯 **Target makes a trade** (immediate alert)
- ✅ **Your trade executed** (success notification)
- ❌ **Trade failed** (error notification)
- 🔔 **Positions closed** (target closes a position)

**Test notifications:**
```bash
poetry run python examples/test_notifications.py
```

**Read more:** `examples/NOTIFICATIONS.md`

## 📊 Monitoring Commands

### View Live Activity
```bash
# Main log
tail -f examples/logs/service_output.log

# Errors only
tail -f examples/logs/service_error.log

# Trading activity
tail -f examples/copy_trade.log
```

### Check Service Status
```bash
# Is it running?
launchctl list | grep com.hyperliquid.copytrader

# What does it show?
launchctl list | grep copytrader
```

### Stop the Service (if needed)
```bash
launchctl unload ~/Library/LaunchAgents/com.hyperliquid.copytrader.plist
```

### Start the Service Again
```bash
launchctl load ~/Library/LaunchAgents/com.hyperliquid.copytrader.plist
```

## 🎯 Understanding the Output

When you view the logs, you'll see:

```
📊 Position change detected for ETH:
   Previous size: 0.0
   Current size:  5.74
   Change: +5.740000
   Copy size: 0.0270 (0.47% of change)
   Direction: BUY
   Estimated value: $113.00

⚠️  Execute this trade? (y/n/q for quit):
```

- **Previous size**: Target's old position
- **Current size**: Target's new position  
- **Change**: Difference (+ means they bought, - means they sold)
- **Copy size**: How much YOU will trade (proportional to your account)
- **Direction**: BUY or SELL
- **Estimated value**: Dollar value of YOUR trade

Type `y` to execute, `n` to skip, or `q` to quit.

## ⚙️ Adjusting Settings

### Want Faster Sync?
Edit `examples/copy_trade.py`:
```python
CHECK_INTERVAL = 3  # Check every 3 seconds (very fast)
```

### Want Lower CPU Usage?
```python
CHECK_INTERVAL = 30  # Check every 30 seconds (slower but uses less CPU)
```

### Want Different Copy Percentage?
```python
AUTO_CALCULATE = False
COPY_PERCENTAGE = 0.005  # Copy 0.5% of target's positions
```

## ⚠️ Important Notes

1. **Your account needs funds** to copy trades
2. **The bot asks for confirmation** before each trade (type `y`)
3. **Copy percentage is auto-calculated** based on your account size
4. **Service auto-restarts** if it crashes
5. **Logs are saved** for debugging

## 🔥 Common Issues

### "No funds in account"
- Visit Hyperliquid and deposit funds
- Wait a few minutes for funds to clear
- Re-run the test

### "Service not starting"
```bash
# Check the service file exists
ls ~/Library/LaunchAgents/com.hyperliquid.copytrader.plist

# Re-install
./examples/setup_24_7_service.sh
```

### "Not copying trades"
1. Check logs: `tail -f examples/logs/service_output.log`
2. Check if target has activity: `poetry run python examples/track_wallet.py`
3. Verify your account has funds
4. Check that you're responding to prompts (`y` to execute)

## 🎉 Success Indicators

You'll know it's working when:
- ✅ Service shows "0" in status (running without errors)
- ✅ Logs show "Position change detected" messages
- ✅ Logs show "Order placed successfully"
- ✅ Your Hyperliquid account shows trades
- ✅ Trades appear in your dashboard

## 📞 Need Help?

1. Check the full guide: `examples/24_7_SETUP_GUIDE.md`
2. Check troubleshooting: `examples/COPY_TRADING_GUIDE.md`
3. View error logs: `tail -f examples/logs/service_error.log`
4. Run the test: `poetry run python examples/test_copy_trader.py`

## 🎯 Next Steps After Setup

1. **Monitor for 24 hours** to ensure stability
2. **Check your first trades** on Hyperliquid dashboard
3. **Compare results** with target wallet
4. **Adjust settings** if needed (copy percentage, check interval)
5. **Review logs weekly** to ensure everything is working

---

**Ready to go?** Run `./examples/setup_24_7_service.sh` now! 🚀

