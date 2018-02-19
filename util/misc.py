import discord
from discord.ext import commands

# Users
ryn_id = 185095270986547200

# Servers
ryn_server_id = 329681826618671104

# Channels
ryn_starboard_id = 355477159629946882
pub_starboard_id = 382661096303230976
bot_log_id = 414193178908819457


base_extensions = ['cogs.base',
                   'cogs.owner',
                   'cogs.logs']

other_extensions = ['cogs.chart',
                    'cogs.my_server',
                    'cogs.server',
                    'cogs.stars']


def is_ryn():
    def predicate(ctx):
        return ctx.message.author.id == ryn_id
    return commands.check(predicate)


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


async def get_message(channel, message_id):
    try:
        o = discord.Object(id=message_id + 1)
        # don't wanna use get_message due to poor rate limit (1/1s) vs (50/1s)
        msg = await channel.history(limit=1, before=o).next()

        if msg.id != message_id:
            return None

        return msg
    except Exception:
        return None
