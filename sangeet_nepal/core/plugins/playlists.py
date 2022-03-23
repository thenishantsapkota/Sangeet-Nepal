from datetime import datetime

import hikari
import lightbulb
from miru.ext import nav
from models import SavedPlaylists
from sangeet_nepal.core.plugins import MusicError, _chunk


class CommandError(lightbulb.LightbulbError):
    pass


playlist_plugin = lightbulb.Plugin(
    "Playlists", "Plugin that handles all playlists related commands"
)


@playlist_plugin.command
@lightbulb.command("playlist", "Base command for all the playlist commands")
@lightbulb.implements(lightbulb.SlashCommandGroup)
async def playlist_command(ctx: lightbulb.Context) -> None:
    pass


@playlist_command.child
@lightbulb.option("name", "Name of this specific playlist")
@lightbulb.option("url", "The URL of the playlist")
@lightbulb.command("save", "Save your playlist!", pass_options=True)
@lightbulb.implements(lightbulb.SlashSubCommand)
async def playlist_save_command(ctx: lightbulb.Context, url: str, name: str) -> None:
    model = await SavedPlaylists.create(
        member_id=ctx.author.id,
        playlist_name=name,
        playlist_url=url,
    )
    await ctx.respond(
        embed=hikari.Embed(
            description="✅ Playlist has been saved successfully!", color=0x00FF00
        )
        .add_field(name="ID", value=model.id, inline=True)
        .add_field(name="Playlist Name", value=name, inline=True)
        .add_field(name="Playlist URL", value=url, inline=False)
    )


@playlist_command.child
@lightbulb.command("list", "List all the available playlists")
@lightbulb.implements(lightbulb.SlashSubCommand)
async def playlist_list_command(ctx: lightbulb.Context) -> None:
    models = await SavedPlaylists.filter(member_id=ctx.author.id)
    if not len(models):
        raise CommandError("❌ You don't have any playlists saved!")
    playlists = [
        f"**ID** - #{model.id}\n**Playlist Name** - {model.playlist_name}\n**Playlist URL** - {model.playlist_url}"
        for model in models
    ]
    fields = [
        hikari.Embed(
            title=f"Saved Playlists of {ctx.author.username}",
            description="\n\n".join(data),
            color=0x00FF00,
            timestamp=datetime.now().astimezone(),
        )
        for data in _chunk(playlists, 5)
    ]
    navigator = nav.NavigatorView(pages=fields)
    await navigator.send(ctx.interaction)
    await navigator.wait()


@playlist_command.child
@lightbulb.option("playlist_id", "ID of the playlist to be deleted", type=int)
@lightbulb.command("delete", "Delete a saved playlist!", pass_options=True)
@lightbulb.implements(lightbulb.SlashSubCommand)
async def playlist_delete_command(ctx: lightbulb.Context, playlist_id: int) -> None:
    model = await SavedPlaylists.get_or_none(id=playlist_id)
    if model is None:
        raise CommandError(f"❌ Playlist with ID `{playlist_id}` couldn't be found!")
    if model.member_id != ctx.author.id:
        raise CommandError("❌ That playlist doesn't belong to you!")
    await model.delete()
    await ctx.respond(
        embed=hikari.Embed(
            description=f"✅ Playlist with ID `{playlist_id}` was deleted successfully",
            color=0x00FF00,
        )
    )


@playlist_command.child
@lightbulb.command("global", "List all the playlists of the guild")
@lightbulb.implements(lightbulb.SlashSubCommand)
async def playlist_global_command(ctx: lightbulb.Context) -> None:
    models = await SavedPlaylists.all()
    if not len(models):
        raise MusicError("❌There are no playlists saved yet!")
    playlists = [
        f"**ID** - #{model.id}\n**Playlist Name** - {model.playlist_name}\n**Playlist URL** - {model.playlist_url}\n**Saved by** - <@{model.member_id}>"
        for model in models
    ]
    fields = [
        hikari.Embed(
            title="Saved Playlists",
            description="\n\n".join(data),
            color=0x00FF00,
            timestamp=datetime.now().astimezone(),
        )
        for data in _chunk(playlists, 5)
    ]
    navigator = nav.NavigatorView(pages=fields)
    await navigator.send(ctx.interaction)
    await navigator.wait()


def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(playlist_plugin)


def unload(bot: lightbulb.BotApp) -> None:
    bot.remove_plugin(playlist_plugin)
