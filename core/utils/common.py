import asyncio


async def run_tasks_with_error_logging(tasks: list[asyncio.Task]):
    results = await asyncio.gather(*tasks, return_exceptions=True)
    for result in results:
        if isinstance(result, Exception):
            print(f"[Error] {type(result).__name__}: {result}")


async def run_tasks_and_stop_on_error(tasks: list[asyncio.Task]):
    try:
        results = await asyncio.gather(*tasks)
        return results
    except Exception as e:
        print(f"[Fatal Error] {type(e).__name__}: {e}")
        # Cancel remaining tasks
        for task in tasks:
            if not task.done():
                task.cancel()
