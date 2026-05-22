from decouple import config


class Config:
    BASE_URL: str = config("BASE_URL", default="https://plt.keu.kz/rest")

    TELEGRAM_BOT_TOKEN: str = config("TELEGRAM_BOT_TOKEN", default="")
    
    JOURNAL_DIRECTORY: str = config("JOURNAL_DIRECTORY", default="./journals")
    SETTINGS_DIRECTORY: str = config("SETTINGS_DIRECTORY", default="./settings")
    AUTH_DIRECTORY: str = config("AUTH_DIRECTORY", default="./auths")
    
    YEAR: int = config("YEAR", default=2025, cast=int)
    SEMESTER: int = config("SEMESTER", default=2, cast=int)
    CHECK_INTERVAL: int = config("CHECK_INTERVAL", default=60, cast=int)
    CONCURRENCY: int = config("CONCURRENCY", default=10, cast=int)


app_config = Config()
