import json
import asyncio
import logging

from media_collector import MediaCollector

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                    filename="app.log",
                    filemode="a")

logger = logging.getLogger(__name__)

with open("config.json", "r") as f:
    config = json.load(f)
    SESSION_NAME = config["session_name"]
    API_ID = config["api_id"]
    API_HASH = config["api_hash"]
    TARGET_CHANNEL = config["target_channel"]
    SOURCES = config["sources"]
    CHANCE = config["chance"]
    BOTTOM_DELAY = config["bottom_delay"]
    TOP_DELAY = config["top_delay"]
    WATERMARK_PATH = config["watermark_path"]
    CAPTION_TEXT = config["caption_text"]


async def main():
    collector = MediaCollector(SESSION_NAME,
                               API_ID,
                               API_HASH,
                               TARGET_CHANNEL,
                               SOURCES,
                               CHANCE,
                               BOTTOM_DELAY,
                               TOP_DELAY,
                               WATERMARK_PATH,
                               CAPTION_TEXT)
    await collector.init_client()
    await collector.client.run_until_disconnected()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Бот остановлен вручную")
    except Exception as e:
        logging.error(f"Критическая ошибка: {str(e)}")