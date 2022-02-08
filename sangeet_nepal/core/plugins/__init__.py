import typing as t

import lavasnek_rs
import lightbulb


class MusicError(lightbulb.LightbulbError):
    ...


_ValueT = t.TypeVar("_ValueT")
T = t.TypeVar("T")
R = t.TypeVar("R")


def check_voice_state(f: t.Callable[..., R]) -> t.Callable[..., t.Awaitable[R]]:
    async def predicate(ctx: lightbulb.Context, *args: object, **kwargs: object) -> R:
        voice_state_bot = ctx.bot.cache.get_voice_state(ctx.guild_id, ctx.bot.get_me())
        voice_state_author = ctx.bot.cache.get_voice_state(ctx.guild_id, ctx.author)

        if voice_state_bot is None:
            raise MusicError(
                "I am not connected to any voice channel.\nUse {}join to connect me to one.".format(
                    ctx.prefix
                )
            )
        if voice_state_author is None:
            raise MusicError("Connect to a voice channel to continue!")

        if not voice_state_author.channel_id == voice_state_bot.channel_id:
            raise MusicError("You and I are not in the same voice channel.")

        return await f(ctx, *args, **kwargs)

    return predicate


def fetch_lavalink(bot: lightbulb.BotApp) -> lavasnek_rs.Lavalink:
    return bot.data.lavalink


async def join(ctx: lightbulb.Context) -> int:
    lavalink = fetch_lavalink(ctx.bot)
    if ctx.bot.cache.get_voice_state(ctx.guild_id, ctx.bot.get_me()):
        raise lightbulb.LightbulbError("Check if I am already in a voice channel!")
    states = ctx.bot.cache.get_voice_states_view_for_guild(ctx.guild_id)
    voice_state = list(filter(lambda i: i.user_id == ctx.author.id, states.iterator()))

    if not voice_state:
        raise lightbulb.LightbulbError("You are not connected to a voice channel!")

    channel_id = (voice_state[0]).channel_id

    try:
        connection_info = await lavalink.join(ctx.guild_id, channel_id)

    except TimeoutError:
        raise lightbulb.LightbulbError(
            "I am having some difficulties connecting to your voice channel!"
        )
    await lavalink.create_session(connection_info)
    node = await lavalink.get_guild_node(ctx.guild_id)
    node.set_data({ctx.guild_id: ctx.channel_id})
    return channel_id


async def leave(ctx: lightbulb.Context) -> None:
    lavalink = fetch_lavalink(ctx.bot)
    await lavalink.destroy(ctx.guild_id)
    await lavalink.stop(ctx.guild_id)
    await lavalink.leave(ctx.guild_id)
    await lavalink.remove_guild_node(ctx.guild_id)
    await lavalink.remove_guild_from_loops(ctx.guild_id)


def _chunk(iterator: t.Iterator[_ValueT], max: int) -> t.Iterator[list[_ValueT]]:
    chunk: list[_ValueT] = []
    for entry in iterator:
        chunk.append(entry)
        if len(chunk) == max:
            yield chunk
            chunk = []

    if chunk:
        yield chunk
