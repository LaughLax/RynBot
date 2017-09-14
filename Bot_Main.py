import discord
from discord.ext import commands
from datetime import datetime
import io
import matplotlib.pyplot as plt

bot = commands.Bot(command_prefix="_", self_bot=True)

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


@bot.event
async def on_message(message):
    try:
        await bot.process_commands(message)
    except discord.errors.HTTPException as err:
        await bot.send_message(message.channel, err)
        raise


@bot.event
async def on_reaction_add(reaction, user):
    if user.id == bot.user.id:
        print("Reaction at " + datetime.now().strftime("%H:%M:%S"))
        global reaction_text
        if reaction.emoji == '\U0001F643' and reaction_text != '':
            await bot.remove_reaction(reaction.message, reaction.emoji, user)
            for a in reaction_text.lower():
                if a.isalpha():
                    emoji = get_alpha_emoji(a)
                    await bot.add_reaction(reaction.message, emoji)
            reaction_text = ''


@bot.command(pass_context=True)
async def test(ctx):
    await bot.add_reaction(ctx.message, '\U0001F44D')


@bot.command(pass_context=True)
async def whoisplaying(ctx, *, game_title: str):
    if game_title is not None:
        users = []
        for a in ctx.message.server.members:
            if a.game is not None and a.game.name is not None:
                if a.game.name.lower() == game_title.lower():
                    users.append(a.name)
        if len(users) == 0:
            await bot.say("No users found playing {}.".format(game_title))
        else:
            title = "Server: {}".format(ctx.message.server.name)
            header = "Game: {}".format(game_title)

            users.sort()
            body = ""
            for a in users:
                body = "{}\n{}".format(body, a)

            embed = discord.Embed(title=title, color=0xff0000)
            embed.add_field(name=header, value=body)

            # embed.add_field(name="Disclaimer", value="Sorry folks, this command is on my self-bot so it only works for me")

            footer = "As of {}".format(datetime.utcnow().strftime("%Y-%m-%d %H:%M (UTC)"))
            embed.set_footer(text=footer)

            await bot.say(embed=embed)
    else:
        print("No game specified.")


@bot.command(pass_context=True)
async def prime(ctx, *, react: str = None):
    if react is not None:
        global reaction_text
        reaction_text = react
        # await bot.edit_message(ctx.message, 'Reaction primed. Trigger with \U0001F643')
        # await asyncio.sleep(1)
        await bot.delete_message(ctx.message)


@bot.command(pass_context=True)
async def unprime(ctx):
    global reaction_text
    reaction_text = ""
    await bot.delete_message(ctx.message)


@bot.command(pass_context=True)
async def channels(ctx, server_id: str = None, print_local: bool = False):
    if server_id is None or server_id.lower() == "here":
        server = ctx.message.server
    else:
        server = bot.get_server(server_id)
        if server is None:
            await bot.say("I'm not in that server.")
            return

    title = str.format("Server: {} (ID {})", server.name, server.id)

    chans = server.channels
    text_avail = []
    text_hidden = []
    for a in chans:
        if a.type == discord.ChannelType.text:
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
        embed = discord.Embed(title=title, color=0xff0000)

        if text_avail[start:end]:
            text_avail_body = "\n".join(text_avail[start:end])
            embed.add_field(name='Unhidden text channels', value=text_avail_body)

        if text_hidden[start:end]:
            text_hidden_body = "\n".join(text_hidden[start:end])
            embed.add_field(name='Hidden text channels', value=text_hidden_body)

        icon_url = server.icon_url
        embed.set_thumbnail(url=icon_url)

        footer = "Page {}/{}, As of {}".format(b+1, num_segments, datetime.utcnow().strftime("%Y-%m-%d %H:%M (UTC)"))
        embed.set_footer(text=footer)

        if print_local:
            await bot.say(embed=embed)
        else:
            await bot.send_message(destination=bot.get_channel('329691248707502100'), embed=embed)

    await bot.delete_message(ctx.message)


@bot.command(pass_context=True)
async def hiddenchannels(ctx, server_id: str = None, print_local: bool = False):
    if server_id is None or server_id.lower() == "here":
        server = ctx.message.server
    else:
        server = bot.get_server(server_id)
        if server is None:
            await bot.say("I'm not in that server.")
            return

    title = "Hidden Channels in Server: {} (ID: {})".format(server.name, server.id)

    chans = server.channels
    hidden_channels = []
    for a in chans:
        if a.type == discord.ChannelType.text and not a.permissions_for(server.me).read_messages:
            hidden_channels.append(a)

    hidden_channels.sort(key=lambda chan: chan.name)

    num_segments = int(len(hidden_channels)/25) + 1
    for b in range(num_segments):
        embed = discord.Embed(title=title, color=0xff0000)
        embed.set_thumbnail(url=server.icon_url)

        footer = "Page {}/{}, As of {}".format(b+1, num_segments, datetime.utcnow().strftime("%Y-%m-%d %H:%M (UTC)"))
        embed.set_footer(text=footer)

        for a in hidden_channels[b*25:b*25+24]:
            if a.topic is not None and a.topic != "":
                embed.add_field(name=a.name, value=a.topic)
            else:
                embed.add_field(name=a.name, value="(No channel topic)")

        if print_local:
            await bot.say(embed=embed)
        else:
            await bot.send_message(destination=bot.get_channel('329691231498272769'), embed=embed)

    await bot.delete_message(ctx.message)


