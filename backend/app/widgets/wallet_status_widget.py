"""
Widget helpers for presenting wallet status information.
"""

from __future__ import annotations

from typing import Any

from chatkit.widgets import WidgetRoot, WidgetTemplate

wallet_status_widget_template = WidgetTemplate.from_file("wallet_status.widget")


def build_wallet_status_widget(wallet_info: dict[str, Any]) -> WidgetRoot:
    """
    Render a wallet status widget using the .widget template.
    
    Args:
        wallet_info: Dictionary with wallet information:
            - address: Wallet address
            - network: Network ID (e.g., "base-sepolia")
            - usdc_balance: USDC balance as float
            - eth_balance: ETH balance as float
            - gasless_enabled: Whether gasless transfers are enabled
            - wallet_type: Type of wallet (e.g., "CDP" or "Private Key")
    """
    # Format the address for display (first 6 and last 4 chars)
    address = wallet_info.get("address", "Unknown")
    short_address = f"{address[:6]}...{address[-4:]}" if len(address) > 10 else address
    
    # Format balances
    usdc_balance = wallet_info.get("usdc_balance", 0)
    eth_balance = wallet_info.get("eth_balance", 0)
    usdc_str = f"{usdc_balance:.6f} USDC"
    eth_str = f"{eth_balance:.6f} ETH"
    
    # Network and wallet type
    network = wallet_info.get("network", "unknown")
    wallet_type = wallet_info.get("wallet_type", "Unknown")
    gasless_enabled = wallet_info.get("gasless_enabled", False)
    
    payload = {
        "address": address,
        "shortAddress": short_address,
        "network": network,
        "usdcBalance": usdc_str,
        "ethBalance": eth_str,
        "walletType": wallet_type,
        "gaslessEnabled": gasless_enabled,
    }
    
    return wallet_status_widget_template.build(payload)
