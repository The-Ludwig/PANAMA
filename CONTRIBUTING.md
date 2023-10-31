# How to develop

This project uses [`pdm`](https://pdm.fming.dev/latest/) since version 0.7.0.
There are nice tutorials available on how to use `pdm`.

A TLDR of my workflow:

1. Install pdm

```
pip install pdm # requires at least python 3.7
```

2. Create a new virtual environment for the project and install all dependencies

```
PDM_IGNORE_ACTIVE_VENV= pdm install --plugins
```

The environment variable `PDM_IGNORE_ACTIVE_VENV` does not need to be set if you are not currently in a venv.

3. Activate the virtual environment:

```
eval $(pdm venv activate)
```

_or alternatively enter a new sub-shell with the right venv_

```
pdm run $SHELL
```
