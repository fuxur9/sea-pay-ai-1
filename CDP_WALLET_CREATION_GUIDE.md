# CDP Wallet Creation & Credentials Guide

## Understanding CDP Wallet Architecture

Your SeaPay application uses **Coinbase CDP Smart Wallet** which requires three types of credentials:

```
┌─────────────────────────────────────────────────────────────┐
│                    Your Application                          │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  AgentKit Wallet Manager                             │  │
│  │                                                       │  │
│  │  Credentials Required:                                │  │
│  │  1. CDP_API_KEY_ID        ←─────────────────────────┼──┼─── From CDP Portal
│  │  2. CDP_API_KEY_SECRET    ←─────────────────────────┼──┼─── From CDP Portal
│  │  3. PRIVATE_KEY (owner)   ←─────────────────────────┼──┼─── Your Ethereum key
│  │  4. CDP_WALLET_SECRET     ←─────────────────────────┼──┼─── Optional (auto-gen)
│  │  5. NETWORK_ID            ←─────────────────────────┼──┼─── base-sepolia
│  └──────────────────────────────────────────────────────┘  │
│                          ↓                                   │
│                    CDP Smart Wallet                          │
│              (Deployed on Base Sepolia)                      │
└─────────────────────────────────────────────────────────────┘
```

## Step-by-Step: Getting Your Credentials

### 1. Get CDP API Credentials

These authenticate your application with Coinbase's platform.

**How to get them:**

1. Visit: https://portal.cdp.coinbase.com/access/api
2. Sign in to your Coinbase Developer account
3. Click **"Create API Key"**
4. Copy both values:
   - `CDP_API_KEY_ID` (e.g., `63de72e1-318e-4aca-88eb-fc4c80035785`)
   - `CDP_API_KEY_SECRET` (long base64 string)

**Add to your `backend/.env`:**

```bash
CDP_API_KEY_ID=63de72e1-318e-4aca-88eb-fc4c80035785
CDP_API_KEY_SECRET=cSc5YdWXd9pLKoZVxb7YHDyJsN5Z1F0avtmTEE3TKib5KwfhKh+QrSUbCreofLAUxd7FDk8H7MB03TA4zt7kkg==
```

### 2. Get or Generate a Private Key (PRIVATE_KEY)

This is **your Ethereum private key** that will be the "owner" of the CDP Smart Wallet.

**Option A: Use MetaMask (Recommended for testing)**

1. Open MetaMask browser extension
2. Click the three dots → Account Details → Export Private Key
3. Enter your password
4. Copy the private key (starts with `0x`)

**Option B: Use an existing key**

If you already have an Ethereum private key from your x402 setup, you can use that.

**Option C: Generate a new one programmatically**

```bash
cd backend
python -c "from eth_account import Account; acc = Account.create(); print(f'Address: {acc.address}'); print(f'Private Key: {acc.key.hex()}')"
```

**Add to your `backend/.env`:**

```bash
PRIVATE_KEY=0xYourPrivateKeyHere1234567890abcdef...
```

### 3. CDP Wallet Secret (Optional)

The `CDP_WALLET_SECRET` is for **persistent wallet storage**.

**Two options:**

**Option A: Let AgentKit auto-create (Easier)**

- Leave `CDP_WALLET_SECRET` empty or omit it from `.env`
- AgentKit will create a new wallet automatically
- ⚠️ **Downside**: A new wallet is created each time you restart

**Option B: Create persistent wallet (Recommended)**

Run the setup script:

```bash
cd backend
python scripts/simple_wallet_setup.py
```

Or manually:

1. Start your app once without `CDP_WALLET_SECRET`
2. Check the logs for wallet creation
3. The wallet address will be logged
4. If you need persistence, use the wallet export feature (advanced)

### 4. Network ID

Set the blockchain network:

```bash
NETWORK_ID=base-sepolia  # For testnet (recommended for development)
# or
NETWORK_ID=base-mainnet  # For production (real money!)
```

## Complete .env Example

Your `backend/.env` file should look like this:

```bash
# OpenAI (for chat)
OPENAI_API_KEY=your_openai_api_key

# SeaPay API
SEAPAY_API_BASE_URL=your_api_url_if_needed

# Ethereum Private Key (owner of CDP wallet)
PRIVATE_KEY=0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef

# CDP API Credentials (from CDP Portal)
CDP_API_KEY_ID=63de72e1-318e-4aca-88eb-fc4c80035785
CDP_API_KEY_SECRET=cSc5YdWXd9pLKoZVxb7YHDyJsN5Z1F0avtmTEE3TKib5KwfhKh+QrSUbCreofLAUxd7FDk8H7MB03TA4zt7kkg==

# CDP Wallet Secret (optional - leave empty for auto-create)
CDP_WALLET_SECRET=

# Network Configuration
NETWORK_ID=base-sepolia
```

## Using the Helper Scripts

I've created two helper scripts for you:

### Script 1: Simple Wallet Setup Checker

Checks your current configuration and provides guidance:

```bash
cd /Users/fuchunhsieh/local-lab/sea-pay-ai/backend
python scripts/simple_wallet_setup.py
```

**What it does:**

- ✅ Verifies all required credentials are set
- ✅ Explains what each credential does
- ✅ Provides next steps
- ✅ Tests wallet manager import

### Script 2: CDP Wallet Creator (Advanced)

Creates a new CDP wallet and displays credentials:

```bash
cd /Users/fuchunhsieh/local-lab/sea-pay-ai/backend
python scripts/create_cdp_wallet.py
```

**What it does:**

- ✅ Creates a new CDP wallet on Base Sepolia
- ✅ Displays the wallet address
- ✅ Shows the CDP_WALLET_SECRET
- ✅ Requests test funds from faucet
- ✅ Displays balance

