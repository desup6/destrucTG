import json
import asyncio
import logging

from media_processor import MediaProcessor

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                    filename="app.log",
                    filemode="a"
                    )

logger = logging.getLogger(__name__)

with open("config.json", "r") as f:
    config = json.load(f)
    CLIENT_SESSION_NAME = config["client_session_name"]
    BOT_SESSION_NAME = config["bot_session_name"]
    API_ID = config["api_id"]
    API_HASH = config["api_hash"]
    BOT_TOKEN = config["bot_token"]
    MAIN_ADMIN = config["main_admin"]
    TARGET_CHANNEL = config["target_channel"]


async def main():
    processor = MediaProcessor(client_session_name=CLIENT_SESSION_NAME,
                               bot_session_name=BOT_SESSION_NAME,
                               api_id=API_ID,
                               api_hash=API_HASH,
                               bot_token=BOT_TOKEN,
                               main_admin=MAIN_ADMIN,
                               target_channel=TARGET_CHANNEL
                               )
    await processor.init_clients()
    await processor.init_settings()
    await processor.client.run_until_disconnected()
    await processor.bot.run_until_disconnected()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Bot stopped manually")
    except Exception as e:
        logging.error(f"Critical error: {str(e)}")
