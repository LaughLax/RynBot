import discord
from discord.ext import commands
import subprocess


class StarError(commands.CheckFailure):
    pass


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

        stream = subprocess.run(['git {}'.format(args)], shell=True, stderr=subprocess.PIPE)
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

    async def on_raw_reaction_add(self, emoji, message_id, channel_id, user_id):
        if user_id == 185095270986547200 and channel_id != 355477159629946882:
            await self.reaction_action('_star', emoji, message_id, channel_id)

    async def reaction_action(self, fmt, emoji, message_id, channel_id):
        if str(emoji) != '\N{WHITE MEDIUM STAR}':
            return

        channel = self.bot.get_channel(channel_id)
        if not isinstance(channel, discord.TextChannel):
            return

        method = getattr(self, '{}_message'.format(fmt))

        try:
            await method(channel, message_id)
        except StarError:
            pass

    async def _star_message(self, channel, message_id):
        """Stars a message.
        Parameters
        ------------
        channel: :class:`TextChannel`
            The channel that the starred message belongs to.
        message_id: int
            The message ID of the message being starred.
        """

        # guild_name = channel.guild.name
        starboard_channel = self.bot.get_channel(355477159629946882)

        msg = await self.get_message(channel, message_id)

        if msg is None:
            raise StarError('\N{BLACK QUESTION MARK ORNAMENT} This message could not be found.')

        if (len(msg.content) == 0 and len(msg.attachments) == 0) or msg.type is not discord.MessageType.default:
            raise StarError('\N{NO ENTRY SIGN} This message cannot be starred.')

        # at this point, we either edit the message or we create a message
        # with our star info
        content, embed = self.get_emoji_message(msg)

        await starboard_channel.send(content, embed=embed)

    async def get_message(self, channel, message_id):
        try:
            o = discord.Object(id=message_id + 1)
            pred = lambda m: m.id == message_id
            # don't wanna use get_message due to poor rate limit (1/1s) vs (50/1s)
            msg = await channel.history(limit=1, before=o).next()

            if msg.id != message_id:
                return None

            return msg
        except Exception:
            return None

    def get_emoji_message(self, message):
        emoji = '\N{WHITE MEDIUM STAR}'

        content = '{} {} {} ID: {}'.format(emoji, message.guild.name, message.channel.mention, message.id)

        embed = discord.Embed(description=message.content)
        if message.embeds:
            data = message.embeds[0]
            if data.type == 'image':
                embed.set_image(url=data.url)

        if message.attachments:
            file = message.attachments[0]
            if file.url.lower().endswith(('png', 'jpeg', 'jpg', 'gif', 'webp')):
                embed.set_image(url=file.url)
            else:
                embed.add_field(name='Attachment', value='[{}]({})'.format(file.filename, file.url), inline=False)

        embed.set_author(name=message.author.display_name, icon_url=message.author.avatar_url_as(format='png'))
        embed.timestamp = message.created_at
        embed.colour = 0xff0000
        return content, embed


def setup(bot):
    bot.add_cog(Owner(bot))
