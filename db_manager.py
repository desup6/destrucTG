import aiosqlite
import sqlite3
import os
import logging

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                    filename="app.log",
                    filemode="a"
                    )
logger = logging.getLogger(__name__)

class DBManager:
    def __init__(self, path_to_db, drop_db=False):
        self.path_to_db = path_to_db
        if drop_db:
            logger.info(f"Dropping {path_to_db}")
            try:
                os.remove(path_to_db)
                logger.info(f"{path_to_db} dropped")
            except OSError as e:
                logger.error(f"Error while dropping db: {e}")
        try:
            connection = sqlite3.connect(path_to_db)
            cursor = connection.cursor()
            cursor.execute("CREATE TABLE IF NOT EXISTS Admins (UserId INTEGER, UserState TEXT, MenuMessage INTEGER, Subscription INTEGER, SuperAdmin INTEGER)")
            cursor.execute('CREATE TABLE IF NOT EXISTS Sources (ChannelId INTEGER, State INTEGER, Chance INTEGER, PostsAmount INTEGER)')
            cursor.execute('CREATE TABLE IF NOT EXISTS Settings (SettingName TEXT, SettingValue TEXT)')
            cursor.execute('CREATE TABLE IF NOT EXISTS ConfirmationPosts (PostId TEXT, AdminId INTEGER, AdminMessageId INTEGER)')
            cursor.execute('CREATE TABLE IF NOT EXISTS ScheduledPosts (ChannelId INTEGER, MessageId INTEGER, TimeAdded TIMESTAMP)')
            cursor.execute('CREATE TABLE IF NOT EXISTS Hashes (MediaHash TEXT, Date TIMESTAMP)')
            connection.commit()
            logger.info("All tables successfully created")
        except Exception as e:
            logger.error(f"Error while creating tables: {e}")

    async def add_admin(self, user_id, user_state, menu_message, subscription, super_admin):
        async with aiosqlite.connect(self.path_to_db) as db:
            await db.execute("INSERT INTO Admins (UserID, UserState, MenuMessage, Subscription, SuperAdmin) VALUES(?, ?, ?, ?, ?)",
                             (user_id, user_state, menu_message, subscription, super_admin))
            await db.commit()

    async def delete_admin(self, user_id):
        async with aiosqlite.connect(self.path_to_db) as db:
            await db.execute("DELETE FROM Admins WHERE UserId=?", (user_id,))
            await db.commit()

    async def get_admin(self, user_id):
        async with aiosqlite.connect(self.path_to_db) as db:
            async with db.execute("SELECT * FROM Admins WHERE UserId=? LIMIT 1", (user_id,)) as cursor:
                res = await cursor.fetchone()
            if res is None:
                return None, None, None, None, None
            return res

    async def get_admins(self):
        async with aiosqlite.connect(self.path_to_db) as db:
            async with db.execute("SELECT * FROM Admins") as cursor:
                res = await cursor.fetchall()
            return res

    async def update_user_state(self, user_id, user_state):
        async with aiosqlite.connect(self.path_to_db) as db:
            await db.execute("UPDATE Admins SET UserState=? WHERE UserId=?", (user_state, user_id))
            await db.commit()

    async def update_menu_message(self, user_id, menu_message):
        async with aiosqlite.connect(self.path_to_db) as db:
            await db.execute("UPDATE Admins SET MenuMessage=? WHERE UserId=?", (menu_message, user_id))
            await db.commit()

    async def update_subscription(self, user_id, subscription):
        async with aiosqlite.connect(self.path_to_db) as db:
            await db.execute("UPDATE Admins SET Subscription=? WHERE UserId=?", (subscription, user_id))
            await db.commit()

    async def update_super_admin(self, user_id, super_admin):
        async with aiosqlite.connect(self.path_to_db) as db:
            await db.execute("UPDATE Admins SET SuperAdmin=? WHERE UserId=?", (super_admin, user_id))
            await db.commit()

    async def add_source(self, channel_id, state, chance, posts_amount):
        async with aiosqlite.connect(self.path_to_db) as db:
            await db.execute("INSERT INTO Sources (ChannelId, State, Chance, PostsAmount) VALUES(?, ?, ?, ?)",
                             (channel_id, state, chance, posts_amount))
            await db.commit()

    async def delete_source(self, channel_id):
        async with aiosqlite.connect(self.path_to_db) as db:
            await db.execute("DELETE FROM Sources WHERE ChannelId=?", (channel_id,))
            await db.commit()

    async def get_source(self, channel_id):
        async with aiosqlite.connect(self.path_to_db) as db:
            async with db.execute("SELECT * FROM Sources WHERE ChannelId=? LIMIT 1", (channel_id,)) as cursor:
                res = await cursor.fetchone()
            if res is None:
                return None, None, None, None
            return res

    async def get_sources(self):
        async with aiosqlite.connect(self.path_to_db) as db:
            async with db.execute("SELECT * FROM Sources") as cursor:
                res = await cursor.fetchall()
            return res

    async def update_state(self, channel_id, state):
        async with aiosqlite.connect(self.path_to_db) as db:
            await db.execute("UPDATE Sources SET State=? WHERE ChannelId=?", (state, channel_id))
            await db.commit()

    async def update_chance(self, channel_id, chance):
        async with aiosqlite.connect(self.path_to_db) as db:
            await db.execute("UPDATE Sources SET Chance=? WHERE ChannelId=?", (chance, channel_id))
            await db.commit()

    async def update_posts_amount(self, channel_id, posts_amount):
        async with aiosqlite.connect(self.path_to_db) as db:
            await db.execute("UPDATE Sources SET PostsAmount=? WHERE ChannelId=?", (posts_amount, channel_id))
            await db.commit()

    async def add_setting(self, setting_name, setting_value):
        async with aiosqlite.connect(self.path_to_db) as db:
            await db.execute("INSERT INTO Settings(SettingName, SettingValue) VALUES(?, ?)", (setting_name, setting_value))
            await db.commit()

    async def update_setting(self, setting_name, setting_value):
        async with aiosqlite.connect(self.path_to_db) as db:
            await db.execute("UPDATE Settings SET SettingValue=? WHERE SettingName=?", (setting_value, setting_name))
            await db.commit()

    async def get_setting(self, setting_name):
        async with aiosqlite.connect(self.path_to_db) as db:
            async with db.execute("SELECT * FROM Settings WHERE SettingName=?", (setting_name,)) as cursor:
                res = await cursor.fetchone()
            if res is None:
                return None, None
            return res

    async def add_confirmation_post(self, post_id, admin_id, admin_message_id):
        async with aiosqlite.connect(self.path_to_db) as db:
            await db.execute("INSERT INTO ConfirmationPosts (PostId, AdminId, AdminMessageId) VALUES(?, ?, ?)", (post_id, admin_id, admin_message_id))
            await db.commit()

    async def delete_confirmation_posts(self, post_id):
        async with aiosqlite.connect(self.path_to_db) as db:
            await db.execute("DELETE FROM ConfirmationPosts WHERE PostId=?", (post_id,))
            await db.commit()

    async def get_confirmation_posts(self, post_id):
        async with aiosqlite.connect(self.path_to_db) as db:
            async with db.execute("SELECT * FROM ConfirmationPosts WHERE PostId=?", (post_id,)) as cursor:
                res = await cursor.fetchall()
            return res

    async def add_scheduled_post(self, channel_id, message_id, time_added):
        async with aiosqlite.connect(self.path_to_db) as db:
            await db.execute("INSERT INTO ScheduledPosts (ChannelId, MessageId, TimeAdded) VALUES(?, ?, ?)", (channel_id, message_id, time_added))
            await db.commit()

    async def delete_scheduled_post(self, channel_id, message_id):
        async with aiosqlite.connect(self.path_to_db) as db:
            await db.execute("DELETE FROM ScheduledPosts WHERE ChannelId=? AND MessageId=?", (channel_id, message_id))
            await db.commit()

    async def delete_scheduled_posts(self, channel_id):
        async with aiosqlite.connect(self.path_to_db) as db:
            await db.execute("DELETE FROM ScheduledPosts WHERE ChannelId=?", (channel_id,))
            await db.commit()

    async def get_scheduled_post(self):
        async with aiosqlite.connect(self.path_to_db) as db:
            async with db.execute("SELECT * FROM ScheduledPosts ORDER BY TimeAdded ASC LIMIT 1") as cursor:
                res = await cursor.fetchone()
            if res is None:
                return None, None, None
            return res

    async def add_media_hash(self, media_hash, date):
        async with aiosqlite.connect(self.path_to_db) as db:
            await db.execute("INSERT INTO Hashes (MediaHash, Date) VALUES(?, ?)", (media_hash, date))
            await db.commit()

    async def delete_media_hash(self, media_hash):
        async with aiosqlite.connect(self.path_to_db) as db:
            await db.execute("DELETE FROM Hashes WHERE MediaHash=?", (media_hash,))
            await db.commit()

    async def get_media_hash(self, media_hash):
        async with aiosqlite.connect(self.path_to_db) as db:
            async with db.execute("SELECT * FROM Hashes WHERE MediaHash=? LIMIT 1", (media_hash,)) as cursor:
                res = await cursor.fetchone()
            if res is None:
                return None, None
            return res