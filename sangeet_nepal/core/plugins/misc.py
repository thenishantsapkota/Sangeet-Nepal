import asyncio
from datetime import timedelta
from platform import python_version
from time import time

import hikari
import lightbulb
import miru
from hikari import __version__ as hikari_version
from lightbulb import __version__ as lb_version
from psutil import Process, virtual_memory
from sangeet_nepal import __version__ as bot_version
from sangeet_nepal.core.utils.time import pretty_timedelta

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


@misc.command
@lightbulb.command("info", "View the info about the bot!")
@lightbulb.implements(lightbulb.SlashCommand)
async def botinfo_command(ctx: lightbulb.Context) -> None:
    proc = Process()
    bot = ctx.bot.get_me()
    with proc.oneshot():
        uptime = pretty_timedelta(timedelta(seconds=time() - proc.create_time()))
        cpu_time = pretty_timedelta(
            timedelta(seconds=(cpu := proc.cpu_times()).system + cpu.user)
        )
        mem_total = virtual_memory().total / (1024 ** 2)
        mem_of_total = proc.memory_percent()
        mem_usage = mem_total * (mem_of_total / 100)

    embed = hikari.Embed(
        description="```adoc\n=== General Information about the Bot ===\n",
        color=0x00FF00,
    ).set_thumbnail(bot.avatar_url)
    fields = [
        ("- Language", "Python"),
        ("- Python Version", python_version()),
        ("- Bot Version", bot_version),
        ("- Library", "hikari-py v{}".format(hikari_version)),
        ("- Command Handler", "hikari-lightbulb v{}".format(lb_version)),
        ("- Uptime", uptime),
        ("- CPU Time", cpu_time),
        (
            "- Memory Usage",
            "{} MiB / {} Mib ({}%)".format(
                int(mem_usage), int(mem_total), int(mem_usage / mem_total)
            ),
        ),
        (
            "- Total Guilds",
            "{}```".format(len(ctx.bot.cache.get_available_guilds_view())),
        ),
    ]
    for name, value in fields:
        embed.description += "{} :: {}\n".format(name, value)

    row = [
        ctx.bot.rest.build_action_row()
        .add_button(
            hikari.ButtonStyle.LINK,
            "https://discord.com/api/oauth2/authorize?client_id={}&permissions=8&scope=bot%20applications.commands".format(
                bot.id
            ),
        )
        .set_label("Invite")
        .add_to_container()
    ]

    await ctx.respond(embed=embed, components=row)


def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(misc)


def unload(bot: lightbulb.BotApp) -> None:
    bot.remove_plugin(misc)
