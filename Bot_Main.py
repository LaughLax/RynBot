import discord
from discord.ext import commands
from datetime import datetime
import io
import matplotlib.pyplot as plt

bot = commands.Bot(command_prefix="_")

reaction_text = ''


def get_alpha_emoji(char):
    return {
        'a': '\U0001F1E6',
        'b': '\U0001F1E7',
        'c': '\U0001F1E8',
        'd': '\U0001F1E9',
        'e': '\U0001F1EA',
        'f': '\U0001F1EB',
        'g': '\U0001F1EC',
        'h': '\U0001F1ED',
        'i': '\U0001F1EE',
        'j': '\U0001F1EF',
        'k': '\U0001F1F0',
        'l': '\U0001F1F1',
        'm': '\U0001F1F2',
        'n': '\U0001F1F3',
        'o': '\U0001F1F4',
        'p': '\U0001F1F5',
        'q': '\U0001F1F6',
        'r': '\U0001F1F7',
        's': '\U0001F1F8',
        't': '\U0001F1F9',
        'u': '\U0001F1FA',
        'v': '\U0001F1FB',
        'w': '\U0001F1FC',
        'x': '\U0001F1FD',
        'y': '\U0001F1FE',
        'z': '\U0001F1FF'
    }.get(char, '')


@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')


# @bot.event
# async def on_message(message):
#     try:
#         await bot.process_commands(message)
#     except discord.errors.HTTPException as err:
#         await bot.send_message(message.channel, err)
#         raise


@bot.command()
async def test(ctx):
    await ctx.message.add_reaction('\U0001F44D')


@bot.command()
async def whoisplaying(ctx, *, game_title: str):
    if game_title is not None:
        users = []
        for a in ctx.guild.members:
            if a.game is not None and a.game.name is not None:
                if a.game.name.lower() == game_title.lower():
                    users.append(a.name)
        if len(users) == 0:
            await ctx.send("No users found playing {}.".format(game_title))
        else:
            title = "Server: {}".format(ctx.guild.name)
            header = "Game: {}".format(game_title)

            users.sort()
            body = "\n".join(users)

            em = discord.Embed(title=title, color=0xff0000, timestamp=ctx.message.created_at)
            em.add_field(name=header, value=body)

            await ctx.send(embed=em)
            await ctx.message.delete()
    else:
        await ctx.send("No game specified.")


@bot.command()
async def channels(ctx, server_id: str = None, print_local: bool = False):
    if server_id is None or server_id.lower() == "here":
        server = ctx.guild
    else:
        server = bot.get_guild(int(server_id))
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
            await bot.get_channel(329691248707502100).send(embed=em)

    await ctx.message.delete()


@bot.command()
async def hiddenchannels(ctx, server_id: str = None, print_local: bool = False):
    if server_id is None or server_id.lower() == "here":
        server = ctx.guild
    else:
        server = bot.get_guild(int(server_id))
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
            await bot.get_channel(329691231498272769).send(embed=em)

    await ctx.message.delete()


@bot.command()
async def roles(ctx, server_id: str = None, print_local: bool = False):
    if server_id is None or server_id.lower() == "here":
        server = ctx.guild
    else:
        server = bot.get_guild(int(server_id))
        if server is None:
            await ctx.send("I'm not in that server.")
            return

    title = "Server: {0.name} (ID {0.id})".format(server)

    role_list = []
    for a in server.role_hierarchy:
        if not a.is_default():
            role_list.append(a.name)

    display_size = 80
    num_segments = int(len(role_list)/display_size) + 1
    for b in range(num_segments):
        embed = discord.Embed(title=title, color=0xff0000, timestamp=ctx.message.created_at)
        embed.set_thumbnail(url=server.icon_url)

        embed.add_field(name='Roles', value=', '.join(role_list[b*display_size:(b+1)*display_size-1]))

        footer = "Page {}/{}".format(b+1, num_segments)
        embed.set_footer(text=footer)

        if print_local:
            await ctx.send(embed=embed)
        else:
            await bot.get_channel(329691241111355392).send(embed=embed)

    await ctx.message.delete()


@bot.command()
async def now(ctx):
    await ctx.send(datetime.utcnow().strftime("%Y-%m-%d %H:%M (UTC)"))


@bot.command()
async def ping(ctx):
    start = datetime.now()
    await (await bot.ws.ping())
    td = datetime.now() - start
    await ctx.send("Pong. Response time: {} ms".format(td.total_seconds() * 1000))


