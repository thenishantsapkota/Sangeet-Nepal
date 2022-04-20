import asyncio
import logging

import hikari
import lavasnek_rs
import lightbulb
from tortoise import Tortoise
from tortoise_config import tortoise_config

from ..config import bot_config, lavalink_config
from .lavalink_events import LavalinkEvents

logger = logging.getLogger(__name__)
HIKARI_VOICE = False


class Data:
    def __init__(self) -> None:
        self.lavalink: lavasnek_rs.Lavalink | None = None


class SangeetNepal(lightbulb.BotApp):
    def __init__(self) -> None:
        super().__init__(
            token=bot_config.token,
            intents=hikari.Intents.ALL,
        )
        self.data = Data()

    def run_bot(self) -> None:
        self.event_manager.subscribe(hikari.StartingEvent, self.on_starting)
        self.event_manager.subscribe(hikari.StartedEvent, self.on_started)
        self.event_manager.subscribe(hikari.StoppingEvent, self.on_stopping)
        self.event_manager.subscribe(hikari.StoppedEvent, self.on_stopped)
        self.event_manager.subscribe(hikari.ShardReadyEvent, self.on_shard_ready)

        super().run(
            activity=hikari.Activity(
                name="Thanks for the donation Brahma <3",
                type=hikari.ActivityType.PLAYING,
            )
        )

    async def on_starting(self, _: hikari.StartingEvent) -> None:
        self.load_extensions_from("./sangeet_nepal/core/plugins", recursive=True)
        asyncio.create_task(self.connect_database())

    async def on_started(self, _: hikari.StartedEvent) -> None:
        logger.info("The bot is marked as Online!")

    async def on_stopping(self, _: hikari.StoppingEvent) -> None:
        ...

    async def on_stopped(self, _: hikari.StoppedEvent) -> None:
        ...

    async def on_shard_ready(self, _: hikari.ShardReadyEvent) -> None:
        builder = (
            lavasnek_rs.LavalinkBuilder(self.get_me(), bot_config.token)
            .set_host("lavalink")
            .set_password(lavalink_config.password)
        )
        if HIKARI_VOICE:
            builder.set_start_gateway(False)
        event_handler = LavalinkEvents(self)
        lava_client = await builder.build(event_handler)
        self.data.lavalink = lava_client

    async def connect_database(self) -> None:
        logger.info("Initializing the connection to the database...")
        await Tortoise.init(tortoise_config)
        logger.info("Connection established to the database successfully!")
