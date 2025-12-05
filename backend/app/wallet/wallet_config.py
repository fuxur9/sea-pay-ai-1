"""
Wallet configuration module with singleton pattern.

This module provides a singleton instance of the AgentKitWalletManager
to ensure consistent wallet state across the application.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

_wallet_manager: Optional["AgentKitWalletManager"] = None


def get_wallet_manager() -> "AgentKitWalletManager":
    """
    Get or create the singleton wallet manager instance.
    
    Returns:
        AgentKitWalletManager: The singleton wallet manager instance
    """
    global _wallet_manager
    
    if _wallet_manager is None:
        from .agentkit_wallet import AgentKitWalletManager
        _wallet_manager = AgentKitWalletManager()
        logger.info("[WALLET] Wallet manager initialized")
    
    return _wallet_manager


def reset_wallet_manager() -> None:
    """
    Reset the wallet manager singleton.
    
    This is useful for testing or when configuration changes.
    Call this after updating CDP credentials in .env to force re-initialization.
    """
    global _wallet_manager
    if _wallet_manager is not None:
        logger.info("[WALLET] Resetting wallet manager to force re-initialization")
    _wallet_manager = None


def is_cdp_wallet_active() -> bool:
    """
    Check if the current wallet is a CDP Smart Wallet (not fallback).
    
    Returns:
        bool: True if CDP Smart Wallet is active, False if using fallback
    """
    global _wallet_manager
    if _wallet_manager is None:
        return False
    return _wallet_manager.wallet_provider is not None