@bot.command()
async def userchart(ctx, server_id: str = None):
    if server_id is None or server_id.lower() == "here":
        server = ctx.guild
    else:
        server = bot.get_guild(int(server_id))
        if server is None:
            await ctx.send("I'm not in that server.")
            return

    members = []
    for a in server.members:
        members.append(a)

    members.sort(key=lambda mem: mem.joined_at)
    (x, y) = ([], [])
    for m in range(members.__len__()):
        if m > 0:
            x.append(members[m].joined_at)
            y.append(m)
        x.append(members[m].joined_at)
        y.append(m+1)
    x.append(ctx.message.created_at)
    y.append(len(members))

    plt.clf()
    plt.plot(x, y)
    plt.xticks(rotation=45)
    plt.xlabel("Date")
    plt.ylabel("Member count")
    plt.title("Membership growth for server: {0.name}\nNote: This data includes only current members.".format(server))
    plt.tight_layout()

    f = io.BytesIO()
    plt.savefig(f, format='png')
    await ctx.send(file=discord.File(fp=f.getbuffer(), filename="userchart.png"))
    f.close()


@bot.command()
async def rolechart(ctx, server_id: str = None):
    if server_id is None or server_id.lower() == "here":
        server = ctx.guild
    else:
        server = bot.get_guild(int(server_id))
        if server is None:
            await ctx.send("I'm not in that server.")
            return

    role_list = []
    role_size = []
    role_colors = []
    for a in server.role_hierarchy:
        if not a.is_default():
            role_list.append(a)
            role_size.append(len(a.members))
            rgb = list(a.color.to_rgb())
            rgba = [1., 1., 1., 1.]
            for b in range(3):
                rgba[b] = rgb[b] / 256.
            role_colors.append(tuple(rgba))

    plt.clf()
    plt.bar(range(len(role_list)), role_size, tick_label=role_list, color=role_colors, width=1., edgecolor='k')
    plt.xticks(rotation=90, size='xx-small')
    plt.xlabel("Role")
    plt.ylabel("Member count")
    plt.title("Role distribution for server:\n{}".format(server.name))
    plt.tight_layout()

    with io.BytesIO() as f:
        plt.savefig(f, format='png')
        await ctx.send(file=discord.File(fp=f.getbuffer(), filename="rolechart.png"))


@bot.command()
async def gameschart(ctx, server_id: str = None):
    if server_id is None or server_id.lower() == "here":
        server = ctx.guild
    else:
        server = bot.get_guild(int(server_id))
        if server is None:
            await ctx.send("I'm not in that server.")
            return

    game_names = []
    game_count = []
    for a in server.members:
        if a.game is not None:
            if a.game.name not in game_names:
                game_names.append(a.game.name)
                game_count.append(1)
            else:
                game_count[game_names.index(a.game.name)] += 1

    cutoff = 0
    while len(game_names) > 50:
        cutoff += 1
        copy = game_names.copy()
        for g in copy:
            ind = game_names.index(g)
            if game_count[ind]<=cutoff:
                game_names.pop(ind)
                game_count.pop(ind)

    game_names, game_count = zip(*sorted(zip(game_names, game_count)))

    plt.clf()
    plt.bar(range(len(game_names)), game_count, tick_label=game_names, width=1., edgecolor='k')
    plt.xticks(rotation=90, size='xx-small')
    plt.xlabel("Game (top {} shown)".format(len(game_names)))
    plt.ylabel("# of Members Playing (min. {})".format(cutoff+1))
    plt.title("Games being played on server:\n{}".format(server.name))
    try:
        plt.tight_layout()

        with io.BytesIO() as f:
            plt.savefig(f, format='png')
            await ctx.send(file=discord.File(fp=f.getbuffer(), filename="gameschart.png"))
    except ValueError:
        await ctx.send("Something went wrong with fitting the graph to scale.")


@bot.command()
async def gamespie(ctx, server_id: str = None):
    if server_id is None or server_id.lower() == "here":
        server = ctx.guild
    else:
        server = bot.get_guild(int(server_id))
        if server is None:
            await ctx.send("I'm not in that server.")
            return

    game_names = []
    game_count = []
    for a in server.members:
        if a.game is not None:
            if a.game.name not in game_names:
                game_names.append(a.game.name)
                game_count.append(1)
            else:
                game_count[game_names.index(a.game.name)] += 1

    cutoff = 0
    other_count = 0
    while len(game_names) >= 10:
        cutoff += 1
        copy = game_names.copy()
        for g in copy:
            ind = game_names.index(g)
            if game_count[ind]==cutoff:
                game_names.pop(ind)
                game_count.pop(ind)
                other_count += cutoff

    if other_count > 0:
        game_names.append("Other")
        game_count.append(other_count)
    # game_names, game_count = zip(*sorted(zip(game_names, game_count)))

    plt.clf()
    patches, texts = plt.pie(game_count, labels=game_names, shadow=True)
    # for t in texts:
        # t.set_size('x-small')
    plt.title("Games being played on server:\n{}".format(server.name))
    plt.axis('scaled')

    with io.BytesIO() as f:
        plt.savefig(f, format='png')
        await ctx.send(file=discord.File(fp=f.getbuffer(), filename="gameschart.png"))


