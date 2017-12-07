import discord
from discord.ext import commands
import subprocess


class Owner:
    """This cog is purely for Ryn's use. Attempts by others will be logged."""
    def __init__(self, bot):
        self.bot = bot

    def __local_check(self, ctx):
        """Checks to see if Ryn issued the command."""
        is_ryn = ctx.message.author.id == 185095270986547200
        if not is_ryn:
            print('{} tried to run an owner-restricted command ({})'.format(ctx.message.author, ctx.invoked_with))
        return is_ryn

    @commands.group()
    async def cog(self, ctx):
        """Commands for managing cogs."""

        if ctx.invoked_subcommand is None:
            await ctx.invoke(self.bot.get_command('help'), 'util')

    @cog.command()
    async def load(self, ctx, name: str):
        """Adds a cog to the bot."""

        if name.startswith('cogs.'):
            name = name.split('.', 1)[1]

        self.bot.load_extension('cogs.{}'.format(name))
        await ctx.send('Cog \'{}\' successfully added.'.format(name))
        # await ctx.invoke(self.bot.get_command('help'), name.lower())

    @cog.command()
    async def unload(self, ctx, name: str):
        """Removes a cog from the bot."""

        if name.startswith('cogs.'):
            name = name.split('.', 1)[1]

        if name.lower() == 'owner' and ctx.invoked_with.lower() != 'reload':
            await ctx.send('Cannot unload the owner cog unless performing a reload.')
        else:
            self.bot.unload_extension('cogs.{}'.format(name))
            await ctx.send('Cog \'{}\' successfully removed.'.format(name))

    @cog.command()
    async def reload(self, ctx, name: str):
        """Removes and then re-adds a cog to the bot."""

        if name.lower() == 'all':
            for ex in self.bot.extensions:
                self.bot.unload_extension(ex)
                self.bot.load_extension(ex)
        else:
            self.bot.unload_extension('cogs.{}'.format(name))
            self.bot.load_extension('cogs.{}'.format(name))

        await ctx.send('Reload operation successful.')

    @cog.command()
    async def list(self, ctx):
        """Lists all cogs currently loaded."""
        paginator = commands.Paginator()

        for ex in self.bot.extensions:
            paginator.add_line(ex)

        for page in paginator.pages:
            await ctx.send(page)
            # await ctx.message.author.send(page)

    @cog.error
    @load.error
    @unload.error
    @reload.error
    async def cog_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send('Not enough arguments supplied.')
        else:
            raise error

    @commands.command()
    async def renamebot(self, ctx, name: str):
        await self.bot.user.edit(username=name)
        await ctx.send("Bot username changed.")

    @commands.command()
    async def git(self, ctx, *, args: str = ''):
        """Git, plain and 'simple.'

        Runs the specified git command on the server and displays the result."""

        paginator = commands.Paginator()

        stream = subprocess.run(['git {}'.format(args)], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if stream.stdout is not None:
            for line in str(stream.stdout.decode('utf-8')).split('\n'):
                paginator.add_line(line)
        elif stream.stderr is not None:
            for line in str(stream.stderr.decode('utf-8')).split('\n'):
                paginator.add_line(line)
        else:
            print('wtf')

        for p in paginator.pages:
            await ctx.send(p)

        """
        if len(args) < 2:
            ctx.send('Not enough arguments.')
            return
        if args[1].lower() == 'pull':
            if len(args) > 1 and args[2].lower() == 'harder':
                return_code = subprocess.run(['git','checkout','-f','.'])
                if return_code > 0:
                    ctx.send('Checkout failed.')
                    return
            return_code = subprocess.run(['git','pull'])
            if return_code == 0:
                ctx.send('Git pull successful.')
            else:
                ctx.send('Git pull failed. You might try pulling harder next time.')
        """

    @commands.command()
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

    @commands.command()
    async def quit(self, ctx):
        """Logs out and terminates the bot process."""
        await self.bot.logout()

    @commands.group(hidden=True)
    async def sneak(self, ctx):
        """This group contains some sneaky-sneaky stuff."""

        if ctx.invoked_subcommand is None:
            await ctx.invoke(self.bot.get_command('help'), 'sneak')

    @sneak.command()
    async def hiddenchannels(self, ctx, server_id: str = None, print_local: bool = False):
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
            if type(a) == discord.TextChannel and not a.permissions_for(server.me).read_messages:
                hidden_channels.append(a)

        hidden_channels.sort(key=lambda chan: chan.name)

        num_segments = int(len(hidden_channels)/25) + 1
        for b in range(num_segments):
            em = discord.Embed(title=title, color=0xff0000, timestamp=ctx.message.created_at)
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
            if type(a) is discord.TextChannel:
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
            em = discord.Embed(title=title, color=0xff0000, timestamp=ctx.message.created_at)

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
        for a in server.role_hierarchy:
            if not a.is_default():
                role_list.append("({:d}) {}".format(len(a.members), a.name))

        display_size = 80
        num_segments = int(len(role_list)/display_size) + 1
        for b in range(num_segments):
            embed = discord.Embed(title=title, color=0xff0000, timestamp=ctx.message.created_at)
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

    @commands.command()
    async def cooldog(self, ctx):
        string = """╭━━━━━╮               This is cooldog. Help
    ╰┃ ┣▇━▇                cooldog take over 
     ┃ ┃  ╰━▅╮ Discord by pasting
     ╰┳╯ ╰━━┳╯        him in 10 other
      ╰╮ ┳━━╯            servers or he
     ▕▔▋ ╰╮╭━╮   will never be a cool dog
    ╱▔╲▋╰━┻┻╮╲╱▔▔▔╲
    ▏  ▔▔▔▔▔▔▔  O O┃ 
    ╲╱▔╲▂▂▂▂╱▔╲▂▂▂╱
     ▏╳▕▇▇▕ ▏╳▕▇▇▕
     ╲▂╱╲▂╱ ╲▂╱╲▂╱"""
        em = discord.Embed(title="Cooldog", color=0xff0000)
        em.add_field(name="The dog himself", value=string)
        await ctx.message.delete()
        await ctx.send("", embed=em)









    @commands.command()
    async def status(self, ctx, type: int, *, text):
        game = discord.Game(type=type, name=text)
        await self.bot.change_presence(game=game)


def setup(bot):
    bot.add_cog(Owner(bot))
