import discord
from discord.ext import commands
from datetime import datetime
from tzlocal import get_localzone

import mysql.connector
import asyncio

import numpy as np
import io
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


class Data(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.db = None
        self.processes_using_db = 0

        self.hourly_check_task = self.bot.loop.create_task(self.hourly_pop_check())

    def cog_unload(self):
        self.close_db()
        self.hourly_check_task.cancel()

    def open_db(self):
        if not self.db:
            try:
                self.db = mysql.connector.connect(user='pi', unix_socket='/var/run/mysqld/mysqld.sock', host='localhost', database='rynbot')
                self.processes_using_db += 1
            except mysql.connector.Error as err:
                self.db = None
                print(err)
                raise err
        return self.db

    def close_db(self):
        if self.db:
            self.processes_using_db -= 1
            if self.processes_using_db == 0:
                self.db.close()
                self.db = None

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
                cur.executemany('INSERT INTO server_pop_temp (Server, Datetime, UserCount) VALUES (%s, %s, %s)', rows)
                self.db.commit()
                cur.close()
                self.close_db()
                last_hour = now.hour
            await asyncio.sleep(60 * 10)

    @commands.group()
    async def data(self, ctx):
        pass

    @data.command()
    async def population(self, ctx):
        self.open_db()
        cur = self.db.cursor()
        cur.execute('SELECT Datetime, UserCount FROM server_pop_temp WHERE Server = %s', (ctx.guild.id,))
        rows = np.array(cur.fetchall())
        cur.close()
        self.close_db()

        plt.clf()
        plt.plot(rows[0,:], rows[1,:])
        plt.xticks(rotation=45)
        plt.xlabel("Date")
        plt.ylabel("Member count")
        plt.title("Membership growth for server: {0.name}".format(ctx.guild))
        plt.tight_layout()

        with io.BytesIO() as f:
            plt.savefig(f, format='png')
            await ctx.send(file=discord.File(fp=f.getbuffer(), filename="userchart.png"))
        plt.close()


def setup(bot):
    bot.add_cog(Data(bot))
