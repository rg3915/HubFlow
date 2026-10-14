import pytest
from typer.testing import CliRunner

from hubflow_cli.main import app


@pytest.fixture(autouse=True)
def config_dir(tmp_path, monkeypatch):
    monkeypatch.setenv('HUBFLOW_CONFIG_DIR', str(tmp_path))
    monkeypatch.setenv('HUBFLOW_URL', 'http://api.test')
    monkeypatch.delenv('HUBFLOW_TOKEN', raising=False)
    return tmp_path


@pytest.fixture
def run():
    runner = CliRunner()
    return lambda *args, **kwargs: runner.invoke(app, list(args), **kwargs)
