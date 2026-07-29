from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application configuration.

    Loads values from environment variables
    and .env automatically.
    """

    # Application
    APP_NAME: str = "SellerOS"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "sqlite:///./selleros.db"

    # JWT
    SECRET_KEY: str = "CHANGE_THIS_IN_PRODUCTION"

    JWT_ALGORITHM: str = "HS256"

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    # CORS — the frontend (React, its own dev-server origin e.g.
    # http://localhost:5173 or http://localhost:3000) calls this API
    # from the browser, which enforces CORS regardless of how trusted
    # the origin actually is. Comma-separated in .env, e.g.:
    #   CORS_ORIGINS=http://localhost:5173,https://app.selleros.com
    # Defaults cover the two most common React dev-server ports so this
    # works out of the box before a real frontend origin exists yet.
    CORS_ORIGINS: str = "http://localhost:8443,http://localhost:5173,http://localhost:3000"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


DEFAULT_SECRET_KEY = "CHANGE_THIS_IN_PRODUCTION"


class InsecureConfigurationError(RuntimeError):
    """Raised at startup when running with unsafe defaults."""


def assert_secret_key_is_safe(config: "Settings") -> None:
    """
    Refuse to proceed if DEBUG=False and SECRET_KEY is still the
    shipped placeholder — that combination means every JWT this
    process issues is signed with a key published in the repo's
    source, so anyone can forge a valid token for any user_id without
    a real login. Pulled out as a standalone function (rather than
    inlined in main.py's startup event) so it can be unit-tested
    directly without booting the whole app.
    """
    if not config.DEBUG and config.SECRET_KEY == DEFAULT_SECRET_KEY:
        raise InsecureConfigurationError(
            "SECRET_KEY is still set to the default placeholder "
            f"('{DEFAULT_SECRET_KEY}') while DEBUG=False. Set a real, "
            "random SECRET_KEY in the environment (or .env) before "
            "starting in production. Refusing to start."
        )


settings = Settings()