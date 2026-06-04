import httpx
import asyncio
import json

async def test():
    async with httpx.AsyncClient() as client:
        r = await client.post('http://127.0.0.1:8000/engine/predict', json={'symbol': 'BTC/USDT', 'timeframe': '1H'})
        print(json.dumps(r.json(), indent=2))

asyncio.run(test())
