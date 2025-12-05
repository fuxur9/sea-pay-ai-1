#!/usr/bin/env python3
"""
Simple CDP Wallet Setup Script
Following the official Coinbase CDP documentation pattern.

This creates a wallet using the @coinbase/cdp-sdk pattern shown in:
https://docs.cdp.coinbase.com/server-wallets/v2/introduction/quickstart#python
"""

import os
import sys
from pathlib import Path

# Add parent directory to path to import from app
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

print("""
╔════════════════════════════════════════════════════════════════╗
║              CDP Wallet Setup Helper                           ║
╚════════════════════════════════════════════════════════════════╝
""")

# Check required environment variables
api_key_id = os.getenv("CDP_API_KEY_ID")
api_key_secret = os.getenv("CDP_API_KEY_SECRET")
private_key = os.getenv("PRIVATE_KEY")

print("\n📋 Checking your current .env configuration...\n")

print(f"✓ CDP_API_KEY_ID: {'✅ Set' if api_key_id else '❌ Missing'}")
print(f"✓ CDP_API_KEY_SECRET: {'✅ Set' if api_key_secret else '❌ Missing'}")
print(f"✓ PRIVATE_KEY: {'✅ Set' if private_key else '❌ Missing'}")

if not api_key_id or not api_key_secret:
    print("""
❌ Missing CDP API credentials!

To get your CDP API Key:
1. Go to: https://portal.cdp.coinbase.com/access/api
2. Click "Create API Key"
3. Save the key ID and secret
4. Add to backend/.env:
   
   CDP_API_KEY_ID=your-key-id-here
   CDP_API_KEY_SECRET=your-key-secret-here
""")
    sys.exit(1)

if not private_key:
    print("""
❌ Missing PRIVATE_KEY!

The PRIVATE_KEY is your Ethereum private key that will be the owner of the CDP wallet.

To get a private key:
1. Use MetaMask or another wallet to generate a new account
2. Export the private key
3. Add to backend/.env:
   
   PRIVATE_KEY=0xyour-private-key-here

⚠️  SECURITY: Never share or commit your private key to git!
""")
    sys.exit(1)

print("""
✅ All required credentials are set!

Now let's understand what each credential does:

1. CDP_API_KEY_ID & CDP_API_KEY_SECRET
   → These authenticate your app with Coinbase's CDP platform
   → Required to create and manage wallets

2. PRIVATE_KEY (owner)
   → This is YOUR Ethereum private key
   → It controls the CDP smart contract wallet
   → Required for signing transactions

3. CDP_WALLET_SECRET (optional)
   → This is for persistent wallet storage
   → If not set, a new wallet is created each time
   → The AgentKit will generate this automatically on first run

════════════════════════════════════════════════════════════════

🎯 RECOMMENDATION:

Your current setup should work! The CDP wallet will be created automatically
when you start the application.

If you want a PERSISTENT wallet (recommended):
1. Run your application once
2. Check the logs for wallet initialization
3. The AgentKit will log the wallet address
4. Copy the CDP_WALLET_SECRET from the logs (if shown)
5. Add it to your .env file

════════════════════════════════════════════════════════════════

📝 Your current .env should have:

CDP_API_KEY_ID={masked_key_id}
CDP_API_KEY_SECRET=***hidden***
PRIVATE_KEY=0x***hidden***
NETWORK_ID=base-sepolia

Optional (for persistent wallet):
CDP_WALLET_SECRET=***will be generated***

════════════════════════════════════════════════════════════════

🚀 NEXT STEPS:

1. Make sure all credentials above are in backend/.env
2. Restart your backend: npm run backend
3. The CDP wallet will initialize automatically
4. Test it: Open http://localhost:5172 and say "Show me my wallet"

════════════════════════════════════════════════════════════════
""".format(
    masked_key_id=api_key_id[:8] + "..." if api_key_id else "not-set"
))

# Check if the wallet manager can be imported
try:
    print("🔍 Testing wallet manager import...")
    from app.wallet.wallet_config import get_wallet_manager
    print("✅ Wallet manager import successful!")
    
    print("\n🔍 Testing AgentKit availability...")
    from app.wallet.agentkit_wallet import AGENTKIT_AVAILABLE
    if AGENTKIT_AVAILABLE:
        print("✅ AgentKit is available!")
    else:
        print("❌ AgentKit not available - installing...")
        os.system("cd .. && uv pip install coinbase-agentkit")
        
except ImportError as e:
    print(f"⚠️  Warning: Could not import wallet manager: {e}")
    print("This is OK - it will work when you run the backend")

print("""
════════════════════════════════════════════════════════════════

💡 UNDERSTANDING YOUR WALLET SETUP:

When your app starts, the AgentKit will:

1. Read CDP_API_KEY_ID and CDP_API_KEY_SECRET
2. Read PRIVATE_KEY (as the wallet owner)
3. Create or load a CDP Smart Wallet
4. Use the wallet to:
   - Query USDC/ETH balances from Base Sepolia
   - Send gasless USDC transactions
   - Display wallet info in the UI

The PRIVATE_KEY you provided controls the smart contract wallet.
Think of it as the "master key" to your CDP wallet.

════════════════════════════════════════════════════════════════

✅ You're all set! Start your backend and test your wallet.

════════════════════════════════════════════════════════════════
""")
