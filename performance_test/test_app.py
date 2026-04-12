import asyncio
import time
from fastapi import FastAPI

app = FastAPI(title="FastAPI Performance Test")

def sync_io_task():
    """Simulates a synchronous I/O task."""
    time.sleep(1)
    return "Complete"

async def async_io_task():
    """Simulates an asynchronous I/O task."""
    await asyncio.sleep(1)
    return "Complete"

@app.get("/sync-task")
def sync_endpoint():
    """
    Sequential execution: 3 tasks x 1s each = ~3s total.
    This simulates a poorly optimized sync architecture.
    """
    results = [sync_io_task() for _ in range(3)]
    return {"status": "success", "mode": "sync", "results": results}

@app.get("/async-task")
async def async_endpoint():
    """
    Parallel execution: asyncio.gather runs 3 tasks concurrently.
    Total time should be ~1s.
    """
    results = await asyncio.gather(
        async_io_task(),
        async_io_task(),
        async_io_task()
    )
    return {"status": "success", "mode": "async", "results": results}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
