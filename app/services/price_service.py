import httpx
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Optional
from decimal import Decimal

from app.core.config import settings
from app.core.database import get_async_session_local
from app.crud import token as token_crud


class PriceService:
    def __init__(self):
        self.base_url = settings.COINGECKO_API_URL
        self.update_interval = timedelta(minutes=settings.PRICE_UPDATE_INTERVAL_MINUTES)
        
    async def get_token_price(self, coingecko_id: str, vs_currency: str = "usd") -> Optional[Decimal]:
        """Get token price from CoinGecko"""
        try:
            async with httpx.AsyncClient() as client:
                url = f"{self.base_url}/simple/price"
                params = {
                    "ids": coingecko_id,
                    "vs_currencies": vs_currency,
                    "include_24hr_change": "true"
                }
                
                response = await client.get(url, params=params)
                response.raise_for_status()
                
                data = response.json()
                if coingecko_id in data and vs_currency in data[coingecko_id]:
                    price = data[coingecko_id][vs_currency]
                    return Decimal(str(price))
                
                return None
        except Exception as e:
            print(f"Error fetching price for {coingecko_id}: {e}")
            return None
    
    async def get_multiple_prices(self, coingecko_ids: list[str], vs_currency: str = "usd") -> Dict[str, Decimal]:
        """Get multiple token prices"""
        try:
            async with httpx.AsyncClient() as client:
                url = f"{self.base_url}/simple/price"
                params = {
                    "ids": ",".join(coingecko_ids),
                    "vs_currencies": vs_currency,
                    "include_24hr_change": "true"
                }
                
                response = await client.get(url, params=params)
                response.raise_for_status()
                
                data = response.json()
                prices = {}
                
                for token_id in coingecko_ids:
                    if token_id in data and vs_currency in data[token_id]:
                        prices[token_id] = Decimal(str(data[token_id][vs_currency]))
                
                return prices
        except Exception as e:
            print(f"Error fetching multiple prices: {e}")
            return {}
    
    async def update_all_token_prices(self) -> None:
        """Update all token prices in database"""
        try:
            async with get_async_session_local()() as db:
                # Get all active tokens with coingecko_id
                tokens = await token_crud.get_tokens_with_coingecko_id(db)
                
                if not tokens:
                    return
                
                # Get coingecko IDs
                coingecko_ids = [token.coingecko_id for token in tokens if token.coingecko_id]
                
                if not coingecko_ids:
                    return
                
                # Fetch prices
                prices = await self.get_multiple_prices(coingecko_ids)
                
                # Update database
                for token in tokens:
                    if token.coingecko_id and token.coingecko_id in prices:
                        await token_crud.update_token_price(
                            db, 
                            token.id, 
                            prices[token.coingecko_id]
                        )
                
                print(f"Updated prices for {len(prices)} tokens")
                
        except Exception as e:
            print(f"Error updating token prices: {e}")
    
    async def convert_to_fiat(
        self, 
        amount: Decimal, 
        token_symbol: str, 
        fiat_currency: str = "USD"
    ) -> Optional[Decimal]:
        """Convert token amount to fiat currency"""
        try:
            async with get_async_session_local()() as db:
                token = await token_crud.get_token_by_symbol(db, token_symbol)
                if not token or not token.current_price_usd:
                    return None
                
                usd_value = amount * token.current_price_usd
                
                # If target currency is USD, return directly
                if fiat_currency.upper() == "USD":
                    return usd_value
                
                # For other currencies, get exchange rate
                exchange_rate = await self.get_fiat_exchange_rate("USD", fiat_currency)
                if exchange_rate:
                    return usd_value * exchange_rate
                
                return usd_value  # Fallback to USD
                
        except Exception as e:
            print(f"Error converting to fiat: {e}")
            return None
    
    async def get_fiat_exchange_rate(self, from_currency: str, to_currency: str) -> Optional[Decimal]:
        """Get fiat currency exchange rate"""
        try:
            # Using a simple exchange rate API (you might want to use a more robust service)
            async with httpx.AsyncClient() as client:
                url = f"https://api.exchangerate-api.com/v4/latest/{from_currency}"
                response = await client.get(url)
                response.raise_for_status()
                
                data = response.json()
                if "rates" in data and to_currency in data["rates"]:
                    return Decimal(str(data["rates"][to_currency]))
                
                return None
        except Exception as e:
            print(f"Error fetching exchange rate: {e}")
            return None


# Global price service instance
price_service = PriceService()


async def start_price_updater():
    """Start the background price updater"""
    while True:
        try:
            await price_service.update_all_token_prices()
            await asyncio.sleep(settings.PRICE_UPDATE_INTERVAL_MINUTES * 60)
        except Exception as e:
            print(f"Error in price updater: {e}")
            await asyncio.sleep(60)  # Wait 1 minute before retrying
