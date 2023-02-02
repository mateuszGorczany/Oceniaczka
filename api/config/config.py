from typing import Union
from pydantic import AnyHttpUrl, BaseSettings, Field



class Settings(BaseSettings):
    SECRET_KEY: str = Field('my super secret key', env='SECRET_KEY')
    BACKEND_CORS_ORIGINS: list[Union[str, AnyHttpUrl]] = ['http://localhost:8000']
    OPENAPI_CLIENT_ID: str = Field(default='', env='OPENAPI_CLIENT_ID')
    APP_CLIENT_ID: str = Field(default='', env='APP_CLIENT_ID')
    TENANT_ID: str = Field(default='', env='TENANT_ID')
    DB: str = Field(default='', env='TENANT_ID')
    TENANT_ID: str = Field(default='', env='TENANT_ID')
    DB_ACCOUNT_URI: str = Field(default='', env="DB_ACCOUNT_URI")
    DB_ACCOUNT_KEY: str = Field(default='', env="DB_ACCOUNT_KEY")
    DB_NAME: str = Field(default='', env="DB_NAME")

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'
        case_sensitive = True

settings = Settings()