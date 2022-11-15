# https://rednafi.github.io/digressions/python/2020/06/03/python-configs.html
import os
from typing import Optional, Union

from pydantic import BaseSettings, Field, MongoDsn


class GlobalConfig(BaseSettings):
    ENV_STATE: str = Field(default="dev", env="ENV_STATE")
    DB_NAME: str = Field(default="appStoreDB")
    FRONTEND_HOST: str = Field(default="http://localhost:9000")
    ALGORITHM: str = Field(default="HS256")
    MAX_UPLOAD_SIZE_GB: Union[int, float] = Field(default=1)
    SECRET_KEY: Optional[
        str
    ] = None  # NOTE: set to none as a hack to get Sphinx to build correctly
    ADMIN_SECRET_KEY: Optional[str] = None
    MONGO_DSN: Optional[MongoDsn] = None
    MONGO_USERNAME: Optional[str] = None
    MONGO_PASSWORD: Optional[str] = None
    IE_NAMESPACE: Optional[str] = None
    CLEARML_CONFIG_FILE: Optional[str] = None
    K8S_HOST: Optional[str] = None
    K8S_API_KEY: Optional[str] = None
    CLEARML_WEB_HOST: Optional[str] = None
    CLEARML_API_HOST: Optional[str] = None
    CLEARML_FILES_HOST: Optional[str] = None
    CLEARML_API_ACCESS_KEY: Optional[str] = None
    CLEARML_API_SECRET_KEY: Optional[str] = None

    class Config:
        env_file: str = "./src/config/.env"

    def set_envvar(self):
        """Temporarily set environment variables.
        This change will not be permanent, so no
        need to worry about overriding system
        envvars.
        """
        for key, value in self.dict(exclude_none=True).items():
            # Save config to environment
            os.environ[key] = str(value)


class DevConfig(GlobalConfig):
    class Config:
        env_prefix: str = "DEV_"


class StagingConfig(GlobalConfig):
    class Config:
        env_prefix: str = "STG_"


class ProductionConfig(GlobalConfig):
    class Config:
        env_prefix: str = "PROD_"


class TestingConfig(GlobalConfig):
    class Config:
        env_prefix: str = "TEST_"


class FactoryConfig:
    """Return config instance based on `ENV_STATE` variable"""

    def __init__(self, env_state: Optional[str]):
        self.env_state = env_state

    def __call__(self):
        if self.env_state == "dev":
            return DevConfig()
        elif self.env_state == "stg":
            return StagingConfig()
        elif self.env_state == "prod":
            return ProductionConfig()
        elif self.env_state == "test":
            return TestingConfig()
        elif self.env_state is None:
            return None
        else:
            raise ValueError(f"Unsupported config: {self.env_state}")


ENV_STATE = GlobalConfig().ENV_STATE
config = FactoryConfig(ENV_STATE)()

if config is not None:
    config.set_envvar()
