import logging
from typing import TYPE_CHECKING

import hikari
import lavasnek_rs
from lightbulb import LightbulbError
from sangeet_nepal.config.bot import bot_config

if TYPE_CHECKING:
    from ..core.bot import SangeetNepal

logger = logging.getLogger(__name__)


class LavalinkEvents:
    def __init__(self, bot: "SangeetNepal") -> None:
        self.bot = bot

    async def track_start(
        self, lavalink: lavasnek_rs.Lavalink, event: lavasnek_rs.TrackStart
    ) -> None:
        guild = self.bot.cache.get_guild(event.guild_id)
        node = await lavalink.get_guild_node(event.guild_id)
        if not node:
            return
        data = node.get_data()
        channel_id = data[event.guild_id]
        channel = self.bot.cache.get_guild_channel(channel_id)
        embed = hikari.Embed(
            title="Currently Playing",
            description="[{0}]({1}) [<@{2}>]".format(
                node.now_playing.track.info.title,
                node.now_playing.track.info.uri,
                node.now_playing.requester,
            ),
            color=0x00FF00,
        ).set_thumbnail(
            "https://i.ytimg.com/vi/{}/default.jpg".format(
                node.now_playing.track.info.identifier
            )
        )

        await self.bot.rest.create_message(
            bot_config.logging_channel,
            embed=hikari.Embed(title="Track Started", color=0x00FF00)
            .add_field(name="Name", value=node.now_playing.track.info.title)
            .add_field(name="Guild", value=guild.name)
            .set_thumbnail(
                "https://i.ytimg.com/vi/{}/default.jpg".format(
                    node.now_playing.track.info.identifier
                )
            ),
        )
        await channel.send(embed=embed)

    async def track_finish(
        self, lavalink: lavasnek_rs.Lavalink, event: lavasnek_rs.TrackFinish
    ) -> None:
        guild = self.bot.cache.get_guild(event.guild_id)

        states = self.bot.cache.get_voice_states_view_for_guild(event.guild_id)

        members = [
            state
            async for state in states.iterator().filter(
                lambda i: i.user_id != self.bot.application.id
            )
        ]
        if len(members) == 0:
            await lavalink.destroy(event.guild_id)
            await lavalink.stop(event.guild_id)
            await lavalink.leave(event.guild_id)
            await lavalink.remove_guild_node(event.guild_id)
            await lavalink.remove_guild_from_loops(event.guild_id)

        logger.info("Track finished on guild - {}".format(event.guild_id))
        await self.bot.rest.create_message(
            bot_config.logging_channel,
            embed=hikari.Embed(title="Track Finished", color=0xFFA500).add_field(
                name="Guild", value=guild.name
            ),
        )

    async def track_exception(
        self, lavalink: lavasnek_rs.Lavalink, event: lavasnek_rs.TrackException
    ) -> None:
        logger.warning(
            "Track Exception took place on guild - {}".format(event.guild_id)
        )

        skip = await lavalink.skip(event.guild_id)
        node = await lavalink.get_guild_node(event.guild_id)

        if not skip:
            raise LightbulbError("There's nothing to skip!")
        else:
            if not node.queue and not node.now_playing:
                await lavalink.stop(event.guild_id)

    async def track_stuck(
        self, lavalink: lavasnek_rs.Lavalink, event: lavasnek_rs.TrackStuck
    ) -> None:
        logger.warning("Track Stuck in guild - {}".format(event.guild_id))
        skip = await lavalink.skip(event.guild_id)
        node = await lavalink.get_guild_node(event.guild_id)

        if not skip:
            raise LightbulbError("There's nothing to skip!")
        else:
            if not node.queue and not node.now_playing:
                await lavalink.stop(event.guild_id)
