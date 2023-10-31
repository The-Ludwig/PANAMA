# How to develop

This project uses [`pdm`](https://pdm.fming.dev/latest/) since version 0.7.0.
There are nice tutorials available on how to use `pdm`.

## Installing this in dev mode

1. Install pdm

```bash
pip install pdm # requires at least python 3.7
```

2. Create a new virtual environment for the project and install all dependencies

```bash
pdm venv create
pdm install --venv in-project
```

## Entering the dev shell

1. Activate the virtual environment:

```bash
eval $(pdm venv activate in-project)
```

**or alternatively enter a new sub-shell with the right venv**

```bash
pdm run $SHELL
```
