from dataclasses import dataclass

import yaml


@dataclass
class LoggingConfig:
    log_file_name: str


@dataclass
class DatabaseConfig:
    name: str


@dataclass
class GPTConfig:
    model: str
    token: str
    temperature: float
    max_tokens: int
    n: int


@dataclass
class LineBotConfig:
    channel_access_token: str
    channel_secret: str
    default_rich_menu_id: str
    default_rich_menu_img_path: str


@dataclass
class AppConfig:
    logging: LoggingConfig
    database: DatabaseConfig
    gpt: GPTConfig
    line_bot: LineBotConfig

    @staticmethod
    def load(file_path: str):
        with open(file_path, 'r') as file:
            config_data = yaml.safe_load(file)

        logging_config = LoggingConfig(**config_data['logging'])
        database_config = DatabaseConfig(**config_data['database'])
        gpt_config = GPTConfig(**config_data['gpt'])
        line_bot_config = LineBotConfig(**config_data['line_bot'])

        return AppConfig(logging=logging_config, database=database_config,
                         gpt=gpt_config, line_bot=line_bot_config)


appconfig = AppConfig.load("config/local.yaml")
