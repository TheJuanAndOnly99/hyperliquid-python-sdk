# 24/7 Copy Trading Setup Guide

This guide will help you set up the copy trading bot to run continuously 24/7 on your Mac with automatic restarts and proper logging.

## 📋 Overview

The 24/7 system includes:
- **Wrapper Script**: Auto-restarts the bot if it crashes
- **macOS Daemon**: Runs the bot as a background service that starts on boot
- **Error Recovery**: Handles network issues, API errors, and other failures gracefully
- **Logging**: Comprehensive logs for debugging and monitoring

## 🚀 Quick Setup (3 Steps)

### Step 1: Configure Your Settings

Edit `examples/copy_trade.py` and set your preferences:

```python
# ===== CONFIGURATION =====
TARGET_WALLET = "0xc20ac4dc4188660cbf555448af52694ca62b0734"
AUTO_CALCULATE = True   # Automatically calculate copy percentage
CHECK_INTERVAL = 5      # Check every 5 seconds for better sync
```

**Recommended Settings:**
- For better sync: `CHECK_INTERVAL = 5` (checks every 5 seconds)
- For lower CPU: `CHECK_INTERVAL = 10` (checks every 10 seconds)

### Step 2: Install the Service

Run the setup script:

```bash
cd /Users/juan/Desktop/hyperliquid-python-sdk
./examples/setup_24_7_service.sh
```

This will:
- ✅ Create the logs directory
- ✅ Install the macOS service (launchd)
- ✅ Start the service automatically
- ✅ Configure auto-restart on crashes

### Step 3: Verify It's Running

Check the service status:

```bash
launchctl list | grep com.hyperliquid.copytrader
```

View the logs:

```bash
tail -f /Users/juan/Desktop/hyperliquid-python-sdk/examples/logs/service_output.log
```

## 📊 Monitoring

### View Live Logs

**Main output:**
```bash
tail -f examples/logs/service_output.log
```

**Errors:**
```bash
tail -f examples/logs/service_error.log
```

**Copy trading logs:**
```bash
tail -f examples/copy_trade.log
```

### Check Service Health

```bash
# Check if service is running
launchctl list | grep com.hyperliquid.copytrader

# Check recent system logs
log show --predicate 'process == "launchd"' --last 10m | grep copytrader
```

## 🔧 Service Management

### Start the Service
```bash
launchctl load ~/Library/LaunchAgents/com.hyperliquid.copytrader.plist
```

### Stop the Service
```bash
launchctl unload ~/Library/LaunchAgents/com.hyperliquid.copytrader.plist
```

### Restart the Service
```bash
launchctl unload ~/Library/LaunchAgents/com.hyperliquid.copytrader.plist && \
launchctl load ~/Library/LaunchAgents/com.hyperliquid.copytrader.plist
```

### Remove the Service Completely
```bash
launchctl unload ~/Library/LaunchAgents/com.hyperliquid.copytrader.plist && \
rm ~/Library/LaunchAgents/com.hyperliquid.copytrader.plist
```

### Check Status
```bash
# Show all running services (look for copytrader)
launchctl list | grep copytrader

# Get detailed info
launchctl print system/com.hyperliquid.copytrader
```

## ⚙️ Configuration

### Check Interval (Sync Speed)

Edit `examples/copy_trade.py`:

```python
CHECK_INTERVAL = 5   # Check every 5 seconds (fastest sync)
CHECK_INTERVAL = 10  # Check every 10 seconds (balanced)
CHECK_INTERVAL = 30  # Check every 30 seconds (low CPU)
```

**Recommended**: 5-10 seconds for best sync with minimal lag.

### Copy Percentage

The bot automatically calculates the copy percentage based on your account values:

```python
AUTO_CALCULATE = True  # Uses your_account / target_account
```

Or set a manual percentage:

```python
AUTO_CALCULATE = False
COPY_PERCENTAGE = 0.01  # Copy 1% of target's positions
```

## 🛡️ Safety Features

### Automatic Restart
- If the bot crashes, it automatically restarts within 60 seconds
- Maximum 100 restarts per hour (prevents infinite loops)
- After 100 restarts, it stops and requires manual intervention

### Error Handling
- Catches and logs all errors
- Continues running even if individual API calls fail
- Multiple consecutive errors cause graceful shutdown (prevents spam)

### Logging
- All actions logged to files
- Separate logs for errors
- Timestamp on every log entry
- Easy to debug issues

## 📱 Alternative: Run in Background Manually

If you prefer not to use the system service, you can run the wrapper script directly:

```bash
# Run in background with output redirected
nohup ./examples/run_copy_trader.sh > examples/logs/manual_run.log 2>&1 &

# Check if running
ps aux | grep copy_trade

# Stop it
pkill -f copy_trade.py
```

