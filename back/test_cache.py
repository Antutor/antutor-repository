import asyncio
from services.semantic_cache import save_to_cache

async def test_cache():
    print("Testing save_to_cache...")
    await save_to_cache("test_concept", "this is a test answer", "this is a test response")
    print("Test complete.")

if __name__ == "__main__":
    asyncio.run(test_cache())
