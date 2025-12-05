"""
Wallet management module using Coinbase AgentKit.

This module provides wallet management capabilities for the SeaPay agent,
including balance checking, USDC transfers, and transaction history.
"""

from .wallet_config import get_wallet_manager
from .agentkit_wallet import AgentKitWalletManager

__all__ = ["get_wallet_manager", "AgentKitWalletManager"]
