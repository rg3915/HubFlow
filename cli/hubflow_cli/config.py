import os
import tomllib
from pathlib import Path

DEFAULT_URL = 'http://localhost:8000'


def config_path():
    base = os.environ.get('HUBFLOW_CONFIG_DIR') or Path.home() / '.config' / 'hubflow'
    return Path(base) / 'config.toml'


def load_config():
    path = config_path()
    if not path.exists():
        return {}
    return tomllib.loads(path.read_text())


def save_config(data):
    path = config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(''.join(f'{key} = "{value}"\n' for key, value in data.items()))
    path.chmod(0o600)


def api_url():
    return os.environ.get('HUBFLOW_URL') or load_config().get('url') or DEFAULT_URL


def token():
    return os.environ.get('HUBFLOW_TOKEN') or load_config().get('token')
