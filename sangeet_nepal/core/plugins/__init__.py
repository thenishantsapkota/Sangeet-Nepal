import lavasnek_rs
import lightbulb


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

    await ctx.respond("Disconnected from voice!")
