# 📱 Notification System

The copy trading bot now sends macOS notifications for all important events!

## 🔔 What You'll Be Notified About

### 1. **Startup Notification** 
When the bot starts tracking the wallet:
- **Title**: "🚀 Copy Trading Active"
- **Sound**: Default
- Shows wallet address and copy percentage

### 2. **Target Move Detected** 🎯
When the target wallet makes a trade:
- **Title**: "🎯 Target Wallet: [COIN] [BOUGHT/SOLD]"
- **Message**: Size and direction of the trade
- **Sound**: Glass (attention-grabbing)
- Example: "Target Wallet: ETH BOUGHT - Size: +0.1000"

### 3. **Trade Executed Successfully** ✅
When your trade is successfully placed:
- **Title**: "✅ Trade Executed: [COIN] [BUY/SELL]"
- **Message**: Size and estimated dollar value
- **Sound**: Purr (success sound)
- Example: "Trade Executed: ETH BUY - Size: 0.0047 | Value: ~$19.69"

### 4. **Trade Failed** ❌
When a trade fails to execute:
- **Title**: "❌ Trade Failed: [COIN] [BUY/SELL]"
- **Message**: Error reason
- **Sound**: Basso (error sound)
- Example: "Trade Failed: BTC BUY - Error: Insufficient margin"

### 5. **Position Closed** 🔔
When target closes a position:
- **Title**: "🔔 Position Closed: [COIN]"
- **Message**: "Target closed position. Closing yours too..."
- **Sound**: Glass

## 🎛️ Enabling/Disabling Notifications

Edit `examples/copy_trade.py`:

```python
# In the main() function:
ENABLE_NOTIFICATIONS = True   # Set to False to disable
```

Or pass it when creating the trader:

```python
trader = CopyTrader(
    target_wallet=TARGET_WALLET,
    enable_notifications=True  # or False
)
```

## 🧪 Test Your Notifications

Test that notifications work on your system:

```bash
poetry run python examples/test_notifications.py
```

This will send 4 test notifications to verify everything is working.

## 📲 macOS Notification Settings

If notifications aren't showing up:

### 1. Check System Preferences
```
System Preferences → Notifications → [Your Terminal App]
```
Enable:
- ✅ Allow notifications
- ✅ Show in Notification Center
- ✅ Play sound

### 2. Check Do Not Disturb
Make sure Do Not Disturb isn't enabled during the day.

### 3. Check Focus Mode
On macOS Monterey+, Focus modes can silence notifications.

## 🔊 Notification Sounds

Different sounds for different events:

| Event | Sound | When |
|-------|-------|------|
| Startup | default | Bot starts |
| Target move | Glass | Target makes a trade |
| Trade success | Purr | Your trade executed |
| Trade failed | Basso | Your trade failed |

## 📊 Example Notification Flow

When the target wallet trades ETH:

1. **9:00 AM** - 🎯 "Target Wallet: ETH BOUGHT"
   - You get notified immediately
   - Bot starts processing your copy trade

2. **9:00:02 AM** - ✅ "Trade Executed: ETH BUY"
   - Your trade was successfully placed
   - Shows size and dollar value

Or if there's an error:

1. **9:00 AM** - 🎯 "Target Wallet: ETH BOUGHT"
2. **9:00:02 AM** - ❌ "Trade Failed: ETH BUY"
   - Error: Insufficient margin
   - You need to add funds to your account

## 🚨 Real-Time Trading

### Live Trading Scenario

**Scenario**: Target wallet buys 5 ETH at $4,200

You'll receive:

```
1. 🎯 Target Wallet: ETH BOUGHT
   Size: +5.7400 | Copying BUY order...
   [Sound: Glass]

2. [In terminal, you're asked to confirm]
   ⚠️  Execute this trade? (y/n/q)

3. ✅ Trade Executed: ETH BUY
   Size: 0.0270 | Value: ~$113.40
   [Sound: Purr]
```

**Timeline**:
- **0s**: Target places order → You get notified 🎯
- **2s**: Bot calculates your copy trade size
- **3s**: Terminal asks for your confirmation (if interactive mode)
- **5s**: You type 'y' to execute
- **7s**: Your trade executes → Success notification ✅

## 🔕 Disable Notifications

If notifications are distracting:

### Method 1: Edit Config
```python
# In copy_trade.py
ENABLE_NOTIFICATIONS = False
```

### Method 2: System-Wide
Disable Terminal notifications:
```
System Preferences → Notifications → Terminal → Allow Notifications (OFF)
```

## ⚙️ Customizing Notification Sounds

You can change the sounds in the code:

```python
# In place_copy_order method:
send_notification(
    title=f"🎯 Target Wallet: {coin} {action}",
    message=f"Size: {size_text}",
    sound="Glass"  # Change to: "default", "Purr", "Funk", etc.
)
```

Available macOS sounds:
- default
- Glass
- Purr
- Basso
- Funk
- Submarine
- And more!

## 📱 Mobile Notifications (Future)

For iOS/Android push notifications, you can integrate:
- **Pushover**: Easy API-based push notifications
- **Telegram Bot**: Send messages to Telegram
- **Email**: SMTP for important alerts

Example with Telegram (needs bot setup):

```python
import requests

def send_telegram(message):
    bot_token = "YOUR_BOT_TOKEN"
    chat_id = "YOUR_CHAT_ID"
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": message})
```

## 🎯 Pro Tips

1. **Keep sound on**: Glass/Purr sounds help you notice important events
2. **Check notifications regularly**: Review logs weekly
3. **Disable at night**: Set ENABLE_NOTIFICATIONS to False during sleep hours
4. **Use for monitoring**: Great for checking if the bot is working

## 🔍 Troubleshooting

### No notifications appearing?

1. **Check terminal permissions**: Ensure Terminal app has notification permissions
2. **Test with the test script**: Run `test_notifications.py`
3. **Check Do Not Disturb**: Disable if enabled
4. **Restart the service**: Reinstall the daemon
5. **Check logs**: Look for "Could not send notification" errors

### Notifications showing but no sound?

1. Check system volume
2. Check notification sound setting
3. Verify Terminal notifications aren't muted

### Too many notifications?

Reduce the check interval:
```python
CHECK_INTERVAL = 30  # Check less frequently
```

This reduces how often you're notified of trades.

## 🎉 Benefits

✅ **Instant alerts**: Know immediately when target trades
✅ **Track execution**: See when your trades succeed or fail
✅ **Stay informed**: Monitor bot activity without checking logs
✅ **Error awareness**: Get notified when something goes wrong

---

**Now you'll never miss a trade! 🚀**

