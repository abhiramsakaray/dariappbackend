from celery import Celery
from app.celery_app import celery_app


@celery_app.task
def update_token_prices():
    """Celery task to update token prices"""
    import asyncio
    from app.services.price_service import price_service
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        result = loop.run_until_complete(
            price_service.update_all_token_prices()
        )
        return "Token prices updated successfully"
    except Exception as e:
        print(f"Error updating token prices: {e}")
        return f"Error: {e}"
    finally:
        loop.close()


@celery_app.task
def calculate_portfolio_value(user_id: int):
    """Calculate user's portfolio value in fiat currency"""
    import asyncio
    
    async def _calculate_portfolio():
        # TODO: Implement portfolio calculation
        pass
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        result = loop.run_until_complete(_calculate_portfolio())
        return result
    except Exception as e:
        print(f"Error calculating portfolio: {e}")
        return None
    finally:
        loop.close()
