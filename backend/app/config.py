""" The configuration of the backend."""
import json
import os


class Config:
    def __init__(self, filename: str):
        self.db_path: str = self._get_db_path()
        self.database_url: str = f"sqlite:///{self.db_path}todo.db"
        self.reload: bool = os.getenv("RELOAD", "true").lower() == "true"
        self.config_file: str = filename
        self._get_db_path()

    def _get_db_path(self) -> str:
        try:
            DATABASE_URL = os.environ["DATABASE_URL"]
            return DATABASE_URL
        except KeyError as err:
            pass
            with open(self.config_file, encoding="utf-8") as f:
                config = json.load(f)
                self.port: int = int(config.get("PORT"))
                self.host: str = config.get("HOST")
                return config.get("db_path", "")
        except FileNotFoundError:
            raise ValueError("Specify the config file or set the environment variable 'DATABASE_URL'!")