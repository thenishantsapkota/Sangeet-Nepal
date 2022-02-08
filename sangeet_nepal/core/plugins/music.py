import random
from datetime import datetime

import hikari
import lavasnek_rs
import lightbulb
import miru
from click import style
from miru.ext import nav

from . import MusicError, _chunk, check_voice_state, fetch_lavalink, join, leave

music = lightbulb.Plugin("Music", "Music Commands")


class Controls(miru.View):
    def __init__(self, author_id: hikari.Snowflake) -> None:
        self.author_id = author_id
        super().__init__(timeout=120)

    @miru.button(label="Play/Pause", style=hikari.ButtonStyle.SUCCESS)
    async def play_pause_button(self, _: miru.Button, ctx: miru.Context) -> None:
        lavalink = fetch_lavalink(music.bot)
        node = await lavalink.get_guild_node(ctx.guild_id)
        if not node or not node.now_playing:
            return await ctx.respond(
                "Nothing playing at the moment!", flags=hikari.MessageFlag.EPHEMERAL
            )
        if node.is_paused:
            await lavalink.resume(ctx.guild_id)
            await lavalink.set_pause(ctx.guild_id, False)
            await ctx.respond(
                content="Resumed!",
                flags=hikari.MessageFlag.EPHEMERAL,
            )
        else:
            await lavalink.pause(ctx.guild_id)
            await lavalink.set_pause(ctx.guild_id, True)
            await ctx.respond(
                content="Paused!",
                flags=hikari.MessageFlag.EPHEMERAL,
            )

    @miru.button(label="Re-Queue", style=hikari.ButtonStyle.PRIMARY)
    async def requeue_button(self, button: miru.Button, ctx: miru.Context) -> None:
        lavalink = fetch_lavalink(music.bot)
        node = await lavalink.get_guild_node(ctx.guild_id)
        queue = node.queue
        try:
            now_playing = queue[0]
            queue.insert(1, now_playing)
        except IndexError:
            button.disabled = True
            await self.message.edit(components=self.build())
            return await ctx.respond(
                "No song could be found to requeue!", flags=hikari.MessageFlag.EPHEMERAL
            )
        node.queue = queue
        await lavalink.set_guild_node(ctx.guild_id, node)
        button.disabled = True
        await self.message.edit(components=self.build())
        await ctx.respond(
            content="Added the song to the queue again!",
            flags=hikari.MessageFlag.EPHEMERAL,
        )

    @miru.button(label="Skip", style=hikari.ButtonStyle.DANGER)
    async def skip_button(self, button: miru.Button, ctx: miru.Context) -> None:
        lavalink = fetch_lavalink(music.bot)
        skip = await lavalink.skip(ctx.guild_id)
        node = await lavalink.get_guild_node(ctx.guild_id)

        if not skip:
            return await ctx.respond(
                "I don't see any tracks to skip 😕", flags=hikari.MessageFlag.EPHEMERAL
            )

        if not node.queue and not node.now_playing:
            await lavalink.stop(ctx.guild_id)

        button.disabled = True
        await self.message.edit(components=self.build())
        await ctx.respond("Skipped!", flags=hikari.MessageFlag.EPHEMERAL)

    @miru.select(
        placeholder="Volume",
        options=[miru.SelectOption(label=x * 10) for x in range(1, 11)],
    )
    async def volume_select(self, select: miru.Select, ctx: miru.Context) -> None:
        lavalink = fetch_lavalink(music.bot)
        node = await lavalink.get_guild_node(ctx.guild_id)
        if not node or not node.now_playing:
            return await ctx.respond(
                "Nothing is playing..", flags=hikari.MessageFlag.EPHEMERAL
            )
        await lavalink.volume(ctx.guild_id, int(select.values[0]))
        await ctx.respond(
            "Volume set to {}%".format(select.values[0]),
            flags=hikari.MessageFlag.EPHEMERAL,
        )

    async def view_check(self, ctx: miru.Context) -> bool:
        if not ctx.user.id == self.author_id:
            await ctx.respond(
                embed=hikari.Embed(
                    description="This belongs to <@{}>".format(self.author_id),
                    color=0xFF0000,
                ),
                flags=hikari.MessageFlag.EPHEMERAL,
            )
        return ctx.user.id == self.author_id

    async def on_timeout(self) -> None:
        for child in self.children:
            child.disabled = True

        await self.message.edit(components=self.build())


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


@music.command
@lightbulb.command("shuffle", "Shuffle the queue")
@lightbulb.implements(lightbulb.SlashCommand)
@check_voice_state
async def shuffle_command(ctx: lightbulb.Context) -> None:
    lavalink = fetch_lavalink(ctx.bot)
    node = await lavalink.get_guild_node(ctx.guild_id)

    if not len(node.queue) > 1:
        raise MusicError("Only one song in the queue, can't shuffle")
    queue = node.queue[1:]
    random.shuffle(queue)
    queue.insert(0, node.queue[0])

    node.queue = queue
    await lavalink.set_guild_node(ctx.guild_id, node)
    await ctx.respond(
        embed=hikari.Embed(description="🔀 Queue shuffled successfully!", color=0x00FF00)
    )


