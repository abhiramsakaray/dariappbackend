import aiohttp
import asyncio
from decimal import Decimal
from typing import Dict, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class CurrencyService:
    """Service for currency conversion and exchange rates"""
    
    def __init__(self):
        self.cache = {}  # Simple in-memory cache
        self.cache_duration = timedelta(minutes=10)  # Cache for 10 minutes
        self.base_url = "https://api.exchangerate-api.com/v4/latest"
        
        # Fallback rates in case API is down
        self.fallback_rates = {
            "USD": 1.0,
            "EUR": 0.85,
            "GBP": 0.73,
            "JPY": 110.0,
            "CAD": 1.25,
            "AUD": 1.35,
            "CHF": 0.92,
            "CNY": 6.45,
            "INR": 74.5,
            "NGN": 411.0,
            "ZAR": 14.5,
            "KES": 108.0,
            "GHS": 6.1,
            "EGP": 15.7,
            "MAD": 8.9,
            "TND": 2.8,
            "DZD": 134.0,
            "XOF": 554.0,  # West African CFA franc
            "XAF": 554.0,  # Central African CFA franc
        }
    
    async def get_exchange_rate(self, from_currency: str, to_currency: str) -> Optional[Decimal]:
        """Get exchange rate from one currency to another"""
        try:
            if from_currency == to_currency:
                return Decimal("1.0")
            
            # Check cache first
            cache_key = f"{from_currency}_{to_currency}"
            if cache_key in self.cache:
                cached_data = self.cache[cache_key]
                if datetime.now() - cached_data["timestamp"] < self.cache_duration:
                    return cached_data["rate"]
            
            # Try to get from API
            rate = await self._fetch_exchange_rate(from_currency, to_currency)
            
            if rate is not None:
                # Cache the result
                self.cache[cache_key] = {
                    "rate": rate,
                    "timestamp": datetime.now()
                }
                return rate
            
            # Fallback to hardcoded rates
            return self._get_fallback_rate(from_currency, to_currency)
            
        except Exception as e:
            logger.error(f"Error getting exchange rate {from_currency} to {to_currency}: {e}")
            return self._get_fallback_rate(from_currency, to_currency)
    
    async def _fetch_exchange_rate(self, from_currency: str, to_currency: str) -> Optional[Decimal]:
        """Fetch exchange rate from external API"""
        try:
            timeout = aiohttp.ClientTimeout(total=5)  # 5 second timeout
            async with aiohttp.ClientSession(timeout=timeout) as session:
                url = f"{self.base_url}/{from_currency}"
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        if "rates" in data and to_currency in data["rates"]:
                            rate = Decimal(str(data["rates"][to_currency]))
                            logger.info(f"Fetched exchange rate {from_currency}/{to_currency}: {rate}")
                            return rate
            
            logger.warning(f"Could not fetch exchange rate for {from_currency}/{to_currency}")
            return None
            
        except asyncio.TimeoutError:
            logger.warning(f"Timeout fetching exchange rate for {from_currency}/{to_currency}")
            return None
        except Exception as e:
            logger.error(f"Error fetching exchange rate: {e}")
            return None
    
    def _get_fallback_rate(self, from_currency: str, to_currency: str) -> Optional[Decimal]:
        """Get fallback exchange rate from hardcoded rates"""
        try:
            if from_currency not in self.fallback_rates or to_currency not in self.fallback_rates:
                logger.warning(f"No fallback rate available for {from_currency}/{to_currency}")
                return None
            
            # Convert via USD
            from_rate = Decimal(str(self.fallback_rates[from_currency]))
            to_rate = Decimal(str(self.fallback_rates[to_currency]))
            
            # Rate = (1 / from_rate) * to_rate
            rate = to_rate / from_rate
            logger.info(f"Using fallback exchange rate {from_currency}/{to_currency}: {rate}")
            return rate
            
        except Exception as e:
            logger.error(f"Error calculating fallback rate: {e}")
            return None
    
    async def convert_amount(self, amount: Decimal, from_currency: str, to_currency: str) -> Optional[Decimal]:
        """Convert amount from one currency to another"""
        try:
            rate = await self.get_exchange_rate(from_currency, to_currency)
            if rate is None:
                return None
            
            converted = amount * rate
            # Round to 4 decimal places for fiat currencies
            return converted.quantize(Decimal('0.0001'))
            
        except Exception as e:
            logger.error(f"Error converting amount: {e}")
            return None
    
    def get_supported_currencies(self) -> list[str]:
        """Get list of supported currencies"""
        return list(self.fallback_rates.keys())
    
    def is_supported_currency(self, currency: str) -> bool:
        """Check if currency is supported"""
        return currency.upper() in self.fallback_rates


# Global instance
currency_service = CurrencyService()
