# expyssion

> **Status: closed (milestone, 2026-09-29).** The language reached a frozen
> `LANGUAGE.md` v1 spec plus a working Python-hosted v1 implementation. No
> further development is planned unless the project's inputs or goals change.

**Expyssion** is a Python-hosted expression language: everything is an expression, and everything is a call. The language reference is in [`LANGUAGE.md`](LANGUAGE.md); design and implementation notes are under [`docs/`](docs/).

## Install and use

Requires Python 3.12 or newer. Install the project in a Python environment, then invoke the `expy` command:

```sh
python -m pip install .
expy --help
```

For development, install the dev dependency group with `uv sync --group dev` and run the test suite with `uv run pytest`.

`LANGUAGE.md` is the frozen v1 reference for the supported syntax and semantics. The implementation is complete for that spec; see [`docs/project-status.md`](docs/project-status.md).

## License

AGPL-3.0-only; see [`LICENSE`](LICENSE).