@bot.command(pass_context=True)
async def roles(ctx, server_id: str = None, print_local: bool = False):
    if server_id is None or server_id.lower() == "here":
        server = ctx.message.server
    else:
        server = bot.get_server(server_id)
        if server is None:
            await bot.say("I'm not in that server.")
            return

    title = "Server: {} (ID {})".format(server.name, server.id)

    role_list = []
    for a in server.role_hierarchy:
        if not a.is_everyone:
            role_list.append(a.name)

    display_size = 50
    num_segments = int(len(role_list)/display_size) + 1
    for b in range(num_segments):
        embed = discord.Embed(title=title, color=0xff0000)
        embed.set_thumbnail(url=server.icon_url)

        embed.add_field(name='Roles', value='\n'.join(role_list[b*display_size:(b+1)*display_size-1]))

        footer = "Page {}/{}, As of {}".format(b+1, num_segments, datetime.utcnow().strftime("%Y-%m-%d %H:%M (UTC)"))
        embed.set_footer(text=footer)

        if print_local:
            await bot.say(embed=embed)
        else:
            await bot.send_message(destination=bot.get_channel('329691241111355392'), embed=embed)

    await bot.delete_message(ctx.message)


@bot.command()
async def now():
    await bot.say(datetime.utcnow().strftime("%Y-%m-%d %H:%M (UTC)"))


@bot.command(pass_context=True)
async def embed(ctx):
    split = ctx.message.content.split(" ", 1)
    if len(split) > 1:
        parts = split[1].split(" | ")
        if len(parts) == 3:
            embed = discord.Embed(title=parts[0], color=0xff0000)
            embed.add_field(name=parts[1], value=parts[2])
            await bot.say(embed=embed)
        if len(parts) == 4:
            embed = discord.Embed(title=parts[0], color=int(parts[3]))
            embed.add_field(name=parts[1], value=parts[2])
            await bot.say(embed=embed)
    await bot.delete_message(ctx.message)


@bot.command(pass_context=True)
async def cooldog(ctx):
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
    embed = discord.Embed(title="Cooldog", color=0xff0000)
    embed.add_field(name="The dog himself", value=string)
    await bot.delete_message(ctx.message)
    await bot.say("", embed=embed)


@bot.command(pass_context=True)
async def userchart(ctx, server_id: str = None):
    if server_id is None or server_id.lower() == "here":
        server = ctx.message.server
    else:
        server = bot.get_server(server_id)
        if server is None:
            await bot.say("I'm not in that server.")
            return

    members = []
    for a in server.members:
        members.append(a)

    members.sort(key=lambda mem: mem.joined_at)
    (x, y) = ([], [])
    for m in range(members.__len__()):
        x.append(members[m].joined_at)
        y.append(m+1)
    x.append(datetime.now())
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
    await bot.send_file(destination=ctx.message.channel, fp=f.getbuffer(), filename="userchart.png")
    f.close()


@bot.command(pass_context=True)
async def commonmembers(ctx, server1_id: str, server2_id: str = None):
    if server1_id is not None:
        if server2_id is None:
            server2 = ctx.message.server
        else:
            server2 = bot.get_server(server2_id)

        server1 = bot.get_server(server1_id)
        if server1 is None or server2 is None:
            await bot.say("I'm not in that server.")
            return

        server1_members = []
        for a in server1.members:
            server1_members.append(a.id)

        both_members = []
        for a in server2.members:
            if server1_members.__contains__(a.id):
                both_members.append(str(a))
        both_members.sort()

        embed = discord.Embed(title="Common Members", color=0xff0000)
        embed.add_field(name="Server 1: \"{}\"".format(server1.name), value="{} members".format(server1.member_count))
        embed.add_field(name="Server 2: \"{}\"".format(server2.name), value="{} members".format(server2.member_count))
        embed.add_field(name="{} users are in both servers:".format(len(both_members)), value="\n".join(both_members), inline=False)

        await bot.say(embed=embed)
    else:
        await bot.say("No server specified.")


bot.run('MzU3Njk1Nzg3NzkyMzM0ODQ4.DJtp_w.pvYRwMjVKouvDZt55MeKB6KfU3Q')
