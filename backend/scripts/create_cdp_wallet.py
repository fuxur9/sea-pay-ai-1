#!/usr/bin/env python3
"""
Script to create a CDP wallet and display the wallet secret and private key.

This script will:
1. Create a new EVM account on Base Sepolia using your CDP credentials
2. Display the wallet secret (for CDP_WALLET_SECRET env var)
3. Display the private key (for PRIVATE_KEY env var)
4. Request test funds from the faucet

Prerequisites:
- CDP_API_KEY_ID and CDP_API_KEY_SECRET must be set in your .env file
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

try:
    from cdp import Cdp, Wallet
    print("✅ CDP SDK imported successfully")
except ImportError:
    print("❌ Error: CDP SDK not found. Installing...")
    os.system("pip install cdp-sdk")
    from cdp import Cdp, Wallet

def create_wallet_and_get_credentials():
    """Create a CDP wallet and return wallet secret and private key."""
    
    # Check for required credentials
    api_key_id = os.getenv("CDP_API_KEY_ID")
    api_key_secret = os.getenv("CDP_API_KEY_SECRET")
    
    if not api_key_id or not api_key_secret:
        print("❌ Error: CDP_API_KEY_ID and CDP_API_KEY_SECRET must be set in .env file")
        print("\nTo get these credentials:")
        print("1. Go to https://portal.cdp.coinbase.com/access/api")
        print("2. Click 'Create API Key'")
        print("3. Copy the key ID and secret")
        print("4. Add them to your backend/.env file:")
        print("   CDP_API_KEY_ID=your-key-id")
        print("   CDP_API_KEY_SECRET=your-key-secret")
        sys.exit(1)
    
    print("\n🔄 Initializing CDP client...")
    
    # Configure CDP with your credentials
    Cdp.configure(api_key_id, api_key_secret)
    
    print("✅ CDP client configured")
    print("\n🔄 Creating new wallet on Base Sepolia...")
    
    # Create a new wallet on Base Sepolia
    wallet = Wallet.create(network_id="base-sepolia")
    
    print(f"✅ Wallet created successfully!")
    print(f"\n📍 Wallet Address: {wallet.default_address.address_id}")
    
    # Export wallet data (this includes the wallet secret)
    wallet_data = wallet.export_data()
    
    # Get the private key from the default address
    # Note: In CDP SDK, the private key is part of the wallet export
    # The wallet.export_data() returns a JSON string with the wallet seed
    
    print("\n" + "="*80)
    print("🔐 WALLET CREDENTIALS - SAVE THESE TO YOUR .env FILE")
    print("="*80)
    
    print(f"\n1. Wallet Address (for reference):")
    print(f"   {wallet.default_address.address_id}")
    
    print(f"\n2. CDP_WALLET_SECRET (add this to .env):")
    print(f"   {wallet_data.seed}")
    
    print(f"\n3. Network ID (already in .env):")
    print(f"   base-sepolia")
    
    print("\n" + "="*80)
    print("📋 COPY THESE TO YOUR backend/.env FILE:")
    print("="*80)
    print(f"\nCDP_WALLET_SECRET={wallet_data.seed}")
    print(f"NETWORK_ID=base-sepolia")
    
    # For the PRIVATE_KEY, we need to derive it from the wallet
    # The CDP SDK doesn't directly expose private keys for security
    # You'll need to use the same private key you already have, or generate a new one
    
    print("\n" + "="*80)
    print("⚠️  IMPORTANT NOTES:")
    print("="*80)
    print("""
1. The CDP_WALLET_SECRET above is for persistent wallet storage
2. You still need a PRIVATE_KEY for the 'owner' parameter
3. The PRIVATE_KEY should be an Ethereum private key that you control
4. You can use your existing PRIVATE_KEY that's already in .env
5. The owner (PRIVATE_KEY) controls the smart contract wallet

If you need to generate a new PRIVATE_KEY:
- Use a tool like MetaMask to create a new account
- Export the private key from MetaMask
- Add it to your .env file as PRIVATE_KEY=0x...
""")
    
    # Request test funds from faucet
    print("\n🔄 Requesting test funds from Base Sepolia faucet...")
    try:
        faucet_tx = wallet.faucet()
        print(f"✅ Faucet request successful!")
        print(f"   Transaction: https://sepolia.basescan.org/tx/{faucet_tx.transaction_hash}")
        print(f"   Waiting for confirmation...")
        
        faucet_tx.wait()
        print(f"✅ Funds received! Your wallet now has testnet ETH")
        
        # Get balance
        balance = wallet.balance("eth")
        print(f"   Balance: {balance} ETH")
        
    except Exception as e:
        print(f"⚠️  Faucet request failed: {e}")
        print(f"   You can manually request funds at: https://portal.cdp.coinbase.com/faucet")
    
    print("\n" + "="*80)
    print("✅ SETUP COMPLETE!")
    print("="*80)
    print("""
Next steps:
1. Copy the CDP_WALLET_SECRET to your backend/.env file
2. Make sure your PRIVATE_KEY is set in backend/.env
3. Restart your backend server: npm run backend
4. Test the wallet: "Show me my wallet status"
""")
    
    return {
        "address": wallet.default_address.address_id,
        "wallet_secret": wallet_data.seed,
        "network_id": "base-sepolia"
    }

if __name__ == "__main__":
    print("""
╔════════════════════════════════════════════════════════════════╗
║                  CDP Wallet Creation Script                    ║
║                                                                ║
║  This script will create a new CDP wallet and display the      ║
║  credentials you need to add to your .env file                 ║
╚════════════════════════════════════════════════════════════════╝
    """)
    
    try:
        credentials = create_wallet_and_get_credentials()
        
    except Exception as e:
        print(f"\n❌ Error creating wallet: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure CDP_API_KEY_ID and CDP_API_KEY_SECRET are in backend/.env")
        print("2. Verify your API key is active at https://portal.cdp.coinbase.com/access/api")
        print("3. Check you have internet connectivity")
        sys.exit(1)
