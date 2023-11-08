from panama import __logo__, __version__
from importlib.metadata import version

def test_logo():
    logo = __logo__
    assert len(logo) > 500
    assert "v" in logo


def test_version():
    assert __version__ == version("corsika-panama").replace("+editable", "")
