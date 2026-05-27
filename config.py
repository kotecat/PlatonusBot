from decouple import config


class Config:
    BASE_URL: str = config("BASE_URL", default="https://m.platonus.kz/pms/api/mobile/university/notMedicalUniversities")

    TELEGRAM_BOT_TOKEN: str = config("TELEGRAM_BOT_TOKEN", default="")
    
    JOURNAL_DIRECTORY: str = config("JOURNAL_DIRECTORY", default="./storage/journals")
    SETTINGS_DIRECTORY: str = config("SETTINGS_DIRECTORY", default="./storage/settings")
    AUTH_DIRECTORY: str = config("AUTH_DIRECTORY", default="./storage/auths")
    
    CHECK_INTERVAL: int = config("CHECK_INTERVAL", default=60, cast=int)
    CONCURRENCY: int = config("CONCURRENCY", default=10, cast=int)
    AUTO_CHECK_ENABLED: bool = config("AUTO_CHECK_ENABLED", default=False, cast=bool)


app_config = Config()
