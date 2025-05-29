import asyncio


async def run_tasks_with_error_logging(tasks: list[asyncio.Task]):
    results = await asyncio.gather(*tasks, return_exceptions=True)
    for result in results:
        if isinstance(result, Exception):
            print(f"[Error] {type(result).__name__}: {result}")