## Quick Start: Getting Your Wallet Running

### The Fastest Way (Recommended)

1. **Get CDP API credentials** from https://portal.cdp.coinbase.com/access/api

2. **Use your existing PRIVATE_KEY** (from your current `.env`)

3. **Update your `.env`:**

```bash
CDP_API_KEY_ID=your-api-key-id
CDP_API_KEY_SECRET=your-api-key-secret
PRIVATE_KEY=your-existing-private-key
NETWORK_ID=base-sepolia
# Leave CDP_WALLET_SECRET empty - it will auto-create
```

4. **Restart your backend:**

```bash
npm run dev
```

5. **Test it:**
   - Open http://localhost:5172
   - Say: "Show me my wallet status"
   - You should see your wallet card with real Base Sepolia balances!

## What Happens When Your App Starts

```
1. Backend starts
   ↓
2. Wallet Manager initializes
   ↓
3. Reads CDP_API_KEY_ID, CDP_API_KEY_SECRET, PRIVATE_KEY
   ↓
4. Creates CdpSmartWalletProviderConfig with these credentials
   ↓
5. Initializes CDP Smart Wallet
   ↓
6. Logs: "CDP Smart Wallet initialized successfully: 0x..."
   ↓
7. Ready to query balances and send transactions!
```

## Troubleshooting

### Error: "Missing required environment variables"

**Fix:** Make sure you have all three credentials in `.env`:

- `CDP_API_KEY_ID`
- `CDP_API_KEY_SECRET`
- `PRIVATE_KEY`

### Error: "Owner private key or CDP server wallet address is required"

**Fix:** The `PRIVATE_KEY` variable is missing or empty. Add it to `.env`.

### Error: "CDP wallet not initialized"

**Fix:** One of your credentials is invalid. Double-check:

1. CDP API credentials are correct (copy-paste from CDP Portal)
2. PRIVATE_KEY is a valid Ethereum private key (starts with `0x`, 66 chars total)

### Wallet balance shows 0.0 USDC

**This is normal for a new wallet!** To get test funds:

1. Copy your wallet address from the logs
2. Visit: https://portal.cdp.coinbase.com/faucet
3. Paste your address and request USDC
4. Wait 30-60 seconds
5. Check balance again: "What's my USDC balance?"

## Security Best Practices

### ⚠️ NEVER COMMIT CREDENTIALS TO GIT

Your `.env` file is in `.gitignore` - keep it that way!

### ✅ DO:

- Keep your `PRIVATE_KEY` secure
- Use testnet (base-sepolia) for development
- Never share your CDP API credentials
- Use environment variables for production

### ❌ DON'T:

- Commit `.env` to git
- Share private keys in chat/email
- Use real funds on testnet
- Use test keys in production

## Getting Test Funds

### Base Sepolia Faucets

**Option 1: CDP Portal Faucet** (Recommended)

- https://portal.cdp.coinbase.com/faucet
- Supports ETH and USDC
- No rate limits for verified accounts

**Option 2: Programmatic Faucet** (Already integrated)

```python
# This happens automatically in create_cdp_wallet.py
faucet_tx = wallet.faucet()
```

**Option 3: Community Faucets**

- https://www.alchemy.com/faucets/base-sepolia
- https://faucet.quicknode.com/base/sepolia

## FAQ

### Q: Do I need to create a wallet manually?

**A:** No! If you have the three required credentials (CDP_API_KEY_ID, CDP_API_KEY_SECRET, PRIVATE_KEY), the wallet will be created automatically when your app starts.

### Q: What's the difference between PRIVATE_KEY and CDP_WALLET_SECRET?

**A:**

- `PRIVATE_KEY`: Your Ethereum key that **controls** the smart wallet
- `CDP_WALLET_SECRET`: CDP's secret for **storing** wallet data persistently

Think of `PRIVATE_KEY` as your master key, and `CDP_WALLET_SECRET` as a storage token.

### Q: Can I use the same PRIVATE_KEY for multiple wallets?

**A:** Yes! The same private key can control multiple CDP smart wallets. Each wallet has a unique address but they're all controlled by your key.

### Q: Will my wallet address change when I restart?

**A:**

- **Without CDP_WALLET_SECRET**: Yes, new wallet each time
- **With CDP_WALLET_SECRET**: No, same wallet persists

### Q: How do I get real USDC on mainnet?

**A:**

1. Change `NETWORK_ID=base-mainnet` in `.env`
2. Buy USDC on Coinbase or another exchange
3. Withdraw to your wallet address on Base mainnet
4. ⚠️ Use real funds carefully!

## Summary

To create and use your CDP wallet:

1. ✅ **Get CDP API credentials** → https://portal.cdp.coinbase.com/access/api
2. ✅ **Use or generate PRIVATE_KEY** → Your Ethereum private key
3. ✅ **Update `.env` file** → Add the three credentials
4. ✅ **Run the helper script** → `python scripts/simple_wallet_setup.py`
5. ✅ **Start your backend** → `npm run dev`
6. ✅ **Test your wallet** → "Show me my wallet status"

Your wallet will be created automatically with your credentials. The helper scripts are there to verify your setup and provide guidance.

**You're all set! Your CDP Smart Wallet is ready to use! 🎉**

## Reference Links

- **CDP Portal**: https://portal.cdp.coinbase.com/
- **CDP Documentation**: https://docs.cdp.coinbase.com/server-wallets/v2/introduction/quickstart
- **Base Sepolia Explorer**: https://sepolia.basescan.org/
- **CDP Faucet**: https://portal.cdp.coinbase.com/faucet
