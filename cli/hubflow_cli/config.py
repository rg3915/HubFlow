import tomllib
from pathlib import Path

from decouple import Config, RepositoryEmpty

# Só variáveis de ambiente (sem procurar .env): a CLI instalada não deve ler o .env da pasta onde for chamada.
env = Config(RepositoryEmpty())

DEFAULT_URL = 'http://localhost:8000'


def config_path():
    base = env('HUBFLOW_CONFIG_DIR', default='') or Path.home() / '.config' / 'hubflow'
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
    return env('HUBFLOW_URL', default='') or load_config().get('url') or DEFAULT_URL


def token():
    return env('HUBFLOW_TOKEN', default='') or load_config().get('token')
