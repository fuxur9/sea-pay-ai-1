"""
Coinbase AgentKit wallet integration layer.

This module provides wallet management capabilities using Coinbase AgentKit.
It supports both CDP Smart Wallet Provider and fallback to private key wallets.
"""

import asyncio
import logging
import os
from typing import Any, Optional
from threading import Lock

from eth_account import Account

# Try to import AgentKit and wallet providers
try:
    from coinbase_agentkit import (
        AgentKit,
        AgentKitConfig,
        CdpSmartWalletProvider,
        CdpSmartWalletProviderConfig,
        EthAccountWalletProvider,
        EthAccountWalletProviderConfig,
    )
    AGENTKIT_AVAILABLE = True
except ImportError as e:
    logger_temp = logging.getLogger(__name__)
    logger_temp.warning(f"AgentKit not available: {e}. Falling back to private key wallet only.")
    AGENTKIT_AVAILABLE = False
    AgentKit = None  # type: ignore
    AgentKitConfig = None  # type: ignore
    CdpSmartWalletProvider = None  # type: ignore
    CdpSmartWalletProviderConfig = None  # type: ignore
    EthAccountWalletProvider = None  # type: ignore
    EthAccountWalletProviderConfig = None  # type: ignore

logger = logging.getLogger(__name__)