@bot.command()
async def nowstreaming(ctx, server_id: str = None):
    if server_id is None or server_id.lower() == "here":
        server = ctx.guild
    else:
        server = bot.get_guild(int(server_id))
        if server is None:
            await ctx.send("I'm not in that server.")
            return

    streamers = []
    for a in server.members:
        if a.game is not None and a.game.type == 1:
            streamers.append(a)

    streamers.sort(key=lambda mem: mem.display_name)

    if len(streamers) > 0:
        display_size = 20
        num_segments = int(len(streamers)/display_size) + 1
        if num_segments <= 5:
            for b in range(num_segments):
                em = discord.Embed(title="Members Streaming (Server: {})".format(server.name), color=0xff0000, timestamp=ctx.message.created_at)
                em.set_thumbnail(url=server.icon_url)
                for a in streamers[b*display_size:(b+1)*display_size-1]:
                    if a.game.url is not None:
                        em.add_field(name=a.display_name, value="[{}]({})".format(a.game.name, a.game.url))
                    else:
                        em.add_field(name=a.display_name, value="{}".format(a.game.name))
                em.set_footer(text="Page {}/{}".format(b+1, num_segments))
                await ctx.send(embed=em)
        else:
            await ctx.send("{} members streaming on server: {}.".format(len(streamers), server.name))
    else:
        await ctx.send("No members streaming on server: {}.".format(server.name))


@bot.command()
async def commonmembers(ctx, server1_id: int, server2_id: int = None):
    if server1_id is not None:
        if server2_id is None:
            server2 = ctx.guild
        else:
            server2 = bot.get_guild(server2_id)

        server1 = bot.get_guild(server1_id)
        if server1 is None:
            await ctx.send("I'm not in that server1.")
            return
        if server2 is None:
            await ctx.send("I'm not in that server2.")
            return

        server1_members = []
        for a in server1.members:
            server1_members.append(a.id)

        both_members = []
        for a in server2.members:
            if server1_members.__contains__(a.id):
                both_members.append(str(a))
        both_members.sort()

        em = discord.Embed(title="Common Members", color=0xff0000)
        em.add_field(name="Server 1: \"{}\"".format(server1.name), value="{} members".format(server1.member_count))
        em.add_field(name="Server 2: \"{}\"".format(server2.name), value="{} members".format(server2.member_count))
        em.add_field(name="{} users are in both servers:".format(len(both_members)), value="\n".join(both_members), inline=False)

        await ctx.send(embed=em)
    else:
        await ctx.send("No server specified.")


@bot.command()
async def userinfo(ctx, name: str = None):
    """Get user info. Ex: >info @user"""
    if name is None:
        user = ctx.message.author
    else:
        try:
            user = ctx.message.mentions[0]
        except:
            user = ctx.guild.get_member_named(name)
        if not user:
            user = ctx.guild.get_member(name)
        if not user:
            await ctx.send('Could not find user.')
            return

    # Thanks to IgneelDxD for help on this
    if user.avatar_url[54:].startswith('a_'):
        avi = 'https://images.discordapp.net/avatars/' + user.avatar_url[35:-10]
    else:
        avi = user.avatar_url

    role = user.top_role.name
    if role == "@everyone":
        role = "N/A"
    voice_state = None if not user.voice else user.voice.channel
    em = discord.Embed(timestamp=ctx.message.created_at, colour=0xff0000)
    em.add_field(name='User ID', value=user.id, inline=True)
    em.add_field(name='Nick', value=user.nick, inline=True)
    em.add_field(name='Status', value=user.status, inline=True)
    em.add_field(name='In Voice', value=voice_state, inline=True)
    em.add_field(name='Game', value=user.game, inline=True)
    em.add_field(name='Highest Role', value=role, inline=True)
    em.add_field(name='Account Created', value=user.created_at.__format__('%A, %d. %B %Y @ %H:%M:%S'))
    em.add_field(name='Join Date', value=user.joined_at.__format__('%A, %d. %B %Y @ %H:%M:%S'))
    em.set_thumbnail(url=avi)
    em.set_author(name=user, icon_url='https://i.imgur.com/RHagTDg.png')
    await ctx.send(embed=em)

    # await ctx.message.delete()


@bot.command()
async def rename(ctx, name: str):
    if ctx.message.author.id == 185095270986547200:
        await bot.user.edit(username=name)
        ctx.send("Bot username changed.")


with open('token.txt','r') as f:
    token = f.readline().strip()
bot.run(token)
