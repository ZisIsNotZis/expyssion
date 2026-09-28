# expyssion

**Expyssion** is a Python-hosted expression language: everything is an expression, and everything is a call. The language reference is in [`LANGUAGE.md`](LANGUAGE.md); design and implementation notes are under [`docs/`](docs/).

## Install and use

Requires Python 3.12 or newer. Install the project in a Python environment, then invoke the `expy` command:

```sh
python -m pip install .
expy --help
```

For development, install the dev dependency group with `uv sync --group dev` and run the test suite with `uv run pytest`.

The language and CLI are under active development; consult `LANGUAGE.md` for the supported syntax and semantics.

## License

AGPL-3.0-only; see [`LICENSE`](LICENSE).