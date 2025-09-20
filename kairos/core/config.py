import os
import warnings
from datetime import timedelta
from typing import Literal

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_ignore_empty=True,
        extra="ignore",
    )
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "")


    # 60 minutes * 24 hours * 8 days = 8 days
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    VERIFICATION_TOKEN_EXPIRE_MINUTES: int = 15
    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES: int = 15
    ENVIRONMENT: Literal["local", "staging", "production"] = "local"

    CORS_ORGINS: list[str] = ["*"]

    PROJECT_NAME: str = "App"

    MAIL_USERNAME: str = "resend"
    MAIL_PASSWORD: str = ""
    MAIL_FROM: str = "send.findkairos.com"
    MAIL_PORT: int = 587
    MAIL_SERVER: str = "smtp.resend.com"

    RESEND_API_KEY: str = ""

    @computed_field
    @property
    def ACCESS_TOKEN_EXPIRE_DELTA(self) -> timedelta:
        """Convert minutes to timedelta object"""
        return timedelta(minutes=self.ACCESS_TOKEN_EXPIRE_MINUTES)


    @computed_field
    @property
    def REFRESH_TOKEN_EXPIRE_DELTA(self) -> timedelta:
        """Convert minutes to timedelta object"""
        return timedelta(minutes=self.REFRESH_TOKEN_EXPIRE_MINUTES)


    @computed_field
    @property
    def VERIFICATION_TOKEN_EXPIRE_DELTA(self) -> timedelta:
        """Convert minutes to timedelta object"""
        return timedelta(minutes=self.VERIFICATION_TOKEN_EXPIRE_MINUTES)

    @computed_field
    @property
    def PASSWORD_RESET_TOKEN_EXPIRE_DELTA(self) -> timedelta:
        """Convert minutes to timedelta object"""
        return timedelta(minutes=self.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES)

    def _check_default_secret(self, var_name: str, value: str | None) -> None:
        if value == "changethis":
            message = (
                f'The value of {var_name} is "changethis", '
                "for security, please change it, at least for deployments."
            )
            if self.ENVIRONMENT == "local":
                warnings.warn(message, stacklevel=1)
            else:
                raise ValueError(message)


settings = Settings()
