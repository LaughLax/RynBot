from discord.ext import commands
from datetime import datetime
from tzlocal import get_localzone
import mysql.connector
import asyncio


class Data(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.db = None

        self.hourly_check_task = self.bot.loop.create_task(self.hourly_pop_check())

    def cog_unload(self):
        self.close_db()
        self.hourly_check_task.cancel()

    def open_db(self):
        if not self.db:
            try:
                self.db = mysql.connector.connect(user='pi', unix_socket='/var/run/mysqld/mysqld.sock', host='localhost', database='rynbot')
            except mysql.connector.Error as err:
                self.db = None
                print(err)
                raise err
        return self.db

    def close_db(self):
        if self.db:
            self.db.close()

    async def hourly_pop_check(self):
        await self.bot.wait_until_ready()
        last_hour = -1
        while not self.bot.is_closed():
            now = datetime.now(get_localzone())
            if now.hour != last_hour:
                rows = []
                for server in self.bot.guilds:
                    rows.append((server.id,
                                 now.replace(minute=0, second=0, microsecond=0),
                                 server.member_count))
                self.open_db()
                cur = self.db.cursor()
                cur.executemany("INSERT INTO server_pop_temp (Server, Datetime, UserCount) VALUES (%s, %s, %s)", rows)
                self.db.commit()
                cur.close()
                self.close_db()
                last_hour = now.hour
            await asyncio.sleep(60 * 10)


def setup(bot):
    bot.add_cog(Data(bot))
