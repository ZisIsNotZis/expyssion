# Contributing to expyssion

expyssion v1 is a closed milestone: the spec in [`LANGUAGE.md`](LANGUAGE.md) is frozen and no further development is planned. Bug fixes, test improvements and documentation corrections are welcome.

## Before you start

- For a bug or a documentation error, open an issue describing what you expected and what happened.
- For a language or semantics change, open an issue first. Accepted changes must update the spec, the semantic-equivalence corpus in [`docs/transpilation.md`](docs/transpilation.md), and the tests together. Decisions belong in [`wayfinder/`](wayfinder/) and, when the execution model changes, in [`docs/adr/`](docs/adr/).
- Read [`CONTEXT.md`](CONTEXT.md) for the terminology and [`LANGUAGE.md`](LANGUAGE.md) for the normative semantics.

## Development setup

Requires Python 3.12+ and [uv](https://docs.astral.sh/uv/).

```sh
uv sync --group dev
uv run pytest
uv run python docs/verify_corpus.py
```

Run a program with `uv run expy <file.expy>`. The end-to-end fixtures live in [`tests/programs/`](tests/programs/).

## Pull requests

- Keep each change focused and explain why it is needed.
- Add or update a test for every behavior change; a fix without a regression test is incomplete.
- Do not change `uv.lock` unless dependencies actually change.
- Match the style of the surrounding code and keep documentation in one home: the spec owns semantics, ADRs own rationale, the README only summarizes.

## License

Contributions are accepted under [AGPL-3.0-only](LICENSE), the project license.