## 🔍 Troubleshooting

### Service Won't Start

1. Check logs:
```bash
cat ~/Library/LaunchAgents/com.hyperliquid.copytrader.plist
```

2. Check permissions:
```bash
ls -la examples/run_copy_trader.sh
chmod +x examples/run_copy_trader.sh
```

3. Check if Poetry is in PATH:
```bash
which poetry
```

### Bot Keeps Crashing

1. Check the error logs:
```bash
tail -f examples/logs/service_error.log
```

2. Check the main log:
```bash
tail -f examples/copy_trade.log
```

3. Common issues:
   - **Network errors**: API timeout - will retry automatically
   - **API rate limits**: Will back off and retry
   - **Insufficient funds**: Check your account balance
   - **Invalid configuration**: Check config.json

### Not Copying Trades

1. Verify target wallet has activity:
```bash
poetry run python examples/track_wallet.py
```

2. Check your account balance:
```bash
# Your account needs funds to copy trades
```

3. Check confirmation prompts:
   - The bot may be waiting for 'y' confirmation
   - Check if there's a terminal waiting for input

### CPU Usage Too High

Reduce check frequency:

```python
CHECK_INTERVAL = 30  # Check every 30 seconds instead of 5
```

Or run on specific schedules:

```bash
# Edit the plist to add StartCalendarInterval
# This runs the bot only at specific times
```

## 📊 Performance Tips

### Best Sync (Fast Execution)
- Set `CHECK_INTERVAL = 5`
- Use faster internet connection
- Run on a machine with good uptime
- Monitor logs regularly

### Lower Resource Usage
- Set `CHECK_INTERVAL = 30` or higher
- Disable user confirmation prompts (edit the code)
- Use limit orders instead of market orders (more complex)

### Balancing
- Set `CHECK_INTERVAL = 10` for good sync and reasonable CPU
- Monitor logs daily
- Check account status weekly

## 🔒 Security

### Protecting Your Keys

1. **Never share your config.json file**
2. **Use environment variables** for sensitive data:
```bash
export HYPERLIQUID_SECRET_KEY="0x..."
```

3. **File permissions**:
```bash
chmod 600 examples/config.json
```

### System Security

- Run on a trusted network
- Use VPN if connecting remotely
- Keep system updated
- Use strong passwords
- Monitor logs for suspicious activity

## 📈 Monitoring Performance

### Track Your Results

Compare your performance vs target:

1. **Track target performance**:
```bash
poetry run python examples/track_wallet.py
```

2. **Track your performance**:
   - Check your Hyperliquid dashboard
   - Review account value changes
   - Monitor position sizes

3. **Expected results**:
   - Copy percentage: Your trades should be proportional to your account size
   - Example: If target makes $100 profit and you have 1% copy, you should see ~$1 profit

### Key Metrics

- **Sync Time**: How quickly trades are copied
- **Success Rate**: % of trades that execute successfully  
- **Slippage**: Difference between target price and your execution price
- **Overall PnL**: Your total profit/loss vs target's

## 🎯 Advanced Configuration

### Custom Sync Interval

Edit `examples/com.hyperliquid.copytrader.plist`:

```xml
<key>StartInterval</key>
<integer>300</integer>  <!-- Run every 5 minutes -->
```

### Scheduled Trading

Only run during market hours:

```xml
<key>StartCalendarInterval</key>
<dict>
    <key>Hour</key>
    <integer>9</integer>
    <key>Minute</key>
    <integer>0</integer>
</dict>
```

### Multiple Bots

To track multiple wallets, create separate plist files:

```bash
# Copy the plist
cp com.hyperliquid.copytrader.plist com.hyperliquid.copytrader2.plist

# Edit the paths and settings
# Then load both services
```

## ⚠️ Important Notes

1. **First Time Setup**: Make sure your wallet has funds before starting
2. **Testing**: Run for a day before committing to 24/7
3. **Monitoring**: Check logs daily for the first week
4. **Backups**: Keep backups of your config.json
5. **Updates**: Update the SDK regularly for security patches

## 📞 Support

If you encounter issues:

1. Check the logs first
2. Review the troubleshooting section
3. Verify your configuration
4. Check your internet connection
5. Ensure your wallet has sufficient funds

## 🎉 Success Checklist

- [ ] Bot is running (check with `launchctl list`)
- [ ] Logs are being written
- [ ] No errors in logs
- [ ] Trades are being copied (check account activity)
- [ ] Service starts on boot (test reboot)
- [ ] Auto-restart works (test by killing the process)

Happy copy trading! 🚀

