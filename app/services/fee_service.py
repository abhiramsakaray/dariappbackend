"""
Transaction Fee Calculation Service
Handles platform fees, gas fees, and international transaction fees
"""

from decimal import Decimal
from typing import Dict, Optional
from app.core.config import settings


class FeeService:
    """Service for calculating transaction fees"""
    
    # Meta-transaction mode: DARI pays all gas fees for users
    GASLESS_MODE = True  # Set to False to charge users for gas fees
    
    # Platform fee percentages
    DOMESTIC_FEE_PERCENT = Decimal("0.01")  # 1% for domestic transactions
    INTERNATIONAL_FEE_PERCENT = Decimal("0.02")  # 2% for international transactions
    
    # Minimum and maximum fees (in USD equivalent)
    MIN_PLATFORM_FEE = Decimal("0.10")  # $0.10 minimum
    MAX_PLATFORM_FEE = Decimal("50.00")  # $50.00 maximum
    
    # Fee-free threshold (transactions below this are free)
    FREE_THRESHOLD = Decimal("1.00")  # Transactions < $1 are free
    
    @staticmethod
    def calculate_platform_fee(
        amount: Decimal,
        is_international: bool = False,
        token_price_usd: Decimal = Decimal("1.0")
    ) -> Decimal:
        """
        Calculate platform fee based on transaction amount and type
        
        Args:
            amount: Transaction amount in token units
            is_international: Whether transaction is international
            token_price_usd: Current price of token in USD
            
        Returns:
            Platform fee in token units
        """
        # Calculate USD value
        amount_usd = amount * token_price_usd
        
        # Free for small transactions
        if amount_usd < FeeService.FREE_THRESHOLD:
            return Decimal("0")
        
        # Calculate fee percentage
        fee_percent = (
            FeeService.INTERNATIONAL_FEE_PERCENT 
            if is_international 
            else FeeService.DOMESTIC_FEE_PERCENT
        )
        
        # Calculate fee in USD
        fee_usd = amount_usd * fee_percent
        
        # Apply min/max limits
        fee_usd = max(FeeService.MIN_PLATFORM_FEE, min(fee_usd, FeeService.MAX_PLATFORM_FEE))
        
        # Convert back to token units
        fee_tokens = fee_usd / token_price_usd if token_price_usd > 0 else Decimal("0")
        
        # Round to token decimals (6 for USDC, 18 for MATIC)
        return fee_tokens.quantize(Decimal("0.000001"))
    
    @staticmethod
    def estimate_gas_fee(
        token: str,
        estimated_gas: int = 21000
    ) -> Dict[str, Decimal]:
        """
        Estimate gas fee for transaction
        
        Args:
            token: Token symbol (USDC, MATIC)
            estimated_gas: Estimated gas units
            
        Returns:
            Dictionary with gas estimates
        """
        # Gas price in Gwei (approximate Polygon gas prices)
        # Polygon is much cheaper than Ethereum
        gas_price_gwei = Decimal("30")  # 30 Gwei average on Polygon
        
        # For token transfers (ERC20), gas is higher
        if token in ["USDC"]:
            estimated_gas = 65000  # ERC20 transfer uses more gas
        
        # Calculate gas fee in MATIC
        gas_fee_matic = (
            Decimal(str(estimated_gas)) * 
            gas_price_gwei / 
            Decimal("1000000000")  # Convert Gwei to MATIC
        )
        
        return {
            "estimated_gas": Decimal(str(estimated_gas)),
            "gas_price_gwei": gas_price_gwei,
            "gas_fee_matic": gas_fee_matic,
            "gas_fee_usd": gas_fee_matic * Decimal("0.50")  # Approximate MATIC price
        }
    
    @staticmethod
    def calculate_total_fee(
        amount: Decimal,
        token: str,
        is_international: bool = False,
        token_price_usd: Decimal = Decimal("1.0"),
        estimated_gas: Optional[int] = None,
        gasless: Optional[bool] = None
    ) -> Dict[str, Decimal]:
        """
        Calculate total transaction fee (platform + gas)
        
        Args:
            amount: Transaction amount
            token: Token symbol
            is_international: International transaction flag
            token_price_usd: Token price in USD
            estimated_gas: Estimated gas units
            gasless: Override gasless mode (if None, uses FeeService.GASLESS_MODE)
            
        Returns:
            Dictionary with fee breakdown
        """
        # Determine if gasless mode is enabled
        is_gasless = FeeService.GASLESS_MODE if gasless is None else gasless
        
        # Calculate platform fee
        platform_fee = FeeService.calculate_platform_fee(
            amount, is_international, token_price_usd
        )
        
        # Estimate gas fee
        gas_estimates = FeeService.estimate_gas_fee(token, estimated_gas or 21000)
        
        # Convert gas fee to token units
        if token == "MATIC":
            gas_fee_tokens = gas_estimates["gas_fee_matic"]
        else:
            # For USDC, convert MATIC gas fee to USD
            gas_fee_tokens = gas_estimates["gas_fee_usd"] / token_price_usd
        
        # In gasless mode, user doesn't pay gas fee (DARI covers it)
        user_gas_fee = Decimal("0") if is_gasless else gas_fee_tokens
        
        # Total fee user pays
        total_fee = platform_fee + user_gas_fee
        
        return {
            "platform_fee": platform_fee,
            "gas_fee": user_gas_fee,  # What user pays for gas (0 in gasless mode)
            "actual_gas_fee": gas_fee_tokens,  # Actual gas cost (for DARI's records)
            "total_fee": total_fee,  # What user pays in total
            "estimated_gas": gas_estimates["estimated_gas"],
            "gas_price_gwei": gas_estimates["gas_price_gwei"],
            "gasless_mode": is_gasless,
            "fee_breakdown": {
                "platform_fee_usd": platform_fee * token_price_usd,
                "gas_fee_usd": gas_estimates["gas_fee_usd"],  # Actual gas cost
                "user_gas_fee_usd": Decimal("0") if is_gasless else gas_estimates["gas_fee_usd"],  # What user pays
                "total_fee_usd": (platform_fee * token_price_usd) + (Decimal("0") if is_gasless else gas_estimates["gas_fee_usd"]),
                "dari_subsidy_usd": gas_estimates["gas_fee_usd"] if is_gasless else Decimal("0")  # What DARI covers
            }
        }
    
    @staticmethod
    def is_international_transaction(from_country: Optional[str], to_country: Optional[str]) -> bool:
        """
        Determine if transaction is international
        
        Args:
            from_country: Sender's country code (ISO 3166-1 alpha-2)
            to_country: Receiver's country code (ISO 3166-1 alpha-2)
            
        Returns:
            True if international, False if domestic or unknown
        """
        if not from_country or not to_country:
            return False  # Default to domestic if countries unknown
        
        return from_country.upper() != to_country.upper()


# Singleton instance
fee_service = FeeService()
