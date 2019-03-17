import discord
from discord.ext import commands
from util import misc, config
from util.database import ServerConfig, Star
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound


class StarError(commands.CheckFailure):
    pass


class Stars(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    def get_starboard_channel(self, db, guild):
        try:
            starboard = db.query(ServerConfig.starboard).\
                filter(ServerConfig.server == guild.id).\
                one()[0]
        except NoResultFound:
            starboard = None
        except MultipleResultsFound as e:
            log = self.bot.get_cog('cogs.logs')
            if log is not None:
                log.log(e)
            return

        return self.bot.get_channel(starboard)

    def get_star_threshold(self, db, guild):
        try:
            star_threshold = db.query(ServerConfig.star_threshold).\
                filter(ServerConfig.server == guild.id).\
                one()[0]
        except NoResultFound:
            star_threshold = 1
        except MultipleResultsFound as e:
            log = self.bot.get_cog('cogs.logs')
            if log is not None:
                log.log(e)
            return 1

        return star_threshold

    def get_star_db_entry(self, db, message):
        try:
            star = db.query(Star).\
                filter(Star.server == message.guild.id).\
                filter(Star.message == message.id).\
                one()
        except NoResultFound:
            star = Star(server=message.guild.id,
                        channel=message.channel.id,
                        message=message.id,
                        author=message.author.id,
                        timestamp=message.created_at)
        except MultipleResultsFound as e:
            log = self.bot.get_cog('cogs.logs')
            if log is not None:
                log.log(e)
            return

        return star

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, p):
        if str(p.emoji) == '\N{WHITE MEDIUM STAR}':
            await self.reaction_action('_star', p.emoji, p.channel_id, p.message_id, p.user_id)

    async def reaction_action(self, fmt, emoji, channel_id, message_id, user_id):
        if str(emoji) != '\N{WHITE MEDIUM STAR}':
            return

        channel = self.bot.get_channel(channel_id)
        if not isinstance(channel, discord.TextChannel)\
                or (user_id != config.owner_id and channel.guild.id != config.ryn_server_id):
            return

        method = getattr(self, '{}_message'.format(fmt))

        try:
            await method(str(emoji), channel, message_id, user_id)
        except StarError:
            pass

    async def _star_message(self, emoji, channel, message_id, user_id):
        """Stars a message.
        Parameters
        ------------
        channel: :class:`TextChannel`
            The channel that the starred message belongs to.
        message_id: int
            The message ID of the message being starred.
        user_id: int
            The user ID of the user starring the message.
        """

        with self.bot.db.get_session() as db:

            # Get the starboard channel for the server
            if user_id == config.owner_id:
                starboard_channel = self.bot.get_channel(config.ryn_starboard_id)
                starboard_channel = self.get_starboard_channel(db, channel.guild)
            else:
                starboard_channel = self.get_starboard_channel(db, channel.guild)
            if (not starboard_channel) or (channel == starboard_channel):
                # TODO respond to stars within the starboard
                return

            # If insufficient perms, ignore the star
            perms = channel.permissions_for(channel.guild.me)
            if not (perms.send_messages and perms.attach_files):
                return

            # Get the message being starred
            msg = await misc.get_message(channel, message_id)
            if msg is None:
                raise StarError('\N{BLACK QUESTION MARK ORNAMENT} This message could not be found.')
            if (len(msg.content) == 0 and len(msg.attachments) == 0) or msg.type is not discord.MessageType.default:
                raise StarError('\N{NO ENTRY SIGN} This message cannot be starred.')

            min_stars = self.get_star_threshold(db, channel.guild)
            star_count = next(r for r in msg.reactions if r.emoji == emoji).count

            star = self.get_star_db_entry(db, msg)
            if not star:
                return

            # at this point, we either edit the message or we create a message
            # with our star info
            content, embed = self.get_emoji_message(msg, star_count)

            if star.card:
                card = await misc.get_message(starboard_channel, star.card)
                await card.edit(content, embed=embed)
            else:
                card = await starboard_channel.send(content, embed=embed)
                star.card = card.id
                db.add(star)

    @staticmethod
    def get_emoji_message(message, star_count):
        emoji = '\N{WHITE MEDIUM STAR}'

        content = '{} {}'.format(message.guild.name, message.channel.mention)

        embed = misc.embedify_message(message)
        embed.set_footer(text='{} \N{WHITE MEDIUM STAR}'.format(star_count))
        return content, embed


def setup(bot):
    bot.add_cog(Stars(bot))
