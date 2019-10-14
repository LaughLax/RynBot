from discord import File
from discord.ext.commands import Cog, command
from discord.ext.tasks import loop

from io import BytesIO

from util import misc


class Tasks(Cog):
    def __init__(self, bot):
        self.bot = bot

        self.task_options = {'rolechart': self.role_chart}

        self.hourly_task_run.start()

    def cog_unload(self):
        self.hourly_task_run.cancel()
        pass

    async def role_chart(self, server_id, channel_id):
        chart_cog = self.bot.get_cog('Chart')
        channel = self.bot.get_channel(channel_id)

        with BytesIO() as f:
            f = await chart_cog.role_chart_wrapper(server_id, f)
            msg = await channel.send(file=File(fp=f, filename="rolechart.png"))

        return msg.id

    @command()
    async def create_task(self, ctx, task_name, *, job):
        if job not in self.task_options:
            await ctx.send('That\'s not a scheduleable task! Options are: {}'.format(list(self.task_options.keys())))
        else:
            msg_id = await self.task_options[job](ctx.guild.id, ctx.channel.id)
            await self.bot.db.create_task(ctx.guild.id, ctx.channel.id, task_name, job, msg_id)

    @command()
    async def delete_task(self, ctx, task_name):
        try:
            await self.bot.db.delete_task(ctx.guild.id, task_name)
            await ctx.send('Task \'{}\' deleted.'.format(task_name))
        except Exception as e:
            await ctx.send('Something went wrong...')

    @loop(hours=1)
    async def hourly_task_run(self):
        tasks = await self.bot.db.fetch_task_list()
        for task in tasks:
            channel = self.bot.get_channel(task.channel)
            old_msg = await misc.get_message(channel, task.last_run_msg_id)

            msg_id = await self.task_options[task.command](task.server, task.channel)
            # await self.task_options['chart roles'](329681826618671104, 382657596458270720)
            await self.bot.db.update_task(task.server, task.task_name, msg_id)
            await old_msg.delete()

    @hourly_task_run.before_loop
    async def before_hourly_task(self):
        await self.bot.wait_until_ready()


def setup(bot):
    bot.add_cog(Tasks(bot))
