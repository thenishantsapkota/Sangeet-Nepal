import lightbulb

from . import join, leave

music = lightbulb.Plugin("Music", "Music Commands")


@music.command
@lightbulb.command("join", "Join the voice channel")
@lightbulb.implements(lightbulb.SlashCommand)
async def join_command(ctx: lightbulb.Context) -> None:
    channel_id = await join(ctx)
    if channel_id:
        await ctx.respond("Joined <#{}>".format(channel_id))


@music.command
@lightbulb.command("leave", "Leave the voice channel")
@lightbulb.implements(lightbulb.SlashCommand)
async def leave_command(ctx: lightbulb.Context) -> None:
    await leave(ctx)


def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(music)


def unload(bot: lightbulb.BotApp) -> None:
    bot.remove_plugin(music)
