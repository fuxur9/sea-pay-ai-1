# Environment Variables Fix - CDP Configuration

## Issue

The AgentKit library expects different environment variable names than what was originally configured.

## Required Changes to Your `.env` File

You need to rename the following variables in `/Users/fuchunhsieh/local-lab/sea-pay-ai/backend/.env`:

### Variable Name Changes

| Old Variable Name (❌ Remove) | New Variable Name (✅ Use)     |
| ----------------------------- | ------------------------------ |
| `CDP_API_KEY_NAME`            | `CDP_API_KEY_ID`               |
| `CDP_API_KEY_PRIVATE_KEY`     | `CDP_API_KEY_SECRET`           |
| `CDP_WALLET_DATA`             | `CDP_WALLET_SECRET`            |
| `CDP_WALLET_ID`               | `CDP_WALLET_SECRET`            |
| `CDP_NETWORK_ID`              | `NETWORK_ID` (already correct) |

## How to Fix

### Option 1: Manual Update

Edit your `/Users/fuchunhsieh/local-lab/sea-pay-ai/backend/.env` file and rename the variables:

```bash
# BEFORE (Old names)
CDP_API_KEY_NAME=your_key_name
CDP_API_KEY_PRIVATE_KEY=your_private_key
CDP_WALLET_ID=your_wallet_id
CDP_WALLET_SECRET=your_wallet_secret

# AFTER (Correct names)
CDP_API_KEY_ID=your_key_name
CDP_API_KEY_SECRET=your_private_key
CDP_WALLET_SECRET=your_wallet_secret
```

### Option 2: Automated Fix (Recommended)

Run this command to automatically rename the variables:

```bash
cd /Users/fuchunhsieh/local-lab/sea-pay-ai/backend

# Backup your current .env file
cp .env .env.backup

# Update variable names
sed -i '' 's/CDP_API_KEY_NAME=/CDP_API_KEY_ID=/g' .env
sed -i '' 's/CDP_API_KEY_PRIVATE_KEY=/CDP_API_KEY_SECRET=/g' .env
sed -i '' 's/CDP_WALLET_ID=/CDP_WALLET_SECRET=/g' .env
sed -i '' 's/CDP_NETWORK_ID=/NETWORK_ID=/g' .env

# Remove CDP_WALLET_DATA if it exists (use CDP_WALLET_SECRET instead)
grep -v "CDP_WALLET_DATA=" .env > .env.tmp && mv .env.tmp .env
```

## After Fixing

1. The backend will automatically reload
2. The wallet will initialize with CDP Smart Wallet
3. You'll be able to see real balances from Base Sepolia network

## Verification

After updating, check the logs. You should see:

```
INFO: [WALLET] CDP Smart Wallet initialized successfully: 0x...
```

Instead of:

```
ERROR: [WALLET] Failed to initialize CDP Smart Wallet: Missing required environment variables
INFO: [WALLET] Falling back to private key wallet
```

## Getting CDP Credentials

If you don't have CDP credentials yet:

1. Visit https://portal.cdp.coinbase.com/access/api
2. Create a new API key
3. Download the credentials JSON file
4. Use the values from the JSON:
   - `name` → `CDP_API_KEY_ID`
   - `privateKey` → `CDP_API_KEY_SECRET`

## Network Configuration

Ensure you have:

```bash
NETWORK_ID=base-sepolia
```

This tells the wallet to connect to Base Sepolia testnet.

## Wallet Secret

The `CDP_WALLET_SECRET` is used to persist your wallet across restarts. If you don't have one:

1. Leave it empty on first run - AgentKit will create a wallet and log the secret
2. Copy the secret from the logs
3. Add it to your `.env` file to persist the wallet

## Summary

The fix ensures that the wallet manager correctly:

- ✅ Initializes CDP Smart Wallet provider
- ✅ Connects to Base Sepolia network
- ✅ Fetches real USDC and ETH balances
- ✅ Enables gasless USDC transfers
