import json

import boto3
from botocore.exceptions import ClientError
from pydantic import BaseSettings, SecretStr


class ConfigException(Exception):
    pass


class Config(BaseSettings):
    gandi_api_key: SecretStr


class BaseConfig(BaseSettings):
    secret_name: str
    secret_region: str

    class Config:
        case_sensitive = False

    def get_config(self) -> Config:
        session = boto3.session.Session()
        client = session.client(
            service_name="secretsmanager", region_name=self.secret_region
        )

        try:
            get_secret_value_response = client.get_secret_value(
                SecretId=self.secret_name
            )
        except ClientError as e:
            raise ConfigException("Failed to retrieve secret") from e

        if "SecretString" in get_secret_value_response:
            secret = get_secret_value_response["SecretString"]
        else:
            raise ConfigException("Secret must be a string")

        return Config(**json.loads(secret))
