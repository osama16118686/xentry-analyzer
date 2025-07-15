
import asyncio
from bot.telegram_bot import start_bot
from analyzer.scheduler import start_scheduler

async def main():
    await asyncio.gather(
        start_bot(),
        start_scheduler()
    )

if __name__ == "__main__":
    asyncio.run(main())
