import logging
import os.path
import random
from io import BytesIO
from hashlib import md5

from telethon import TelegramClient, events
from telethon.tl.types import User, Channel, Chat
from telethon.custom import Button
from telethon.errors import ScheduleTooMuchError
from datetime import datetime, timedelta

from db_manager import DBManager
from utils import add_watermark

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                    filename="app.log",
                    filemode="a"
                    )
logger = logging.getLogger(__name__)

class MediaProcessor:
    def __init__(self,
                 client_session_name,
                 bot_session_name,
                 api_id,
                 api_hash,
                 bot_token,
                 main_admin,
                 target_channel):

        self.client_session_name = client_session_name
        self.bot_session_name = bot_session_name
        self.api_id = api_id
        self.api_hash = api_hash
        self.bot_token = bot_token
        self.main_admin = main_admin
        self.target_channel = target_channel

        self.db_manager = DBManager('destrucTG.db')

        self.client = None
        self.bot = None
        self.sources = []
        self.admins = []

        self.watermark = None
        self.caption = None
        self.bottom_delay = None
        self.top_delay = None
        self.media_types = None

    async def init_clients(self):
        self.client = TelegramClient(self.client_session_name, self.api_id, self.api_hash)
        await self.client.start()
        logger.info(f"Client {self.client_session_name} launched successfully")

        sources = await self.db_manager.get_sources()
        if sources is not None:
            for source in sources:
                source_id, state, chance, _ = source
                logger.info(f"Found source {source_id}")
                if state != 0:
                    self.sources.append(source_id)
                    logger.info(f"Source {source_id} is added to sources")
                else:
                    logger.info("Source is not active, skipping")
        else:
            logger.info("No sources found, skipping")
        try:
            self.client.add_event_handler(
                self.process_media,
                events.NewMessage(incoming=True)
            )
            logger.info(f"Added sources handlers")
        except Exception as e:
            logger.error(f"Error while adding sources handlers: {e}")

        self.client.add_event_handler(self.send_media_from_db,
                                      events.NewMessage(chats=self.target_channel,
                                                        outgoing=True)
                                      )
        logger.info("Added outgoing messages handler")

        self.bot = TelegramClient(self.bot_session_name, self.api_id, self.api_hash)
        self.bot.parse_mode = "html"
        await self.bot.start(bot_token=self.bot_token)
        logger.info(f"Bot {self.bot_session_name} launched successfully")
        self.add_bot_handlers()

        admins = await self.db_manager.get_admins()
        if admins:
            for admin in admins:
                self.admins.append(admin[0])
                logger.info(f"Added {admin[0]} to admins list")
        else:
            logger.info("No admins found")
            if self.main_admin:
                await self.db_manager.add_admin(self.main_admin, None, None, 1, 1)
                self.admins.append(self.main_admin)
                logger.info("Added main admin as a backup variant")
            else:
                logger.error("Main admin was not specified, bot won't work")

    async def init_settings(self):
        logger.info("Initializing additional settings")

        _, watermark_path = await self.db_manager.get_setting("watermark")
        if watermark_path is None:
            logger.info("Watermark path not found, setting to default (\"\")")
            await self.db_manager.add_setting("watermark", "")
            self.watermark = None
        else:
            logger.info(f"Watermark path is \"{watermark_path}\"")
            try:
                self.watermark = open(watermark_path, "rb")
            except FileNotFoundError:
                logger.info("Watermark file was probably moved or deleted, setting watermark path to (\"\")")
                self.watermark = None
                await self.db_manager.update_setting("watermark", "")


        _, caption = await self.db_manager.get_setting("caption")
        if caption is None:
            logger.info("Caption not found, setting to default (\"\")")
            await self.db_manager.add_setting("caption", "")
            self.caption = ""
        else:
            logger.info(f"Caption is \"{caption}\"")
            self.caption = caption

        _, bottom_delay = await self.db_manager.get_setting("bottom_delay")
        if bottom_delay is None:
            logger.info("Bottom delay not found, setting to default (720)")
            await self.db_manager.add_setting("bottom_delay", "720")
            self.bottom_delay = 720
        else:
            logger.info(f"Bottom delay is {bottom_delay}")
            self.bottom_delay = int(bottom_delay)

        _, top_delay = await self.db_manager.get_setting("top_delay")
        if top_delay is None:
            logger.info("Top delay not found, setting to default (1440)")
            await self.db_manager.add_setting("top_delay", "1440")
            self.top_delay = 1440
        else:
            logger.info(f"Top delay is {top_delay}")
            self.top_delay = int(top_delay)

        _, media_types = await self.db_manager.get_setting("media_types")
        if media_types is None:
            logger.info("Media types not found, setting to default (\"pic+vid\")")
            await self.db_manager.add_setting("media_types", "pic+vid")
            self.media_types = "pic+vid"
        else:
            logger.info(f"Media types is \"{media_types}\"")
            self.media_types = media_types

    def add_bot_handlers(self):
        logger.info(f"Adding bot handlers")
        try:
            self.bot.add_event_handler(
                self.start_handler,
                events.NewMessage(pattern="/start")
            )
            self.bot.add_event_handler(
                self.main_handler,
                events.CallbackQuery(data=b"main")
            )
            self.bot.add_event_handler(
                self.manage_sources_handler,
                events.CallbackQuery(data=b"manage_sources")
            )
            self.bot.add_event_handler(
                self.list_sources_handler,
                events.CallbackQuery(pattern=r"list_sources_\d+")
            )
            self.bot.add_event_handler(
                self.add_source_handler,
                events.CallbackQuery(data=b"add_source")
            )
            self.bot.add_event_handler(
                self.edit_source_handler,
                events.CallbackQuery(pattern=r"edit_\d+")
            )
            self.bot.add_event_handler(
                self.edit_state_handler,
                events.CallbackQuery(pattern=r"edit_state_\d+")
            )
            self.bot.add_event_handler(
                self.update_state_handler,
                events.CallbackQuery(pattern=r"update_state_\d+")
            )
            self.bot.add_event_handler(
                self.edit_chance_handler,
                events.CallbackQuery(pattern=r"edit_chance_\d+")
            )
            self.bot.add_event_handler(
                self.new_source_handler,
                events.CallbackQuery(pattern=r"add_\d+_\d+_\d+")
            )
            self.bot.add_event_handler(
                self.delete_source_handler,
                events.CallbackQuery(pattern=r"delete_\d+")
            )
            self.bot.add_event_handler(
                self.approve_handler,
                events.CallbackQuery(pattern=r"approve_\d+_\d+")
            )
            self.bot.add_event_handler(
                self.instant_approve_handler,
                events.CallbackQuery(pattern=r"approve_instantly_\d+_\d+")
            )
            self.bot.add_event_handler(
                self.reject_handler,
                events.CallbackQuery(pattern=r"reject_\d+_\d+")
            )
            self.bot.add_event_handler(
                self.manage_admins_handler,
                events.CallbackQuery(data=b"manage_admins")
            )
            self.bot.add_event_handler(
                self.list_admins_handler,
                events.CallbackQuery(pattern=r"list_admins_\d+")
            )
            self.bot.add_event_handler(
                self.add_admin_handler,
                events.CallbackQuery(data=b"add_admin")
            )
            self.bot.add_event_handler(
                self.edit_admin_handler,
                events.CallbackQuery(pattern=r"edit_admin_\d+")
            )
            self.bot.add_event_handler(
                self.edit_subscription_handler,
                events.CallbackQuery(pattern=r"sub_\d+_\d+")
            )
            self.bot.add_event_handler(
                self.edit_superadmin_handler,
                events.CallbackQuery(pattern=r"super_\d+_\d+")
            )
            self.bot.add_event_handler(
                self.new_admin_handler,
                events.CallbackQuery(pattern=r"add_admin_\d+_\d+")
            )
            self.bot.add_event_handler(
                self.delete_admin_handler,
                events.CallbackQuery(pattern=r"delete_admin_\d+")
            )
            self.bot.add_event_handler(
                self.additional_settings_handler,
                events.CallbackQuery(pattern=b"additional_settings")
            )
            self.bot.add_event_handler(
                self.watermark_handler,
                events.CallbackQuery(pattern=b"watermark")
            )
            self.bot.add_event_handler(
                self.add_watermark_handler,
                events.CallbackQuery(pattern=b"add_watermark")
            )
            self.bot.add_event_handler(
                self.disable_watermark_handler,
                events.CallbackQuery(pattern=b"disable_watermark")
            )
            self.bot.add_event_handler(
                self.caption_handler,
                events.CallbackQuery(pattern=b"caption")
            )
            self.bot.add_event_handler(
                self.add_caption_handler,
                events.CallbackQuery(pattern=b"add_caption")
            )
            self.bot.add_event_handler(
                self.disable_caption_handler,
                events.CallbackQuery(pattern=b"disable_caption")
            )
            self.bot.add_event_handler(
                self.delay_handler,
                events.CallbackQuery(pattern=b"delays")
            )
            self.bot.add_event_handler(
                self.edit_delay_handler,
                events.CallbackQuery(pattern=r".+_delay")
            )
            self.bot.add_event_handler(
                self.new_message_handler,
                events.NewMessage()
            )
            self.bot.add_event_handler(
                self.media_type_handler,
                events.CallbackQuery(pattern=b"media_types")
            )
            self.bot.add_event_handler(
                self.edit_media_type_handler,
                events.CallbackQuery(pattern=r"update_media_.+")
            )
            logger.info(f"Bot handlers successfully added")
        except Exception as e:
            logger.error(f"Error while adding bot handlers: {e}")

    def media_filter(self, event):
        if self.media_types == "pic+vid":
            if event.photo or event.video:
                return True
            return False
        elif self.media_types == "pic":
            if event.photo:
                return True
            return False
        elif self.media_types == "vid":
            if event.video:
                return True
            return False

    async def schedule_media(self, source_id, message_id, schedule):
        try:
            source_message = await self.client.get_messages(source_id, ids=message_id)
            media = source_message.media
        except Exception as e:
            logger.error(f"Error while getting mediafile: {str(e)}")
            logger.info("Message was probably deleted or broken, skipping it")
            return

        try:
            if source_message.photo and self.watermark:
                image_bytes = await self.client.download_media(media, file=bytes)
                media = add_watermark(image_bytes, self.watermark)

            if schedule:
                now = datetime.now()
                target_time = now + timedelta(minutes=random.randint(self.bottom_delay, self.top_delay))
                target_time = target_time.astimezone()
            else:
                target_time = None

            await self.client.send_file(
                self.target_channel,
                file=media,
                caption=self.caption,
                schedule=target_time,
                parse_mode="html"
            )
            _, _, _, posts_amount = await self.db_manager.get_source(source_id)
            await self.db_manager.update_posts_amount(source_id, posts_amount + 1)
            if target_time:
                logger.info(f"Mediafile scheduled for {target_time}")
            else:
                logger.info(f"Mediafile sent instantly")

        except ScheduleTooMuchError:
            logger.info(f"Scheduled messages are full, adding post to db instead")
            await self.db_manager.add_scheduled_post(source_id, message_id, datetime.now())

    async def start_handler(self, event):
        sender = await event.get_sender()
        if sender.id not in self.admins:
            return
        await self.db_manager.update_subscription(sender.id, 1)
        await self.db_manager.update_user_state(sender.id, "idle")
        reply_message = await event.reply("Welcome to destrucTG control bot.\nPress the button below to continue.",
                                          buttons=[[Button.inline("Start", data="main")]]
                                          )
        _, _, menu_message, _, _ = await self.db_manager.get_admin(sender.id)
        if menu_message:
            await self.bot.delete_messages(sender.id, menu_message)
        await self.db_manager.update_menu_message(sender.id, reply_message.id)
        await reply_message.pin()

    async def main_handler(self, event):
        if event.query.user_id not in self.admins:
            return
        await event.edit("Main menu",
                         buttons=[[Button.inline("Manage sources", data="manage_sources")],
                                  [Button.inline("Manage bot admins", data="manage_admins")],
                                  [Button.inline("Additional settings", data="additional_settings")]]
                         )

    async def manage_sources_handler(self, event):
        if event.query.user_id not in self.admins:
            await event.answer()
            return
        await self.db_manager.update_user_state(event.query.user_id, "idle")
        await event.edit("Managing sources",
                         buttons=[[Button.inline("List sources", data="list_sources_1")],
                                  [Button.inline("Add source", data="add_source")],
                                  [Button.inline("Main Menu", data="main")]]
                         )

    async def list_sources_handler(self, event):
        if event.query.user_id not in self.admins:
            await event.answer()
            return
        sources_page_number = int(event.data.decode("utf-8").split("_")[2])
        if sources_page_number < 1:
            return
        sources = await self.db_manager.get_sources()
        if sources:
            basic_buttons = [[Button.inline("Prev", data=f"list_sources_{sources_page_number-1}"),
                              Button.inline("Back ⬅️", data="manage_sources"),
                              Button.inline("Next", data=f"list_sources_{sources_page_number+1}")]]
            sources_on_page = sources[5*(sources_page_number-1):5*sources_page_number]
            if sources_on_page:
                sources_buttons = []
                for source in sources_on_page:
                    source_object = await self.bot.get_entity(source[0])
                    if isinstance(source_object, (Chat, Channel)):
                        source_name = source_object.title
                    elif isinstance(source_object, User):
                        source_name = f"{source_object.first_name} {source_object.last_name}"
                    else:
                        source_name = "No name"

                    sources_buttons.append([Button.inline(source_name, data=f"edit_{source[0]}")])
                await event.edit("Here is the list of sources.\nClick one of the buttons below to edit properties of source.",
                                 buttons=sources_buttons+basic_buttons
                                 )
            else:
                await event.answer("No sources to show.")
        else:
            await event.edit("No sources have been added yet.",
                             buttons=[[Button.inline("Back ⬅️", data="manage_sources")]])

    async def add_source_handler(self, event):
        if event.query.user_id not in self.admins:
            await event.answer()
            return
        _, _, _, _, super_admin = await self.db_manager.get_admin(event.query.user_id)
        if super_admin == 0:
            message_text = "You're not allowed to add sources"
        else:
            message_text = "Send new source link/username/id"
            await self.db_manager.update_user_state(event.query.user_id, "adding_source")
        await event.edit(message_text,
                         buttons=[[Button.inline("Back ⬅️", data="manage_sources")]]
                         )

    async def new_source_handler(self, event):
        if event.query.user_id not in self.admins:
            await event.answer()
            return
        data = event.data.decode("utf-8").split("_")
        source_id = int(data[1])
        source_chance = int(data[2])
        source_state = int(data[3])
        await self.db_manager.add_source(source_id, source_state, source_chance, 0)
        self.sources.append(source_id)
        await event.edit(f"Source {source_id} successfully added.",
                         buttons=[[Button.inline("Back", data="manage_sources")]]
                         )

    async def edit_source_handler(self, event):
        if event.query.user_id not in self.admins:
            await event.answer()
            return
        _, _, _, _, super_admin = await self.db_manager.get_admin(event.query.user_id)
        if super_admin == 0:
            await event.edit("You're not allowed to edit sources",
                             buttons=[[Button.inline("Back ⬅️", data="list_sources_1")]]
                             )
        else:
            source_id = int(event.data.decode("utf-8").split("_")[1])
            _, source_state, source_chance, source_amount = await self.db_manager.get_source(source_id)

            source_object = await self.bot.get_entity(source_id)
            if isinstance(source_object, (Chat, Channel)):
                source_name = source_object.title
            elif isinstance(source_object, User):
                source_name = f"{source_object.first_name} {source_object.last_name if source_object.last_name else ''}"
            else:
                source_name = "No name"

            if source_object.username:
                source_link_text = f"<a href=https://t.me/{source_object.username}>{source_name}</a>"
            else:
                source_link_text = source_name

            if source_state == 0:
                state = "inactive"
            elif source_state == 1:
                state = "active"
            elif source_state == 2:
                state = "active + auto approve"

            await event.edit(f"<b>Source:</b> <i>{source_link_text}</i>\n"
                             f"<b>State:</b> <i>{source_state} ({state})</i>\n"
                             f"<b>Chance:</b> <i>{source_chance}%</i>\n"
                             f"<b>Posts taken:</b> <i>{source_amount}</i>",
                             parse_mode="html",
                             buttons=[[Button.inline("Edit state", data=f"edit_state_{source_id}")],
                                      [Button.inline("Edit chance", data=f"edit_chance_{source_id}")],
                                      [Button.inline("Delete Source", data=f"delete_{source_id}")],
                                      [Button.inline("Back ⬅️", data="list_sources_1")]])

    async def edit_state_handler(self, event):
        if event.query.user_id not in self.admins:
            await event.answer()
            return
        source_id = int(event.data.decode("utf-8").split("_")[2])
        _, source_state, _, _ = await self.db_manager.get_source(source_id)
        if source_state:
            await event.edit(f"Choose state for channel {source_id}\n",
                             parse_mode="html",
                             buttons=[[Button.inline(f"Active {'[chosen]' if source_state == 1 else ''}",
                                                     data=f"update_state_{source_id}_1")],
                                      [Button.inline(f"Active (with auto approve) {'[chosen]' if source_state == 2 else ''}",
                                                     data=f"update_state_{source_id}_2")],
                                      [Button.inline(f"Inactive {'[chosen]' if source_state == 0 else ''}",
                                                     data=f"update_state_{source_id}_0")],
                                      [Button.inline("Back ⬅️", data=f"edit_{source_id}")]]
                             )
        else:
            await event.edit(f"Source {source_id} was removed from sources",
                             buttons=[[Button.inline("Back ⬅️", data="list_sources_1")]]
                             )

    async def update_state_handler(self, event):
        if event.query.user_id not in self.admins:
            await event.answer()
            return
        data = event.data.decode("utf-8").split("_")
        source_id = int(data[2])
        source_state = int(data[3])
        await self.db_manager.update_state(source_id, source_state)
        logger.info(f"Source {source_id} state was updated to {source_state}")
        if source_state == 0:
            state = "inactive"
        elif source_state == 1:
            state = "active"
        elif source_state == 2:
            state = "active + auto approve"
        await event.edit(f"Source {source_id} state was updated to <i>{state}</i>",
                         parse_mode="html",
                         buttons=[[Button.inline("Back ⬅️", data=f"edit_{source_id}")]]
                         )

    async def edit_chance_handler(self, event):
        if event.query.user_id not in self.admins:
            await event.answer()
            return
        source_id = int(event.data.decode("utf-8").split("_")[2])
        await self.db_manager.update_user_state(event.query.user_id, f"update_chance_{source_id}")
        await event.edit(f"Send new chance for {source_id} (from 1 to 100)",
                         buttons=[[Button.inline("Back ⬅️", data=f"edit_{source_id}")]]
                         )

    async def delete_source_handler(self, event):
        if event.query.user_id not in self.admins:
            await event.answer()
            return
        source_id = int(event.data.decode("utf-8").split("_")[1])
        await self.db_manager.delete_source(source_id)
        await self.db_manager.delete_scheduled_posts(source_id)
        self.sources.remove(source_id)
        await event.edit(f"Source {source_id} deleted.",
                         buttons=[[Button.inline("Back ⬅️", data="list_sources_1")]]
                         )

    async def approve_handler(self, event):
        if event.query.user_id not in self.admins:
            await event.answer()
            return
        data = event.data.decode("utf-8").split("_")
        post_id = data[1] + "_" + data[2]
        source_id = int(data[1])
        message_id = int(data[2])
        logger.info(f"Approving post {message_id} from {source_id}")
        await self.schedule_media(source_id, message_id, True)
        confirmation_posts = await self.db_manager.get_confirmation_posts(post_id)
        if confirmation_posts:
            for post in confirmation_posts:
                await self.bot.delete_messages(post[1], post[2])
                logger.info(f"Deleted confirmation message from {post[1]} chat")
        await self.db_manager.delete_confirmation_posts(post_id)
        logger.info("Deleted confirmation posts from db")

    async def instant_approve_handler(self, event):
        if event.query.user_id not in self.admins:
            await event.answer()
            return
        data = event.data.decode("utf-8").split("_")
        post_id = data[2] + "_" + data[3]
        source_id = int(data[2])
        message_id = int(data[3])
        logger.info(f"Instantly approving post {message_id} from {source_id}")
        await self.schedule_media(source_id, message_id, False)
        confirmation_posts = await self.db_manager.get_confirmation_posts(post_id)
        if confirmation_posts:
            for post in confirmation_posts:
                await self.bot.delete_messages(post[1], post[2])
                logger.info(f"Deleted confirmation message from {post[1]} chat")
        await self.db_manager.delete_confirmation_posts(post_id)
        logger.info("Deleted confirmation posts from db")

    async def reject_handler(self, event):
        if event.query.user_id not in self.admins:
            await event.answer()
            return
        data = event.data.decode("utf-8").split("_")
        post_id = data[1] + "_" + data[2]
        source_id = int(data[1])
        message_id = int(data[2])
        logger.info(f"Rejecting post {message_id} from {source_id}")
        confirmation_posts = await self.db_manager.get_confirmation_posts(post_id)
        if confirmation_posts:
            for post in confirmation_posts:
                await self.bot.delete_messages(post[1], post[2])
                logger.info(f"Deleted confirmation message from {post[1]} chat")
        await self.db_manager.delete_confirmation_posts(post_id)
        logger.info("Deleted confirmation posts from db")

    async def manage_admins_handler(self, event):
        if event.query.user_id not in self.admins:
            await event.answer()
            return
        await self.db_manager.update_user_state(event.query.user_id, "idle")
        await event.edit("Managing admins",
                         buttons=[[Button.inline("List admins", data="list_admins_1")],
                                  [Button.inline("Add admin", data="add_admin")],
                                  [Button.inline("Main Menu", data="main")]]
                         )

    async def list_admins_handler(self, event):
        if event.query.user_id not in self.admins:
            await event.answer()
            return
        sources_page_number = int(event.data.decode("utf-8").split("_")[2])
        if sources_page_number < 1:
            return
        admins = await self.db_manager.get_admins()
        if admins:
            basic_buttons = [[Button.inline("Prev", data=f"list_admins_{sources_page_number-1}"),
                              Button.inline("Back ⬅️", data="manage_admins"),
                              Button.inline("Next", data=f"list_admins_{sources_page_number+1}")]]
            admins_on_page = admins[5*(sources_page_number-1):5*sources_page_number]
            if admins_on_page:
                admins_buttons = []
                for admin in admins:
                    admin_object = await self.bot.get_entity(admin[0])
                    admin_name = f"{admin_object.first_name} {admin_object.last_name if admin_object.last_name else ''}"

                    admins_buttons.append([Button.inline(admin_name, data=f"edit_admin_{admin[0]}")])
                await event.edit("Here is the list of bot admins.\nClick one of the buttons below to edit admins' properties.",
                                 buttons=admins_buttons+basic_buttons)
            else:
                await event.answer("No admins to show.")
        else:
            await event.edit("No admins have been added yet.",
                             buttons=[[Button.inline("Back ⬅️", data="manage_admins")]])

    async def add_admin_handler(self, event):
        if event.query.user_id not in self.admins:
            await event.answer()
            return
        _, _, _, _, super_admin = await self.db_manager.get_admin(event.query.user_id)
        if super_admin == 0:
            message_text = "You're not allowed to add admins"
        else:
            message_text = "Send new admin link/username/id"
            await self.db_manager.update_user_state(event.query.user_id, "adding_admin")
        await event.edit(message_text,
                         buttons=[[Button.inline("Back ⬅️", data="manage_admins")]])

    async def new_admin_handler(self, event):
        if event.query.user_id not in self.admins:
            await event.answer()
            return
        data = event.data.decode("utf-8").split("_")
        admin_id = int(data[2])
        super_admin = int(data[3])
        await self.db_manager.add_admin(admin_id, None, None, 0, super_admin)
        self.admins.append(admin_id)
        await event.edit(f"Admin {admin_id} successfully added.",
                         buttons=[[Button.inline("Back", data="manage_admins")]]
                         )

    async def edit_admin_handler(self, event):
        if event.query.user_id not in self.admins:
            await event.answer()
            return
        _, _, _, _, super_admin = await self.db_manager.get_admin(event.query.user_id)
        if super_admin == 0:
            await event.edit("You're not allowed to edit admins",
                             buttons=[[Button.inline("Back ⬅️", data="list_admins_1")]]
                             )
        else:
            admin_id = int(event.data.decode("utf-8").split("_")[2])
            admin_id, _, _, admin_subscription, super_admin = await self.db_manager.get_admin(admin_id)
            if admin_subscription == 1:
                subscription_button = Button.inline("Disable subscription", data=f"sub_{admin_id}_0")
            else:
                subscription_button = Button.inline("Enable subscription", data=f"sub_{admin_id}_1")

            if super_admin == 1:
                superadmin_button = Button.inline("Make user a regular admin", data=f"super_{admin_id}_0")
            else:
                superadmin_button = Button.inline("Make user a superadmin", data=f"super_{admin_id}_1")

            admin_object = await self.bot.get_entity(admin_id)
            admin_name = f"{admin_object.first_name} {admin_object.last_name if admin_object.last_name else ''}"
            if admin_object.username:
                admin_link_text = f"<a href=https://t.me/{admin_object.username}>{admin_name}</a>"
            else:
                admin_link_text = admin_name
            await event.edit(f"<b>Admin:</b> <i>{admin_link_text}</i>\n"
                             f"<b>Subscribed:</b> <i>{'True' if admin_subscription else 'False'}</i>\n"
                             f"<b>Superadmin:</b> <i>{'True' if super_admin else 'False'}</i>",
                             parse_mode="html",
                             buttons=[[subscription_button],
                                      [superadmin_button],
                                      [Button.inline("Delete admin", data=f"delete_admin_{admin_id}")],
                                      [Button.inline("Back ⬅️", data="list_admins_1")]]
                             )

    async def edit_subscription_handler(self, event):
        if event.query.user_id not in self.admins:
            await event.answer()
            return
        data = event.data.decode("utf-8").split("_")
        admin_id = int(data[1])
        subscription = int(data[2])
        await self.db_manager.update_subscription(admin_id, subscription)
        await event.edit(f"Subscription status was successfully updated to <i>{'True' if subscription else 'False'}</i>",
                         parse_mode="html",
                         buttons=[[Button.inline("Back ⬅️", data=f"edit_admin_{admin_id}")]]
                         )

    async def edit_superadmin_handler(self, event):
        if event.query.user_id not in self.admins:
            await event.answer()
            return
        data = event.data.decode("utf-8").split("_")
        admin_id = int(data[1])
        super_admin_state = int(data[2])
        _, _, _, _, super_admin = await self.db_manager.get_admin(admin_id)
        admins = await self.db_manager.get_admins()
        superadmins_amount = 0
        for admin in admins:
            if admin[4] == 1:
                superadmins_amount += 1
        if super_admin and superadmins_amount == 1 and not super_admin_state:
            await event.edit(
                f"You cant remove super admin status from last superadmin or the bot will be broken.",
                buttons=[[Button.inline("Back ⬅️", data=f"edit_admin_{admin_id}")]]
                )
        else:
            await self.db_manager.update_super_admin(admin_id, super_admin_state)
            await event.edit(f"Super admin status was successfully updated to <i>{'True' if super_admin_state else 'False'}</i>",
                             parse_mode="html",
                             buttons=[[Button.inline("Back ⬅️", data=f"edit_admin_{admin_id}")]]
                             )

    async def delete_admin_handler(self, event):
        if event.query.user_id not in self.admins:
            await event.answer()
            return
        admin_id = int(event.data.decode("utf-8").split("_")[2])
        _, _, _, _, super_admin = await self.db_manager.get_admin(admin_id)
        admins = await self.db_manager.get_admins()
        superadmins_amount = 0
        for admin in admins:
            if admin[3] == 1:
                superadmins_amount += 1
        if super_admin and superadmins_amount == 1:
            await event.edit(
                f"You cant delete last super admin or the bot will be broken.",
                parse_mode="html",
                buttons=[[Button.inline("Back ⬅️", data=f"edit_admin_{admin_id}")]]
                )
        else:
            await self.db_manager.delete_admin(admin_id)
            await event.edit(
                f"Admin <i>{admin_id}</i> was successfully deleted",
                parse_mode="html",
                buttons=[[Button.inline("Back ⬅️", data=f"manage_admins")]]
                )
            self.admins.remove(admin_id)

    async def additional_settings_handler(self, event):
        if event.query.user_id not in self.admins:
            await event.answer()
            return
        _, _, _, _, super_admin = await self.db_manager.get_admin(event.query.user_id)
        if super_admin == 0:
            await event.edit("You're not allowed to edit additional_settings",
                             buttons=[[Button.inline("Back ⬅️", data="main")]]
                             )
        # await self.db_manager.update_user_state(event.query.user_id, "idle")
        else:
            await event.edit("Additional settings",
                             buttons=[[Button.inline("Watermark", data="watermark")],
                                      [Button.inline("Caption", data="caption")],
                                      [Button.inline("Delays", data="delays")],
                                      [Button.inline("Media types", data="media_types")],
                                      [Button.inline("Main Menu", data="main")]]
                             )

    async def watermark_handler(self, event):
        if event.query.user_id not in self.admins:
            await event.answer()
            return
        _, _, _, _, super_admin = await self.db_manager.get_admin(event.query.user_id)
        if super_admin == 0:
            await event.edit("You're not allowed to edit watermark",
                             buttons=[[Button.inline("Back ⬅️", data="main")]]
                             )
        else:
            _, watermark_path = await self.db_manager.get_setting("watermark")
            if watermark_path:
                message_text = "Watermark state: <i>enabled</i>"
                manage_button = [[Button.inline("Disable watermark", data="disable_watermark")]]
            else:
                message_text = "Watermark state: <i>disabled</i>"
                manage_button = [[Button.inline("Add watermark", data="add_watermark")]]
            await event.edit(message_text,
                             parse_mode="html",
                             buttons=manage_button+[[Button.inline("Back ⬅️", data="additional_settings")]]
                             )

    async def add_watermark_handler(self, event):
        if event.query.user_id not in self.admins:
            await event.answer()
            return
        _, _, _, _, super_admin = await self.db_manager.get_admin(event.query.user_id)
        if super_admin == 0:
            await event.edit("You're not allowed to add watermark",
                             buttons=[[Button.inline("Back ⬅️", data="main")]]
                             )
        else:
            await self.db_manager.update_user_state(event.query.user_id, "adding_watermark")
            await event.edit("Send a watermark as a file. Use .png format with transparency for best result",
                             buttons=[[Button.inline("Back ⬅️", data="watermark")]]
                             )

    async def disable_watermark_handler(self, event):
        if event.query.user_id not in self.admins:
            await event.answer()
            return
        _, _, _, _, super_admin = await self.db_manager.get_admin(event.query.user_id)
        if super_admin == 0:
            await event.edit("You're not allowed to disable watermark",
                             buttons=[[Button.inline("Back ⬅️", data="main")]]
                             )
        else:
            await self.db_manager.update_setting("watermark", "")
            self.watermark = None
            await event.edit("Watermark was disabled",
                             buttons=[[Button.inline("Back ⬅️", data="watermark")]]
                             )

    async def caption_handler(self, event):
        if event.query.user_id not in self.admins:
            await event.answer()
            return
        _, _, _, _, super_admin = await self.db_manager.get_admin(event.query.user_id)
        if super_admin == 0:
            await event.edit("You're not allowed to edit caption",
                             buttons=[[Button.inline("Back ⬅️", data="main")]]
                             )
        else:
            _, caption = await self.db_manager.get_setting("caption")
            if caption:
                message_text = f"Caption state: <i>enabled</i>\n\"{caption}\""
                manage_button = [[Button.inline("Disable caption", data="disable_caption")]]
            else:
                message_text = "Caption state: <i>disabled</i>"
                manage_button = [[Button.inline("Add caption", data="add_caption")]]
            await event.edit(message_text,
                             parse_mode="html",
                             buttons=manage_button+[[Button.inline("Back ⬅️", data="additional_settings")]]
                             )

    async def add_caption_handler(self, event):
        if event.query.user_id not in self.admins:
            await event.answer()
            return
        _, _, _, _, super_admin = await self.db_manager.get_admin(event.query.user_id)
        if super_admin == 0:
            await event.edit("You're not allowed to add caption",
                             buttons=[[Button.inline("Back ⬅️", data="main")]]
                             )
        else:
            await self.db_manager.update_user_state(event.query.user_id, "adding_caption")
            await event.edit("Send caption for posts. You can use Telegram text formatting.",
                             buttons=[[Button.inline("Back ⬅️", data="caption")]]
                             )

    async def disable_caption_handler(self, event):
        if event.query.user_id not in self.admins:
            await event.answer()
            return
        _, _, _, _, super_admin = await self.db_manager.get_admin(event.query.user_id)
        if super_admin == 0:
            await event.edit("You're not allowed to disable caption",
                             buttons=[[Button.inline("Back ⬅️", data="main")]]
                             )
        else:
            await self.db_manager.update_setting("caption", "")
            self.caption = ""
            await event.edit("Caption was disabled",
                             buttons=[[Button.inline("Back ⬅️", data="caption")]]
                             )

    async def delay_handler(self, event):
        if event.query.user_id not in self.admins:
            await event.answer()
            return
        _, _, _, _, super_admin = await self.db_manager.get_admin(event.query.user_id)
        if super_admin == 0:
            await event.edit("You're not allowed to edit delays",
                             buttons=[[Button.inline("Back ⬅️", data="main")]]
                             )
        else:
            _, bottom_delay = await self.db_manager.get_setting("bottom_delay")
            bottom_delay = int(bottom_delay)
            _, top_delay = await self.db_manager.get_setting("top_delay")
            top_delay = int(top_delay)
            await event.edit(f"Bottom delay: <i>{bottom_delay} mins (~{bottom_delay // 60} hrs)</i>\n"
                             f"Top delay: <i>{top_delay} mins (~{top_delay // 60} hrs)</i>",
                             parse_mode="html",
                             buttons=[[Button.inline("New bottom delay", data="bottom_delay")],
                                      [Button.inline("New top delay", data="top_delay")],
                                      [Button.inline("Back ⬅️", data="additional_settings")]]
                             )

    async def edit_delay_handler(self, event):
        if event.query.user_id not in self.admins:
            await event.answer()
            return
        _, _, _, _, super_admin = await self.db_manager.get_admin(event.query.user_id)
        if super_admin == 0:
            await event.edit("You're not allowed to edit delays",
                             buttons=[[Button.inline("Back ⬅️", data="main")]]
                             )
        else:
            delay_type = event.data.decode("utf-8").split("_")[0]
            if delay_type == "bottom":
                await self.db_manager.update_user_state(event.query.user_id, "adding_bottom_delay")
                await event.edit("Send new bottom delay (in minutes)",
                                 buttons=[[Button.inline("Back ⬅️", data="delays")]]
                                 )
            elif delay_type == "top":
                await self.db_manager.update_user_state(event.query.user_id, "adding_top_delay")
                await event.edit("Send new top delay (in minutes)",
                                 buttons=[[Button.inline("Back ⬅️", data="delays")]]
                                 )\

    async def media_type_handler(self, event):
        if event.query.user_id not in self.admins:
            await event.answer()
            return
        _, _, _, _, super_admin = await self.db_manager.get_admin(event.query.user_id)
        if super_admin == 0:
            await event.edit("You're not allowed to edit media types",
                             buttons=[[Button.inline("Back ⬅️", data="main")]]
                             )
        else:
            _, media_type = await self.db_manager.get_setting("media_types")
            if media_type == "pic":
                service_buttons = [[Button.inline("vid", data="update_media_vid")],
                                   [Button.inline("pic+vid", data="update_media_pic+vid")]]
                media_type_text = "pic (Processing pictures only)"
            elif media_type == "vid":
                service_buttons = [[Button.inline("pic", data="update_media_pic")],
                                   [Button.inline("pic+vid", data="update_media_pic+vid")]]
                media_type_text = "vid (Processing videos only)"
            elif media_type == "pic+vid":
                service_buttons = [[Button.inline("pic", data="update_media_pic")],
                                   [Button.inline("vid", data="update_media_vid")]]
                media_type_text = "pic+vid (Processing pictures and videos)"

            await event.edit(f"Type of processed media:\n{media_type_text}.\nPress one of the buttons below to change it",
                             parse_mode="html",
                             buttons=service_buttons+[[Button.inline("Back ⬅️", data="additional_settings")]]
                             )

    async def edit_media_type_handler(self, event):
        if event.query.user_id not in self.admins:
            await event.answer()
            return
        _, _, _, _, super_admin = await self.db_manager.get_admin(event.query.user_id)
        if super_admin == 0:
            await event.edit("You're not allowed to edit delays",
                             buttons=[[Button.inline("Back ⬅️", data="main")]]
                             )
        else:
            media_type = event.data.decode("utf-8").split("_")[2]
            await self.db_manager.update_setting("media_types", media_type)
            self.media_types = media_type
            await event.edit(f"Processed media type updated ({media_type})",
                             buttons=[[Button.inline("Back ⬅️", data="media_types")]]
                             )

    async def new_message_handler(self, event):
        sender = await event.get_sender()
        if sender.id not in self.admins:
            return
        _, user_state, _, _, _ = await self.db_manager.get_admin(sender.id)
        if user_state == "idle" and event.text != "/start":
            await event.delete()

        elif user_state == "adding_source":
            source_id = event.text
            try:
                source_id = int(source_id)
            except ValueError:
                pass
            try:
                source_object = await self.bot.get_entity(source_id)
                sid, _, _, _ = await self.db_manager.get_source(source_object.id)
                _, _, menu_message, _, _ = await self.db_manager.get_admin(sender.id)
                if sid is not None:
                    await event.reply("Source is already in database.")
                    return
                await self.db_manager.update_user_state(sender.id, f"add_chance_{source_object.id}")
                if source_object.username:
                    link_text = f"<a href=https://t.me/{source_object.username}>{source_object.id}</a>"
                else:
                    link_text = f"{source_object.id} (no link to source because it has no username)"
                await self.bot.edit_message(sender.id,
                                            menu_message,
                                            f"Picked source: {link_text}\nSend a chance (from 1 to 100) of taking post for this channel.",
                                            parse_mode="html",
                                            buttons=[[Button.inline("Back ⬅️", data="manage_sources")]])
                await event.delete()
            except Exception as e:
                await event.reply("Not a valid source.")
                logger.error(f"Error occurred while getting source: {e}")

        elif user_state.startswith("add_chance") or user_state.startswith("update_chance"):
            source_id = int(user_state.split("_")[2])
            chances = [str(i) for i in range(1, 101)]
            if event.text in chances:
                _, _, menu_message, _, _ = await self.db_manager.get_admin(sender.id)
                if user_state.startswith("add_chance"):
                    await self.bot.edit_message(sender.id,
                                                menu_message,
                                                f"Chance for {source_id} is {event.text}",
                                                buttons=[[Button.inline("Add channel", data=f"add_{source_id}_{event.text}_1")],
                                                         [Button.inline("Add channel (auto approve)", data=f"add_{source_id}_{event.text}_2")],
                                                         [Button.inline("Back ⬅️", data="manage_sources")]])
                else:
                    await self.db_manager.update_chance(source_id, int(event.text))
                    await self.bot.edit_message(sender.id,
                                                menu_message,
                                                f"Chance for {source_id} was updated to {event.text}",
                                                buttons=[[Button.inline("Back ⬅️", data=f"edit_{source_id}")]])
                await event.delete()
                await self.db_manager.update_user_state(sender.id, "idle")
            else:
                await event.reply("Not a valid chance!")

        elif user_state == "adding_admin":
            admin_id = event.text
            try:
                admin_id = int(admin_id)
            except ValueError:
                pass
            try:
                admin_object = await self.bot.get_entity(admin_id)
                if not isinstance(admin_object, User):
                    await event.reply("Not a valid admin")
                    return
                uid, _, _, _, _ = await self.db_manager.get_admin(admin_object.id)
                _, _, menu_message, _, _ = await self.db_manager.get_admin(sender.id)
                if uid is not None:
                    await event.reply("Admin is already in database.")
                    return
                if admin_object.username:
                    link_text = f"<a href=https://t.me/{admin_object.username}>{admin_object.id}</a>"
                else:
                    link_text = f"{admin_object.id} (no link to admin because he has no username)"
                await self.bot.edit_message(sender.id,
                                            menu_message,
                                            f"Picked admin: {link_text}\nChoose an option below:",
                                            parse_mode="html",
                                            buttons=[[Button.inline("Add as regular admin",
                                                                    data=f"add_admin_{admin_object.id}_0")],
                                                     [Button.inline("Add as superadmin",
                                                                    data=f"add_admin_{admin_object.id}_1")],
                                                     [Button.inline("Back ⬅️",
                                                                    data="manage_admins")]]
                                            )
                await event.delete()
                await self.db_manager.update_user_state(sender.id, "idle")
            except Exception as e:
                await event.reply("Not a valid admin.")
                logger.error(f"Error occurred while getting source: {e}")

        elif user_state == "adding_watermark":
            if event.document and event.document.mime_type == "image/png":
                _, _, menu_message, _, _ = await self.db_manager.get_admin(sender.id)

                watermark_path = os.path.join(os.getcwd(), "watermark.png")
                await self.bot.download_media(event.media, file=watermark_path)
                await self.db_manager.update_setting("watermark", watermark_path)
                self.watermark = open(watermark_path, "rb")

                await self.bot.edit_message(sender.id,
                                            menu_message,
                                            "Watermark was updated",
                                            buttons=[[Button.inline("Back ⬅️", data="watermark")]]
                                            )
                await event.delete()
                await self.db_manager.update_user_state(sender.id, "idle")
            else:
                await event.reply("Not a correct watermark format.")

        elif user_state == "adding_caption":
            if event.text:
                _, _, menu_message, _, _ = await self.db_manager.get_admin(sender.id)

                caption = event.text
                await self.db_manager.update_setting("caption", caption)
                self.caption = caption

                await self.bot.edit_message(sender.id,
                                            menu_message,
                                            f"Caption was updated:\n{caption}",
                                            parse_mode="html",
                                            buttons=[[Button.inline("Back ⬅️", data="caption")]]
                                            )
                await event.delete()
                await self.db_manager.update_user_state(sender.id, "idle")
            else:
                await event.reply("Not a correct caption.")

        elif user_state == "adding_bottom_delay":
            bottom_delay = event.text
            try:
                bottom_delay_value = int(bottom_delay)
            except ValueError:
                await event.reply("Not a correct delay.")
                return
            if bottom_delay_value > 0:
                _, _, menu_message, _, _ = await self.db_manager.get_admin(sender.id)

                await self.db_manager.update_setting("bottom_delay", bottom_delay)
                self.bottom_delay = bottom_delay_value

                await self.bot.edit_message(sender.id,
                                            menu_message,
                                            f"Bottom delay was updated: {bottom_delay} mins",
                                            buttons=[[Button.inline("Back ⬅️", data="delays")]]
                                            )
                await event.delete()
                await self.db_manager.update_user_state(sender.id, "idle")

            else:
                await event.reply("Not a correct delay.")

        elif user_state == "adding_top_delay":
            top_delay = event.text
            try:
                top_delay_value = int(top_delay)
            except ValueError:
                await event.reply("Not a correct delay.")
                return
            if top_delay_value > 0:
                _, _, menu_message, _, _ = await self.db_manager.get_admin(sender.id)

                await self.db_manager.update_setting("top_delay", top_delay)
                self.top_delay = top_delay_value

                await self.bot.edit_message(sender.id,
                                            menu_message,
                                            f"Bottom delay was updated: {top_delay} mins",
                                            buttons=[[Button.inline("Back ⬅️", data="delays")]]
                                            )
                await event.delete()
                await self.db_manager.update_user_state(sender.id, "idle")

            else:
                await event.reply("Not a correct delay.")

    async def process_media(self, event):
        sender = await event.get_sender()
        if sender.id not in self.sources:
            return
        if self.media_filter(event):
            logger.info(f"New mediafile in source {sender.id}")
            _, source_state, source_chance, _ = await self.db_manager.get_source(sender.id)
            if source_state == 0:
                logger.info("Skipping mediafile due to source state (inactive)")
                return
            percent = random.randint(1, 100)
            if percent > source_chance:
                logger.info(f"Skipping mediafile due to random ({source_chance} < {percent})")
                return
            bio = BytesIO()
            if event.photo:
                bio.name = "file.png"
            elif event.video:
                bio.name = "file.mp4"

            await self.client.download_media(event.media, file=bio)
            bio.seek(0)
            media_hash = md5(bio.getbuffer()).hexdigest()
            logger.info(f"Hash of current media {media_hash}")
            stored_media_hash, _ = await self.db_manager.get_media_hash(media_hash)
            if stored_media_hash:
                logger.info(f"Skipping mediafile due to duplicate {stored_media_hash}")
                return
            else:
                await self.db_manager.add_media_hash(media_hash, datetime.now())
            if source_state == 1:
                post_id = f"{sender.id}_{event.message.id}"
                logger.info(f"No duplicate found, sending mediafile for approve")
                admins = await self.db_manager.get_admins()
                for admin in admins:
                    if admin[3] == 1:
                        confirmation_message = await self.bot.send_file(admin[0],
                                                                        file=bio,
                                                                        buttons=[[Button.inline("Approve",
                                                                                                data=f"approve_{post_id}")],
                                                                                 [Button.inline("Approve instantly",
                                                                                                data=f"approve_instantly_{post_id}")],
                                                                                 [Button.inline("Reject",
                                                                                                data=f"reject_{post_id}")]]
                                                                        )
                        bio.seek(0)
                        await self.db_manager.add_confirmation_post(post_id, admin[0], confirmation_message.id)
            elif source_state == 2:
                logger.info(f"No duplicate found, scheduling mediafile instantly")
                await self.schedule_media(sender.id, event.message.id, True)

    async def send_media_from_db(self, event):
        logger.info("Mediafile from scheduled was sent")
        source_id, message_id, _ = await self.db_manager.get_scheduled_post()
        if source_id is not None and message_id is not None:
            await self.db_manager.delete_scheduled_post(source_id, message_id)
            await self.schedule_media(source_id, message_id, True)
        else:
            logger.info("No mediafile in db to schedule")
