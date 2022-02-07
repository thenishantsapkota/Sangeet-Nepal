import asyncio

import hikari
import lightbulb

misc = lightbulb.Plugin("Misc", "Misc Commands")


@misc.command
@lightbulb.command("ping", "Check if the bot is alive")
@lightbulb.implements(lightbulb.SlashCommand)
async def ping_command(ctx: lightbulb.Context) -> None:
    await ctx.respond("Pinging!")
    await asyncio.sleep(1)
    await ctx.edit_last_response(
        content="",
        embed=hikari.Embed(
            description="**Ping**\n\n{}ms".format(
                int(ctx.bot.heartbeat_latency * 1000)
            ),
            color=0x00FF00,
        ),
    )


@misc.command
@lightbulb.option("query", "Query for help command", required=False)
@lightbulb.command("help", "Help command for the bot")
@lightbulb.implements(lightbulb.SlashCommand)
async def help_command(ctx: lightbulb.Context) -> None:
    await ctx.bot.help_command.send_help(ctx, ctx.options.query)


def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(misc)


def unload(bot: lightbulb.BotApp) -> None:
    bot.remove_plugin(misc)
