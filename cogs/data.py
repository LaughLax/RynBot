import discord
from discord.ext import commands
from util import misc

from datetime import datetime
import pytz
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
        self.force_db_close()
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

    def force_db_close(self):
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
                cur.executemany('INSERT IGNORE INTO server_pop_temp (Server, Datetime, UserCount) VALUES (%s, %s, %s)', rows)
                self.db.commit()
                cur.close()
                self.close_db()
                last_hour = now.hour
            await asyncio.sleep(60 * 10)

    @commands.group()
    async def data(self, ctx):
        pass

    @data.command()
    async def population(self, ctx, server=None):
        if not server or ctx.message.author.id != misc.ryn_id:
            server = ctx.guild
        else:
            server = self.bot.get_guild(int(server))

        self.open_db()
        cur = self.db.cursor()
        cur.execute('SELECT Datetime, UserCount FROM server_pop_temp WHERE Server = %s', (server.id,))
        rows = np.array(cur.fetchall())
        cur.close()
        self.close_db()

        plt.clf()
        plt.plot(rows[:,0], rows[:,1])
        plt.xticks(rotation=45)
        plt.xlabel("Date")
        plt.ylabel("Member count")
        plt.title("Membership growth for server: {0.name}".format(server))
        plt.tight_layout()

        with io.BytesIO() as f:
            plt.savefig(f, format='png')
            await ctx.send(file=discord.File(fp=f.getbuffer(), filename="userchart.png"))
        plt.close()

    @data.command()
    async def population2(self, ctx, server=None):
        if not server or ctx.message.author.id != misc.ryn_id:
            server = ctx.guild
        else:
            server = self.bot.get_guild(int(server))
            if server is None:
                await ctx.send("I'm not in that server.")
                return

        self.open_db()
        cur = self.db.cursor()
        cur.execute('SELECT Datetime, UserCount FROM server_pop_temp WHERE Server = %s ORDER BY Datetime', (server.id,))
        rows = np.array(cur.fetchall())
        cur.close()
        self.close_db()

        f = lambda x: x.replace(tzinfo=get_localzone())
        rows[:, 0] = np.array(list(map(f, rows[:, 0])))

        members = []
        for a in server.members:
            # if a.joined_at <= rows[0,0]:
            members.append(a)

        members.sort(key=lambda mem: mem.joined_at)
        (x, y) = ([], [])
        cutoff = datetime(2019, 3, 5, 0, 0, 0, 0)
        for m in range(len(members)):
            joined_at = members[m].joined_at
            if joined_at <= cutoff:
                continue
            if m > 0:
                x.append(joined_at)
                y.append(m)
            x.append(joined_at)
            y.append(m+1)
        x.append(ctx.message.created_at)
        y.append(len(members))

        plt.clf()
        plt.plot(x, y, 'b', rows[:,0], rows[:,1], 'k')
        plt.xticks(rotation=45)
        plt.xlabel("Date")
        plt.ylabel("Member count")
        plt.title("Membership growth for server: {0.name}".format(server))
        plt.tight_layout()

        with io.BytesIO() as f:
            plt.savefig(f, format='png')
            await ctx.send(file=discord.File(fp=f.getbuffer(), filename="userchart.png"))
        plt.close()


def setup(bot):
    bot.add_cog(Data(bot))
