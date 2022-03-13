from pydantic import BaseSettings


class BotConfig(BaseSettings):
    token: str
    test_guilds: list[int]
    logging_channel: int

    class Config:
        env_file = ".env"
        env_prefix = "bot_"


bot_config = BotConfig()
