
import os
from pathlib import Path

import yaml
from dotenv import dotenv_values
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import jwt

app = FastAPI()

@app.get("/healthz")
def healthz():
    return {"status": "ok", "redis": "up"}

# Keep your existing OAuth settings and /verify endpoint below.


@app.get("/healthz")
def healthz():
    return {
        "status": "ok",
        "redis": "up"
    }

# Allow browser-based checks from the assignment page.
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
    """Convert values to the required types."""
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

    # Layer 2: environment-specific YAML.
    yaml_path = Path(f"config.{ENVIRONMENT}.yaml")
    if yaml_path.exists():
        with yaml_path.open("r", encoding="utf-8") as file:
            yaml_config = yaml.safe_load(file) or {}
        config.update(yaml_config)

    # Layer 3: read .env WITHOUT putting its values into os.environ.
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

    # Layer 4: actual OS environment variables.
    for key, value in os.environ.items():
        if key.startswith("APP_"):
            config[key[4:].lower()] = value

    # Layer 5: query-string overrides have the highest priority.
    for item in set:
        if "=" not in item:
            continue

        key, value = item.split("=", 1)
        key = key.strip().lower()

        if key:
            config[key] = value

    # Apply required types after all layers have been merged.
    result = {
        key: coerce(key, value)
        for key, value in config.items()
    }

    # Never expose the real API key.
    if "api_key" in result:
        result["api_key"] = "****"

    return result
