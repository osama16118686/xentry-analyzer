from bot.telegram_bot import run_bot
from services.scheduler import start_scheduler

if __name__ == "__main__":
    print("🚀 Xentry Crypto Bot is starting...")
    run_bot()
    start_scheduler()
