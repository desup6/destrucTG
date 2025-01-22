import logging
import random

from telethon import TelegramClient, events
from telethon.tl.types import MessageMediaPhoto, MessageMediaDocument
from asyncio import Queue as AsyncQueue
from datetime import datetime, timedelta

from utils import add_watermark

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                    filename="app.log",
                    filemode="a"
                    )
logger = logging.getLogger(__name__)

class MediaCollector:
    def __init__(self, session_name, api_id, api_hash, target_channel, sources, chance, bottom_delay, top_delay, watermark_path, caption_text):
        self.collected_media = AsyncQueue()
        self.session_name = session_name
        self.api_id = api_id
        self.api_hash = api_hash
        self.target_channel = target_channel
        self.sources = sources
        self.chance = chance
        self.bottom_delay = bottom_delay
        self.top_delay = top_delay
        if watermark_path:
            self.watermark = open(watermark_path, "rb")
        else:
            self.watermark = None
        self.caption_text = caption_text
        self.client = None

    async def init_client(self):
        self.client = TelegramClient(self.session_name, self.api_id, self.api_hash)
        await self.client.start()
        logger.info(f"Client {self.session_name} launched successfully")
        for channel in self.sources:
            try:
                self.client.add_event_handler(
                    self.media_from_source,
                    events.NewMessage(chats=channel)
                )
                logger.info(f"Added source {channel}")
            except Exception as e:
                logger.info(f"Error while adding source {channel}: {str(e)}")
        self.client.add_event_handler(
                                self.media_from_queue,
                                events.NewMessage(chats=self.target_channel,
                                                  outgoing=True)
        )
        logger.info("Added outgoing messages handler")

    async def schedule_media(self, media):
        if self.watermark:
            image_bytes = await self.client.download_media(media, file=bytes)
            media = add_watermark(image_bytes, self.watermark)
        now = datetime.now()
        target_time = now + timedelta(minutes=random.randint(self.bottom_delay, self.top_delay))
        await self.client.send_file(
            self.target_channel,
            file=media,
            caption=self.caption_text,
            schedule=target_time,
            parse_mode="html"
        )
        logger.info(f"Mediafile scheduled for {target_time}")

    async def media_from_source(self, event):
        if event.message.media and (isinstance(event.message.media, (MessageMediaPhoto, MessageMediaDocument))):
            logger.info(f"New mediafile in channel {event.chat_id}")
            percent = random.randint(1, 100)
            if percent > self.chance:
                logger.info("Skipping a mediafile due to random")
                return
            logger.info(f"Scheduling mediafile")
            try:
                await self.schedule_media(event.message.media)
            except Exception as e:
                logger.info(f"Error while scheduling mediafile: {str(e)}")
                logger.info("Putting mediafile to queue")
                await self.collected_media.put(event.message.media)

    async def media_from_queue(self, event):
        logger.info("Mediafile from scheduled was sent")
        media = await self.collected_media.get()
        try:
            await self.schedule_media(media)
        except Exception as e:
            logger.info(f"Error while scheduling mediafile: {str(e)}")
            logger.info("Mediafile probably deleted or broken, skipping it")