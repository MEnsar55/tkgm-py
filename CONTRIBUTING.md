# Contributing to tkgm-py

Thank you for your interest in contributing! Here's how to get started.

## Setup

```bash
git clone https://github.com/MEnsar55/tkgm-py.git
cd tkgm-py
pip install -e ".[dev]"
```

## Running Tests

```bash
pytest
```

## Code Style

This project uses **ruff** for linting and **mypy** for type checking.

```bash
ruff check tkgm/
mypy tkgm/
```

## Guidelines

- **Type hints** are required on all public functions and methods.
- **Bilingual comments**: add a Turkish translation below every English docstring/comment.
- Keep the public API minimal — new methods should cover a real use case.
- All new endpoints should raise the appropriate `TKGMError` subclass.

## Submitting a PR

1. Fork the repo and create a branch: `git checkout -b feat/my-feature`
2. Make your changes and add tests.
3. Open a Pull Request against `master` and fill in the template.

## Reporting Issues

Use the [GitHub issue tracker](https://github.com/MEnsar55/tkgm-py/issues).
Please include:
- Python version
- Full traceback
- Minimal reproducible example
