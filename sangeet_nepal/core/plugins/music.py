from datetime import datetime

import hikari
import lavasnek_rs
import lightbulb
import miru
from miru.ext import nav

from . import MusicError, _chunk, check_voice_state, fetch_lavalink, join, leave

music = lightbulb.Plugin("Music", "Music Commands")


@music.command
@lightbulb.command("join", "Make the bot join the voice channel")
@lightbulb.implements(lightbulb.SlashCommand)
async def join_command(ctx: lightbulb.Context) -> None:
    channel_id = await join(ctx)
    if channel_id:
        await ctx.respond(
            embed=hikari.Embed(
                description="Joined <#{}>".format(channel_id), color=0x00FF00
            )
        )


@music.command
@lightbulb.command(
    "leave",
    "Make the bot leave the voice channel",
)
@lightbulb.implements(lightbulb.SlashCommand)
@check_voice_state
async def leave_command(ctx: lightbulb.Context) -> None:
    await leave(ctx)
    await ctx.respond(
        embed=hikari.Embed(description="Disconnected from voice!", color=0x00FF00)
    )


@music.command
@lightbulb.option("query", "Query for the play command[Name or URL of the song]")
@lightbulb.command("play", "Play some music using the bot")
@lightbulb.implements(lightbulb.SlashCommand)
async def play_command(ctx: lightbulb.Context) -> None:
    lavalink = fetch_lavalink(ctx.bot)
    query = ctx.options.query
    connection_info = lavalink.get_guild_gateway_connection_info(ctx.guild_id)
    if not connection_info:
        await join(ctx)

    query_information = await lavalink.auto_search_tracks(query)
    playlist = False
    if query_information.playlist_info.name:
        playlist = True

    if not query_information.tracks:
        raise MusicError("No matching video to the given query.")

    if playlist:
        try:
            for track in query_information.tracks:
                await lavalink.play(ctx.guild_id, track).requester(
                    ctx.author.id
                ).queue()
        except lavasnek_rs.NoSessionPresent:
            raise MusicError("I am not connected to any voice channel!")

        await ctx.respond(
            embed=hikari.Embed(
                title="Playlist Added",
                description=f"{query_information.playlist_info.name}({len(query_information.tracks)} tracks added to queue [{ctx.author.mention}])",
                color=0x00FF00,
            )
        )
    else:
        try:
            await lavalink.play(ctx.guild_id, query_information.tracks[0]).requester(
                ctx.author.id
            ).queue()
        except lavasnek_rs.NoSessionPresent:
            raise MusicError("I am not connected to any voice channel")

        await ctx.respond(
            embed=hikari.Embed(
                title="Track Added",
                description=f"[{query_information.tracks[0].info.title}]({query_information.tracks[0].info.uri}) added to the queue [{ctx.author.mention}]",
                color=0x00FF00,
            )
        )


@music.command
@lightbulb.command("clear", "Clear the current queue")
@lightbulb.implements(lightbulb.SlashCommand)
@check_voice_state
async def clear_command(ctx: lightbulb.Context) -> None:
    await leave(ctx)
    await join(ctx)
    await ctx.respond(
        embed=hikari.Embed(description="Cleared the current queue!", color=0x00FF00)
    )


@music.command
@lightbulb.command("queue", "Displays the current music queue for the server")
@lightbulb.implements(lightbulb.SlashCommand)
async def queue_command(ctx: lightbulb.Context) -> None:
    lavalink = fetch_lavalink(ctx.bot)
    song_queue = []
    node = await lavalink.get_guild_node(ctx.guild_id)
    if not node or not node.queue:
        raise MusicError("There are no tracks in the queue.")

    for song in node.queue:
        song_queue += [
            f"[{song.track.info.title}]({song.track.info.uri}) [<@{song.requester}>]"
        ]

    fields = []
    counter = 1
    if not len(song_queue[1:]) > 0:
        return await ctx.respond(
            f"No tracks in the queue.\n**Now Playing** : [{node.now_playing.track.info.title}]({node.now_playing.track.info.uri})"
        )
    for index, track in enumerate(_chunk(song_queue[1:], 8)):
        string = """**Next Up**\n"""
        for i in track:
            amount = node.queue[counter].track.info.length
            millis = int(amount)
            l_seconds = (millis / 1000) % 60
            l_seconds = int(l_seconds)
            l_minutes = (millis / (1000 * 60)) % 60
            l_minutes = int(l_minutes)
            first_n = int(l_seconds / 10)
            string += f"""{counter}.`{l_minutes}:{l_seconds if first_n !=0 else f'0{l_seconds}'}` {i}\n"""

            counter += 1
        embed = hikari.Embed(
            title=f"Queue for {ctx.get_guild()}",
            color=0x00FF00,
            timestamp=datetime.now().astimezone(),
            description=string,
        )
        embed.set_footer(text=f"Page {index+1}")
        embed.add_field(
            name="Now Playing",
            value=f"[{node.now_playing.track.info.title}]({node.now_playing.track.info.uri}) [<@{node.now_playing.requester}>]",  # noqa: E501
        )
        fields.append(embed)

    navigator = nav.NavigatorView(pages=fields)
    await navigator.send(ctx.interaction)
    await navigator.wait()


@music.command
@lightbulb.command("pause", "Pause the currently playing track")
@lightbulb.implements(lightbulb.SlashCommand)
@check_voice_state
async def pause_command(ctx: lightbulb.Context) -> None:
    lavalink = fetch_lavalink(ctx.bot)
    node = await lavalink.get_guild_node(ctx.guild_id)
    if not node or not node.now_playing:
        raise MusicError("No tracks are playing currently!")

    if node.is_paused:
        raise MusicError(
            "How are you expecting me to pause something that's already paused?"
        )
    await lavalink.pause(ctx.guild_id)
    await lavalink.set_pause(ctx.guild_id, True)

    await ctx.respond(embed=hikari.Embed(description="⏸️ Paused", color=0x00FF00))


@music.command
@lightbulb.command("resume", "Resume the currently paused song")
@lightbulb.implements(lightbulb.SlashCommand)
@check_voice_state
async def resume_command(ctx: lightbulb.Context) -> None:
    lavalink = fetch_lavalink(ctx.bot)
    node = await lavalink.get_guild_node(ctx.guild_id)
    if not node or not node.now_playing:
        raise MusicError("No tracks are playing currently!")

    if not node.is_paused:
        raise MusicError("Don't make me resume something that's not paused 😠")

    await lavalink.resume(ctx.guild_id)
    await ctx.respond(
        embed=hikari.Embed(description="🎵 Playback resumed.", color=0x00FF00)
    )


def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(music)
    miru.load(bot)


def unload(bot: lightbulb.BotApp) -> None:
    bot.remove_plugin(music)
