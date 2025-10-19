import aiohttp

async def get_fiat_conversion_rate(from_currency: str, to_currency: str) -> float:
    """Get conversion rate from CoinGecko API (from_currency to to_currency)"""
    if from_currency.lower() == to_currency.lower():
        return 1.0
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={from_currency.lower()}&vs_currencies={to_currency.lower()}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                # Example: {'usd-coin': {'inr': 83.2}}
                for v in data.values():
                    if to_currency.lower() in v:
                        return float(v[to_currency.lower()])
    return 1.0  # fallback if API fails
