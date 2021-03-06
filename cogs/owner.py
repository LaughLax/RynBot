import ast
import cProfile
import io
import math
import pstats
import subprocess

import discord
import psutil
from discord import Activity
from discord import ActivityType
from discord import Embed
from discord import Member
from discord import Role
from discord import TextChannel
from discord.errors import NotFound
from discord.ext import commands
from discord.ext.commands import Cog
from discord.ext.commands import Group
from discord.ext.commands import Paginator
from discord.ext.commands import command
from discord.ext.commands import group

from util import config
from util.misc import MyEmbed
# TODO Clean up imports


class Owner(Cog):
    """Commands for Ryn's use. Attempts by others will be logged."""
    def __init__(self, bot):
        self.bot = bot

    def cog_check(self, ctx):
        """Check to see if the bot owner issued the command."""
        is_owner = ctx.message.author.id == config.owner_id
        if (not is_owner) and (not ctx.invoked_with == "help"):
            print('{} tried to run an owner-restricted command ({})'.format(ctx.message.author, ctx.invoked_with))
        return is_owner

    @group()
    async def cog(self, ctx):
        """Commands for managing cogs."""

        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @cog.command()
    async def load(self, ctx, name: str):
        """Add a cog to the bot."""

        if name.startswith('cogs.'):
            name = name.split('.', 1)[1]

        self.bot.load_extension('cogs.{}'.format(name))
        await ctx.send('Cog \'{}\' successfully added.'.format(name))

    @cog.command()
    async def unload(self, ctx, name: str):
        """Remove a cog from the bot."""

        if name.startswith('cogs.'):
            name = name.split('.', 1)[1]

        if name.lower() == 'owner' and ctx.invoked_with.lower() != 'reload':
            await ctx.send('Cannot unload the owner cog unless performing a reload.')
        else:
            self.bot.unload_extension('cogs.{}'.format(name))
            await ctx.send('Cog \'{}\' successfully removed.'.format(name))

    @cog.command(name='reload')
    async def _cog_reload(self, ctx, name: str = 'all'):
        """Remove and then re-add a cog to the bot."""

        if name.lower() == 'all':
            for ex in self.bot.extensions:
                self.bot.reload_extension(ex)
        else:
            self.bot.reload_extension('cogs.{}'.format(name))

        await ctx.send('Reload operation successful.')

    @cog.command(aliases=['show'])
    async def list(self, ctx):
        """Lists all cogs currently loaded."""
        paginator = Paginator()

        for ex in self.bot.extensions:
            paginator.add_line(ex)

        for page in paginator.pages:
            await ctx.send(page)

    @command()
    async def renamebot(self, ctx, name: str):
        """Change RynBot's name"""

        await self.bot.user.edit(username=name)
        await ctx.send("Bot username changed.")

    @command()
    async def git(self, ctx, *, args: str = ''):
        """Git, plain and 'simple.'

        Run the specified git command on the server and display the result."""

        paginator = Paginator()

        stream = subprocess.run(['git {}'.format(args)], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if stream.stdout is not None:
            paginator.add_line("STDOUT:")
            for line in str(stream.stdout.decode('utf-8')).split('\n'):
                paginator.add_line(line)

        if stream.stderr is not None:
            paginator.add_line("\nSTDERR:")
            for line in str(stream.stderr.decode('utf-8')).split('\n'):
                paginator.add_line(line)

        for p in paginator.pages:
            await ctx.send(p)

    @group()
    async def db(self, ctx):
        pass

    @db.command(name='reload')
    async def _db_reload(self, ctx):
        self.bot.unload_extension('database.handler')
        self.bot.load_extension('database.handler')

        await ctx.send('Reload operation successful.')

    @db.command()
    async def upgrade(self, ctx):
        paginator = Paginator()

        stream = subprocess.run(['alembic', 'upgrade', 'head'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if stream.stdout is not None:
            paginator.add_line("STDOUT:")
            for line in str(stream.stdout.decode('utf-8')).split('\n'):
                paginator.add_line(line)

        if stream.stderr is not None:
            paginator.add_line("\nSTDERR:")
            for line in str(stream.stderr.decode('utf-8')).split('\n'):
                paginator.add_line(line)

        for p in paginator.pages:
            await ctx.send(p)

    @command()
    async def update(self, ctx):
        """Calls an update script and exits.

        This command should only be run if the bot's core needs updating.
        Also, it doesn't work so it's commented out.
        If it did work, it would call update.sh, which:
        * Waits for the bot process to end
        * Does a git pull
        * Starts the bot"""
        pass
        # print("Calling update.sh")
        # subprocess.Popen(["./update.sh"],
        #                  cwd=os.getcwd(),
        #                  stdout=subprocess.PIPE,
        #                  stderr=subprocess.STDOUT)
        # print("Quitting")
        # await self.bot.logout()

    @command()
    async def reboot(self, ctx):
        """Reboot the server running RynBot"""

        await ctx.send('Going down, be back soon!')
        for ex in list(self.bot.extensions.keys()):
            self.bot.unload_extension(ex)
        subprocess.run(['reboot'], shell=True)

    @command()
    async def quit(self, ctx):
        """Log out and terminate the bot process"""
        await ctx.send('No, please don\'t kill me!')
        for ex in list(self.bot.extensions.keys()):
            self.bot.unload_extension(ex)
        await self.bot.logout()

    @group(hidden=True)
    async def sneak(self, ctx):
        """This group contains some sneaky-sneaky stuff."""

        if ctx.invoked_subcommand is None:
            await ctx.invoke(self.bot.get_command('help'), 'sneak')

    @sneak.command(name='hiddenchannels')
    async def hidden_channels(self, ctx, server_id: str = None, print_local: bool = False):
        if server_id is None or server_id.lower() == "here":
            server = ctx.guild
        else:
            server = self.bot.get_guild(int(server_id))
            if server is None:
                await ctx.send("I'm not in that server.")
                return

        title = "Hidden Channels in Server: {0.name} (ID: {0.id})".format(server)

        chans = server.channels
        hidden_channels = []
        for a in chans:
            if type(a) == TextChannel and not a.permissions_for(server.me).read_messages:
                hidden_channels.append(a)

        hidden_channels.sort(key=lambda chan: chan.name)

        num_segments = int(len(hidden_channels)/25) + 1
        for b in range(num_segments):
            em = MyEmbed(bot=ctx.me)
            em.set_thumbnail(url=server.icon_url)

            footer = "Page {}/{}".format(b+1, num_segments)
            em.set_footer(text=footer)

            for a in hidden_channels[b*25:b*25+24]:
                if a.topic is not None and a.topic != "":
                    em.add_field(name=a.name, value=a.topic)
                else:
                    em.add_field(name=a.name, value="(No channel topic)")

            if print_local:
                await ctx.send(embed=em)
            else:
                await self.bot.get_channel(329691231498272769).send(embed=em)

        await ctx.message.delete()

    @sneak.command()
    async def channels(self, ctx, server_id: str = None, print_local: bool = False):
        if server_id is None or server_id.lower() == "here":
            server = ctx.guild
        else:
            server = self.bot.get_guild(int(server_id))
            if server is None:
                await ctx.send("I'm not in that server.")
                return

        title = str.format("Server: {0.name} (ID {0.id})", server)

        chans = server.channels
        text_avail = []
        text_hidden = []
        for a in chans:
            if type(a) is TextChannel:
                if a.permissions_for(server.me).read_messages:
                    text_avail.append(a.name)
                else:
                    text_hidden.append(a.name)

        text_avail.sort()
        text_hidden.sort()

        display_size = 40
        num_segments = int(max(len(text_avail)/display_size, len(text_hidden)/display_size)) + 1

        for b in range(num_segments):
            start = b*display_size
            end = (b+1)*display_size - 1
            em = MyEmbed(bot=ctx.me, title=title)

            if text_avail[start:end]:
                text_avail_body = "\n".join(text_avail[start:end])
                em.add_field(name='Unhidden text channels', value=text_avail_body)

            if text_hidden[start:end]:
                text_hidden_body = "\n".join(text_hidden[start:end])
                em.add_field(name='Hidden text channels', value=text_hidden_body)

            icon_url = server.icon_url
            em.set_thumbnail(url=icon_url)

            footer = "Page {}/{}".format(b+1, num_segments)
            em.set_footer(text=footer)

            if print_local:
                await ctx.send(embed=em)
            else:
                await self.bot.get_channel(329691248707502100).send(embed=em)

        if ctx.me.permissions_in(ctx.channel).manage_messages:
            await ctx.message.delete()

    @sneak.command()
    async def roles(self, ctx, server_id: str = None, print_local: bool = False):

        if server_id is None or server_id.lower() == "here":
            server = ctx.guild
        else:
            server = self.bot.get_guild(int(server_id))
            if server is None:
                await ctx.send("I'm not in that server.")
                return

        title = "Server: {0.name} (ID {0.id})".format(server)

        role_list = []
        for a in server.roles:
            if not a.is_default():
                role_list.append("({:d}) {}".format(len(a.members), a.name))
        role_list.reverse()

        display_size = 60
        num_segments = int(len(role_list)/display_size) + 1
        for b in range(num_segments):
            embed = MyEmbed(bot=ctx.me, title=title)
            embed.set_thumbnail(url=server.icon_url)

            embed.add_field(name='Roles', value='\n'.join(role_list[b*display_size:(b+1)*display_size-1]))

            footer = "Page {}/{}".format(b+1, num_segments)
            embed.set_footer(text=footer)

            if print_local:
                await ctx.send(embed=embed)
            else:
                await self.bot.get_channel(329691241111355392).send(embed=embed)

        if ctx.me.permissions_in(ctx.channel).manage_messages:
            await ctx.message.delete()

    @command()
    async def set_status(self, ctx, status_type: int, *, text):
        """Set the bot's presence"""
        tp = {
            0: ActivityType.playing,
            1: ActivityType.streaming,
            2: ActivityType.watching,
            3: ActivityType.listening,
        }.get(status_type)
        game = Activity(type=tp, name=text)
        await self.bot.change_presence(activity=game)

    @command()
    async def profile(self, ctx, *, cmd):
        # TODO this next line causes an error if it's profiling a zero-arg command (ie `profile channels`)
        try:
            [cmd_string, args] = cmd.split(maxsplit=1)
        except ValueError:
            cmd_string = cmd
            args = ''
        while isinstance(self.bot.get_command(cmd_string), Group):
            splat = args.split(maxsplit=1)
            cmd_string += ' ' + splat[0]
            args = splat[1] if len(splat) > 1 else ''

        pr = cProfile.Profile()

        pr.enable()
        if args != '':
            await ctx.invoke(self.bot.get_command(cmd_string), args)
        else:
            await ctx.invoke(self.bot.get_command(cmd_string))
        pr.disable()
        pr.create_stats()

        # s = io.StringIO()

        paginator = Paginator()

        with io.StringIO() as s:
            ps = pstats.Stats(pr, stream=s).strip_dirs().sort_stats('tottime')
            ps.print_stats()

            for line in s.getvalue().split('\n'):
                paginator.add_line(line)

        # for p in paginator.pages:
        await ctx.send(paginator.pages[0])

    @command()
    async def usersearch(self, ctx, *, name: str = None):
        """Look up the ID of a user"""
        if name is None:
            await ctx.send("You didn't give me someone to search for.")
            return

        users = ctx.message.mentions
        if not users:
            users = list(filter(lambda u: name in u.name, self.bot.users))
        if not users:
            await ctx.send('Could not find user `{}`.'.format(name))
            return

        if hasattr(users, '__iter__'):
            if len(users) > 100:
                await ctx.send("Over 100 matching users.")
            else:
                try:
                    max_length = len(max(users, key=lambda u: len(u.name)).name)
                except ValueError:
                    await ctx.send('Could not find user `{}`.'.format(name))
                    return

                paginator = Paginator(prefix="```{head:>{n_len}}#xxxx | ID".format(head="User", n_len=max_length))

                for user in users:
                    paginator.add_line("{username:>{n_len}}#{discrim} | {user_id}".format(username=user.name, n_len=max_length, discrim=user.discriminator, user_id=user.id))
                for p in paginator.pages:
                    await ctx.send(p)
        else:
            await ctx.send("The ID of user `{}` is `{}`.".format(name, users[0].id))

    @command()
    async def user_servers(self, ctx, user_id: int):
        user_guilds = []
        for guild in self.bot.guilds:
            if guild.get_member(user_id):
                user_guilds.append(guild)

        if not user_guilds:
            await ctx.send('I have no servers in common with that user.')
            return

        paginator = Paginator()
        paginator.add_line("User with ID {} is in {} servers with me.\n".format(user_id, len(user_guilds)))

        max_name_length = len(max(user_guilds, key=lambda g: len(g.name)).name)

        for guild in user_guilds:
            mem = guild.get_member(user_id)
            nick = mem.nick
            if not nick:
                nick = mem.name
            paginator.add_line("{0.name:<{n_len}} | ({n})".format(guild, n_len=max_name_length, n=nick))

        for p in paginator.pages:
            await ctx.send(p)

    @command(aliases=['msg'])
    async def message(self, ctx, user_id: int = None, *, message: str = None):
        """Send a message to a user"""
        if user_id is not None and message is not None:
            try:
                user = self.bot.get_user(user_id)
            except NotFound:
                await ctx.send("Invalid user ID.")
                return

            if message.count("`") % 2 == 1:
                message = message + "`"
            await user.send("{}\n\n`This message was sent to you by my owner, Ryndinovaia#0903. To send him a message, use the `_owner` command.`".format(message))
        else:
            await ctx.send("Not enough arguments.")

    @command()
    async def servers(self, ctx):
        guilds = self.bot.guilds
        num_guilds = len(guilds)

        paginator = Paginator()
        paginator.add_line("I am in {} servers, totalling {} unique members.\n".format(num_guilds, len(self.bot.users)))

        max_name_length = len(max(guilds, key=lambda g: len(g.name)).name)
        max_num_length = int(math.log(max(g.member_count for g in guilds), 10) // 1 + 1)

        for g in guilds:
            # TODO Reorder output to put guild name last
            paginator.add_line("{0.name:<{n_len}} | {0.member_count:{m_len}d} members | {0.id}".format(g, n_len=max_name_length, m_len=max_num_length))

        for p in paginator.pages:
            await ctx.send(p)

    @command()
    async def eval_fn(self, ctx, *, cmd):
        """Evaluates input.
        Input is interpreted as newline seperated statements.
        If the last statement is an expression, that is the return value.
        Usable globals:
          - `bot`: the bot instance
          - `discord`: the discord module
          - `commands`: the discord.ext.commands module
          - `ctx`: the invokation context
          - `__import__`: the builtin `__import__` function
        Such that `>eval 1 + 1` gives `2` as the result.
        The following invokation will cause the bot to send the text '9'
        to the channel of invokation and return '3' as the result of evaluating
        >eval ```
        a = 1 + 2
        b = a * 2
        await ctx.send(a + b)
        a
        ```


        Lifted from https://gist.github.com/nitros12/2c3c265813121492655bc95aa54da6b9"""

        fn_name = "_eval_expr"

        cmd_orig = cmd.strip("` ")

        # add a layer of indentation
        cmd = "\n".join("\t{}".format(i) for i in cmd_orig.splitlines())

        # wrap in async def body
        body = "async def {}():\n{}".format(fn_name, cmd)

        parsed = ast.parse(body)
        body = parsed.body[0].body

        def insert_returns(_body):
            # insert return stmt if the last expression is a expression statement
            if isinstance(_body[-1], ast.Expr):
                _body[-1] = ast.Return(_body[-1].value)
                ast.fix_missing_locations(_body[-1])

            # for if statements, we insert returns into the body and the orelse
            if isinstance(_body[-1], ast.If):
                insert_returns(_body[-1].body)
                insert_returns(_body[-1].orelse)

            # for with blocks, again we insert returns into the body
            if isinstance(_body[-1], ast.With):
                insert_returns(_body[-1].body)

        insert_returns(body)

        env = {
            'bot': self.bot,
            'discord': discord,
            'commands': commands,
            'ctx': ctx,
            '__import__': __import__
        }
        exec(compile(parsed, filename="<ast>", mode="exec"), env)

        result = str(await eval("{}()".format(fn_name), env))

        embed = MyEmbed(bot=ctx.me)
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url_as(format='png'))

        embed.add_field(name='Code', value=('```python\n' + cmd_orig + '```'), inline=False)
        embed.add_field(name='Result', value=('```\n' + result + '```'), inline=False)
        
        await ctx.send(embed=embed)

    @command()
    async def status(self, ctx):
        main_proc = psutil.Process()
        main_proc_mem = main_proc.memory_info().rss / 1024 / 1024

        children = main_proc.children(recursive=True)
        children_mem = sum([c.memory_info().rss for c in children]) / 1024 / 1024

        redis = None
        for p in psutil.process_iter(['name']):
            if p.info['name'] == 'redis-server':
                redis = p
        if redis is not None:
            redis_mem = redis.memory_info().rss / 1024 / 1024

        db_size = await self.bot.db.get_db_size()

        em = MyEmbed(bot=ctx.me)

        em.add_field(name='Main Process Memory Usage', value=f'{main_proc_mem:3.1f} MB')
        em.add_field(name='Children Memory Usage', value=f'{children_mem:3.1f} MB ({len(children)} children)')
        if redis is not None:
            em.add_field(name='Cache Memory Usage', value=f'{redis_mem:3.1f} MB')
        else:
            em.add_field(name='Cache Memory Usage', value='Unknown')
        em.add_field(name='Database Disk Usage', value=f'{db_size:3.1f} MB')
        
        await ctx.send(embed=em)


def setup(bot):
    bot.add_cog(Owner(bot))