@music.command
@lightbulb.command("stop", "Stop the playback")
@lightbulb.implements(lightbulb.SlashCommand)
@check_voice_state
async def stop_command(ctx: lightbulb.Context) -> None:
    lavalink = fetch_lavalink(ctx.bot)
    await lavalink.stop(ctx.guild_id)
    await ctx.respond(
        embed=hikari.Embed(description="⏹️ Stopped the Playback!", color=0x00FF00)
    )


@music.command
@lightbulb.command("song", "Command Group for tasks related to songs")
@lightbulb.implements(lightbulb.SlashCommandGroup)
async def song(ctx: lightbulb.Context) -> None:
    await ctx.bot.help_command.send_group_help(ctx, ctx.command)


@song.child
@lightbulb.option("new_index", "New index for the song", type=int)
@lightbulb.option("old_index", "Old index of the song", type=int)
@lightbulb.command("move", "Move song to specific index in the queue.")
@lightbulb.implements(lightbulb.SlashSubCommand)
@check_voice_state
async def move_song_command(ctx: lightbulb.Context) -> None:
    lavalink = fetch_lavalink(ctx.bot)
    node = await lavalink.get_guild_node(ctx.guild_id)
    if not len(node.queue) >= 1:
        raise MusicError("Only one song in the queue!")
    queue = node.queue
    song_to_be_moved = queue[ctx.options.old_index]
    try:
        queue.pop(ctx.options.old_index)
        queue.insert(ctx.options.new_index, song_to_be_moved)
    except KeyError:
        raise MusicError("No song could be found at the specified index.")

    node.queue = queue
    await lavalink.set_guild_node(ctx.guild_id, node)
    await ctx.respond(
        embed=hikari.Embed(
            description=f"Moved `{song_to_be_moved.track.info.title}` to Position `{ctx.options.new_index}`",
            color=0x00FF00,
        )
    )


@song.child
@lightbulb.option("index", "Index of the song to be removed", type=int)
@lightbulb.command("remove", "Remove the song at the specified index from the queue")
@lightbulb.implements(lightbulb.SlashSubCommand)
@check_voice_state
async def remove_song_command(ctx: lightbulb.Context) -> None:
    lavalink = fetch_lavalink(ctx.bot)
    index: int = ctx.options.index
    node = await lavalink.get_guild_node(ctx.guild_id)
    if not node.queue:
        raise MusicError("There are no songs in the queue!")

    if index == 0:
        raise MusicError(
            "Cannot remove a currently playing song\nUse {}skip to skip the song".format(
                ctx.prefix
            )
        )
    queue = node.queue
    song_to_remove = queue[index]
    try:
        queue.pop(index)
    except KeyError:
        raise MusicError("No song could be found at the specified index.")

    node.queue = queue
    await lavalink.set_guild_node(ctx.guild_id, node)
    await ctx.respond(
        embed=hikari.Embed(
            description=f"Removed `{song_to_remove.track.info.title}` from the queue.",
            color=0x00FF00,
        )
    )


@music.command
@lightbulb.command("nowplaying", "See currently playing track's info")
@lightbulb.implements(lightbulb.SlashCommand)
async def nowplaying_command(ctx: lightbulb.Context) -> None:
    lavalink = fetch_lavalink(ctx.bot)
    view = Controls(author_id=ctx.author.id)
    node = await lavalink.get_guild_node(ctx.guild_id)

    if not node or not node.now_playing:
        raise MusicError("There's nothing playing at the moment!")

    embed = hikari.Embed(
        title="Now Playing",
        description=f"[{node.now_playing.track.info.title}]({node.now_playing.track.info.uri})",
        color=0x00FF00,
    )
    fields = [
        ("Requested by", f"<@{node.now_playing.requester}>", True),
        ("Author", node.now_playing.track.info.author, True),
    ]
    for name, value, inline in fields:
        embed.add_field(name=name, value=value, inline=inline)
    response = await ctx.respond(embed=embed, components=view.build())
    message = await response.message()
    view.start(message)
    await view.wait()


@music.command
@lightbulb.command("skip", "Skip the currently playing song")
@lightbulb.implements(lightbulb.SlashCommand)
@check_voice_state
async def skip_command(ctx: lightbulb.Context) -> None:
    lavalink = fetch_lavalink(ctx.bot)

    skip = await lavalink.skip(ctx.guild_id)
    node = await lavalink.get_guild_node(ctx.guild_id)

    if not skip:
        raise MusicError("There's nothing to skip!")

    if not node.queue and not node.now_playing:
        await lavalink.stop(ctx.guild_id)
    await ctx.respond(
        embed=hikari.Embed(
            title="⏭️ Skipped",
            description=f"[{skip.track.info.title}]({skip.track.info.uri})",
        )
    )


def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(music)
    miru.load(bot)


def unload(bot: lightbulb.BotApp) -> None:
    bot.remove_plugin(music)
