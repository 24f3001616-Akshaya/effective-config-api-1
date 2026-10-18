
import os
from pathlib import Path

import yaml
from dotenv import dotenv_values
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

@app.get("/healthz")
def healthz():
    return {"status": "ok", "redis": "up"}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

DEFAULTS = {
    "port": 8000,
    "workers": 1,
    "debug": False,
    "log_level": "info",
    "api_key": "default-secret-000",
}

ENVIRONMENT = "development"


def coerce(key, value):
    if key in ("port", "workers"):
        return int(value)

    if key == "debug":
        if isinstance(value, bool):
            return value
        return str(value).strip().lower() in (
            "true", "1", "yes", "on"
        )

    return str(value)


@app.get("/effective-config")
def effective_config(set: list[str] = Query(default=[])):
    config = DEFAULTS.copy()

    yaml_path = Path(f"config.{ENVIRONMENT}.yaml")
    if yaml_path.exists():
        with yaml_path.open("r", encoding="utf-8") as file:
            yaml_config = yaml.safe_load(file) or {}
        config.update(yaml_config)

    env_path = Path(".env")
    file_env = dotenv_values(env_path) if env_path.exists() else {}

    for key, value in file_env.items():
        if value is None:
            continue

        if key == "NUM_WORKERS":
            config["workers"] = value
        elif key.startswith("APP_"):
            config[key[4:].lower()] = value
        else:
            config[key.lower()] = value

    for key, value in os.environ.items():
        if key.startswith("APP_"):
            config[key[4:].lower()] = value

    for item in set:
        if "=" not in item:
            continue

        key, value = item.split("=", 1)
        key = key.strip().lower()

        if key:
            config[key] = value

    result = {
        key: coerce(key, value)
        for key, value in config.items()
    }

    if "api_key" in result:
        result["api_key"] = "****"

    return result