class AgentKitWalletManager:
    """
    Manages wallet operations using Coinbase AgentKit.
    
    Supports both CDP Smart Wallet Provider and local private key wallets
    for backward compatibility with x402.
    """

    def __init__(self):
        """Initialize wallet manager with configuration from environment."""
        self.agentkit: Optional[AgentKit] = None
        self.wallet_provider = None
        self._fallback_account: Optional[Account] = None
        self._network_id: str = os.getenv("NETWORK_ID", "base-sepolia")
        self._initialization_attempted = False
        self._initialization_success = False  # Track if initialization succeeded
        self._initialization_lock = Lock()  # Thread-safe initialization
        self._cdp_credentials = self._get_cdp_credentials()
        # Don't initialize here - will be done lazily on first use
        # This avoids event loop conflicts during module import

    def _get_cdp_credentials(self) -> dict[str, Optional[str]]:
        """Get CDP credentials from environment variables."""
        return {
            "api_key_id": os.getenv("CDP_API_KEY_ID"),
            "api_key_secret": os.getenv("CDP_API_KEY_SECRET"),
            "wallet_secret": os.getenv("CDP_WALLET_SECRET"),
            "owner_private_key": os.getenv("PRIVATE_KEY"),
        }
    
    async def _ensure_initialized(self) -> None:
        """Ensure wallet is initialized (lazy initialization, thread-safe)."""
        # Double-check locking pattern for thread safety
        if self._initialization_success:
            return  # Already successfully initialized
        
        with self._initialization_lock:
            # Check again after acquiring lock
            if self._initialization_success:
                return
            
            # Allow retry if previous attempt failed
            if not self._initialization_attempted:
                self._initialization_attempted = True
                await self._initialize_wallet_async()
    
    async def _initialize_wallet_async(self) -> None:
        """Initialize wallet provider based on configuration (async version)."""
        try:
            # Check if AgentKit is available
            if not AGENTKIT_AVAILABLE:
                logger.warning("[WALLET] AgentKit not available, using fallback private key wallet")
                self._initialize_fallback_wallet()
                return
            
            # Get credentials
            cdp_api_key_id = self._cdp_credentials["api_key_id"]
            cdp_api_key_secret = self._cdp_credentials["api_key_secret"]
            cdp_wallet_secret = self._cdp_credentials["wallet_secret"]
            owner_private_key = self._cdp_credentials["owner_private_key"]
            
            if cdp_api_key_id and cdp_api_key_secret and owner_private_key:
                # Use CDP Smart Wallet Provider
                logger.info("[WALLET] Initializing CDP Smart Wallet...")
                
                try:
                    # Ensure private key has 0x prefix
                    if not owner_private_key.startswith("0x"):
                        owner_private_key = "0x" + owner_private_key
                    
                    # Create wallet provider in a thread to avoid event loop conflicts
                    loop = asyncio.get_running_loop()
                    
                    def _create_wallet():
                        """Create CDP wallet in a separate context."""
                        # Build config - if wallet_secret is None, a new wallet will be created
                        config_params = {
                            "api_key_id": cdp_api_key_id,
                            "api_key_secret": cdp_api_key_secret,
                            "owner": owner_private_key,
                            "network_id": self._network_id,
                        }
                        
                        # Only add wallet_secret if it's provided
                        if cdp_wallet_secret:
                            config_params["wallet_secret"] = cdp_wallet_secret
                        
                        wallet_config = CdpSmartWalletProviderConfig(**config_params)
                        provider = CdpSmartWalletProvider(config=wallet_config)
                        
                        # Log the wallet secret for persistence (if newly created)
                        if not cdp_wallet_secret:
                            try:
                                # Try to get the wallet data for persistence
                                wallet_data = provider.export_wallet()
                                if wallet_data and hasattr(wallet_data, 'seed'):
                                    logger.info(
                                        f"[WALLET] New wallet created! To persist this wallet, "
                                        f"add to your .env file:\n"
                                        f"CDP_WALLET_SECRET={wallet_data.seed}"
                                    )
                            except Exception as e:
                                logger.debug(f"[WALLET] Could not export wallet data: {e}")
                        
                        return provider
                    
                    # Run in thread pool to avoid event loop conflicts
                    self.wallet_provider = await loop.run_in_executor(None, _create_wallet)
                    
                    # Create AgentKit instance
                    agentkit_config = AgentKitConfig(
                        wallet_provider=self.wallet_provider,
                        action_providers=[],  # Can add action providers later
                    )
                    self.agentkit = AgentKit(config=agentkit_config)
                    
                    self._initialization_success = True  # Mark as successful
                    logger.info(
                        f"[WALLET] CDP Smart Wallet initialized successfully: "
                        f"{self.get_wallet_address()}"
                    )
                except Exception as e:
                    error_msg = str(e)
                    logger.error(f"[WALLET] Failed to initialize CDP Smart Wallet: {error_msg}")
                    
                    # Don't retry if it's a "multiple wallets" error - need CDP_WALLET_SECRET
                    if "Multiple smart wallets" in error_msg:
                        logger.error(
                            "[WALLET] A wallet already exists with this owner. "
                            "To reuse it, you need to set CDP_WALLET_SECRET in your .env file. "
                            "Check the logs from the first successful initialization for the secret."
                        )
                    
                    logger.info("[WALLET] Falling back to private key wallet")
                    self._initialize_fallback_wallet()
            else:
                # Fallback to private key wallet
                logger.warning(
                    "[WALLET] CDP credentials incomplete. "
                    "Required: CDP_API_KEY_ID, CDP_API_KEY_SECRET, PRIVATE_KEY (owner). "
                    "Using fallback private key wallet."
                )
                self._initialize_fallback_wallet()
                
        except Exception as e:
            logger.error(f"[WALLET] Failed to initialize wallet: {e}")
            logger.info("[WALLET] Falling back to private key wallet")
            self._initialize_fallback_wallet()

    def _initialize_fallback_wallet(self) -> None:
        """Initialize fallback wallet using private key."""
        private_key = os.getenv("PRIVATE_KEY")
        if not private_key:
            logger.warning(
                "[WALLET] No wallet configuration found. Set CDP credentials "
                "(CDP_API_KEY_NAME, CDP_API_KEY_PRIVATE_KEY) or PRIVATE_KEY"
            )
            return
        
        if not private_key.startswith("0x"):
            private_key = "0x" + private_key
        
        self._fallback_account = Account.from_key(private_key)
        logger.info(f"[WALLET] Fallback wallet initialized: {self._fallback_account.address}")

    def get_wallet_address(self) -> str:
        """
        Get the wallet address.
        
        Returns:
            str: The wallet address
        """
        # Note: This is synchronous, initialization should happen via async methods first
        if self.wallet_provider:
            return self.wallet_provider.get_address()
        elif self._fallback_account:
            return self._fallback_account.address
        else:
            raise ValueError("No wallet configured")

    def get_network_id(self) -> str:
        """
        Get the configured network ID.
        
        Returns:
            str: The network ID (e.g., 'base-sepolia', 'base-mainnet')
        """
        return self._network_id

    async def get_balance(self, asset_id: str = "usdc") -> dict[str, Any]:
        """
        Get wallet balance for specified asset.
        
        Args:
            asset_id: The asset ID to check balance for (default: "usdc")
            
        Returns:
            dict: Balance information with asset_id, balance, and formatted_balance
        """
        await self._ensure_initialized()
        
        try:
            if not AGENTKIT_AVAILABLE or not self.wallet_provider:
                raise ValueError(
                    "CDP wallet not initialized. Balance checking only supported with CDP wallet. "
                    "Please configure CDP credentials (CDP_API_KEY_ID, CDP_API_KEY_SECRET, "
                    "CDP_WALLET_SECRET, PRIVATE_KEY) and ensure coinbase-agentkit package is installed."
                )
            
            # Get balance from wallet provider
            # Note: CdpSmartWalletProvider.get_balance() takes asset_id as positional arg
            balance = self.wallet_provider.get_balance(asset_id)
            balance_float = float(balance) if balance else 0.0
            
            return {
                "success": True,
                "asset_id": asset_id.upper(),
                "balance": balance_float,
                "formatted_balance": f"{balance_float:.6f} {asset_id.upper()}",
            }
        except Exception as e:
            logger.error(f"[WALLET] Failed to get balance: {e}")
            return {
                "success": False,
                "error": str(e),
                "asset_id": asset_id,
                "balance": 0,
                "formatted_balance": "0 " + asset_id.upper(),
            }

    async def get_wallet_info(self) -> dict[str, Any]:
        """
        Get comprehensive wallet information.
        
        Returns:
            dict: Wallet information including address, network, balances, and gasless status
        """
        await self._ensure_initialized()
        
        try:
            address = self.get_wallet_address()
            network = self.get_network_id()
            
            # Get USDC balance
            usdc_balance_info = await self.get_balance("usdc")
            usdc_balance = usdc_balance_info.get("balance", 0)
            
            # Get ETH balance (gas token for Base)
            eth_balance_info = await self.get_balance("eth")
            eth_balance = eth_balance_info.get("balance", 0)
            
            # Gasless USDC is available on Base networks with CDP
            gasless_enabled = "base" in network.lower() and self.wallet_provider is not None
            
            return {
                "success": True,
                "address": address,
                "network": network,
                "usdc_balance": usdc_balance,
                "eth_balance": eth_balance,
                "gasless_enabled": gasless_enabled,
                "wallet_type": "CDP Smart Wallet" if self.wallet_provider else "Private Key",
                "message": (
                    f"Wallet: {address}\n"
                    f"Network: {network}\n"
                    f"USDC Balance: {usdc_balance:.6f} USDC\n"
                    f"ETH Balance: {eth_balance:.6f} ETH\n"
                    f"Gasless Transfers: {'Enabled' if gasless_enabled else 'Disabled'}"
                ),
            }
        except Exception as e:
            logger.error(f"[WALLET] Failed to get wallet info: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to retrieve wallet information: {str(e)}",
            }

    async def transfer_usdc(
        self,
        destination_address: str,
        amount_usdc: float,
        memo: Optional[str] = None,
        gasless: bool = True,
    ) -> dict[str, Any]:
        """
        Transfer USDC to another address.
        
        Args:
            destination_address: The recipient address
            amount_usdc: Amount of USDC to transfer
            memo: Optional memo/note for the transfer
            gasless: Whether to use gasless transfer (default: True on Base)
            
        Returns:
            dict: Transfer result with transaction hash and details
        """
        await self._ensure_initialized()
        
        try:
            if not AGENTKIT_AVAILABLE or not self.wallet_provider:
                raise ValueError(
                    "CDP wallet not initialized. USDC transfers only supported with CDP wallet. "
                    "Please configure CDP credentials (CDP_API_KEY_NAME, CDP_API_KEY_PRIVATE_KEY) "
                    "and ensure coinbase-agentkit package is installed."
                )
            
            logger.info(
                f"[WALLET] Transferring {amount_usdc} USDC to {destination_address} "
                f"(gasless: {gasless})"
            )
            
            # Perform the transfer using wallet provider
            tx_hash = self.wallet_provider.transfer(
                to=destination_address,
                amount=str(amount_usdc),
                asset_id="usdc",
            )
            
            logger.info(f"[WALLET] Transfer completed: {tx_hash}")
            
            return {
                "success": True,
                "transaction_hash": tx_hash,
                "amount": amount_usdc,
                "currency": "USDC",
                "destination": destination_address,
                "network": self._network_id,
                "status": "confirmed",
                "memo": memo,
                "message": (
                    f"Successfully transferred {amount_usdc} USDC to {destination_address}\n"
                    f"Transaction: {tx_hash}"
                ),
            }
        except Exception as e:
            logger.error(f"[WALLET] Transfer failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "amount": amount_usdc,
                "currency": "USDC",
                "destination": destination_address,
                "network": self._network_id,
                "status": "failed",
                "message": f"Transfer failed: {str(e)}",
            }

    async def get_transaction_history(self, limit: int = 10) -> dict[str, Any]:
        """
        Get recent transaction history.
        
        Args:
            limit: Maximum number of transactions to return
            
        Returns:
            dict: Transaction history with list of transactions
        """
        try:
            if not AGENTKIT_AVAILABLE or not self.wallet_provider:
                raise ValueError(
                    "CDP wallet not initialized. Transaction history only supported with CDP wallet. "
                    "Please configure CDP credentials and ensure coinbase-agentkit package is installed."
                )
            
            # Note: Transaction history API may vary by wallet provider
            # This is a placeholder - actual implementation depends on wallet provider API
            logger.warning("[WALLET] Transaction history not yet implemented for AgentKit wallet provider")
            
            return {
                "success": True,
                "transactions": [],
                "count": 0,
                "message": "Transaction history feature coming soon",
            }
        except Exception as e:
            logger.error(f"[WALLET] Failed to get transaction history: {e}")
            return {
                "success": False,
                "error": str(e),
                "transactions": [],
                "count": 0,
                "message": f"Failed to retrieve transaction history: {str(e)}",
            }

    def export_wallet_data(self) -> dict[str, Any]:
        """
        Export wallet data for backup.
        
        WARNING: This exposes sensitive information. Use with caution.
        
        Returns:
            dict: Wallet data for backup
        """
        try:
            if not AGENTKIT_AVAILABLE or not self.wallet_provider:
                return {
                    "success": False,
                    "error": "CDP wallet not initialized",
                    "message": "Wallet export only supported with CDP wallet. Please configure CDP credentials.",
                }
            
            # Note: Export functionality depends on wallet provider API
            logger.warning("[WALLET] Wallet export not yet implemented for AgentKit wallet provider")
            
            return {
                "success": False,
                "message": "Wallet export feature coming soon. Please save your API keys and wallet ID securely.",
            }
        except Exception as e:
            logger.error(f"[WALLET] Failed to export wallet: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to export wallet: {str(e)}",
            }
