[![Build Status](https://github.com/OCHA-DAP/hdx-python-country/actions/workflows/run-python-tests.yaml/badge.svg)](https://github.com/OCHA-DAP/hdx-python-country/actions/workflows/run-python-tests.yaml)
[![Coverage Status](https://coveralls.io/repos/github/OCHA-DAP/hdx-python-country/badge.svg?branch=main&ts=1)](https://coveralls.io/github/OCHA-DAP/hdx-python-country?branch=main)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Downloads](https://img.shields.io/pypi/dm/hdx-python-country.svg)](https://pypistats.org/packages/hdx-python-country)

The HDX Python Country Library provides utilities to map between country and region
codes and names and to match administrative level names from different sources.
It also provides utilities for foreign exchange enabling obtaining current and historic
FX rates for different currencies.

It provides country mappings including ISO 2 and ISO 3 letter codes (ISO 3166) and regions
using live official data from the [UN OCHA](https://vocabulary.unocha.org/) feed with
fallbacks to an internal static file if there is any problem with retrieving data from
the url. (Also it is possible to force the use of the internal static files.)

It can exact match English, French, Spanish, Russian, Chinese and Arabic. There is a
fuzzy matching for English look up that can handle abbreviations in country names like
Dem. for Democratic and Rep. for Republic.

Mapping administration level names from a source to a given base set is also handled
including phonetic fuzzy name matching.

It also provides foreign exchange rates and conversion from amounts in local
currency to USD and vice-versa. The conversion relies on Yahoo Finance, falling
back on [currency-api](https://github.com/fawazahmed0/currency-api) for current rates, and Yahoo Finance falling back
on IMF data via IATI (with interpolation) for historic daily rates.

For more information, please read the [documentation](https://hdx-python-country.readthedocs.io/en/latest/).

This library is part of the [Humanitarian Data Exchange](https://data.humdata.org/)
(HDX) project. If you have humanitarian related data, please upload your datasets to
HDX.

# Development

## Environment

Development is currently done using Python 3.13. The environment can be created with:

```shell
    uv sync
```

This creates a .venv folder with the versions specified in the project's uv.lock file.

### Pre-commit

pre-commit will be installed when syncing uv. It is run every time you make a git
commit if you call it like this:

```shell
    pre-commit install
```

With pre-commit, all code is formatted according to
[ruff](https://docs.astral.sh/ruff/) guidelines.

To check if your changes pass pre-commit without committing, run:

```shell
    pre-commit run --all-files
```

## Packages

[uv](https://github.com/astral-sh/uv) is used for package management.  If
you’ve introduced a new package to the source code (i.e. anywhere in `src/`),
please add it to the `project.dependencies` section of `pyproject.toml` with
any known version constraints.

To add packages required only for testing, add them to the
`[dependency-groups]`.

Any changes to the dependencies will be automatically reflected in
`uv.lock` with `pre-commit`, but you can re-generate the files without committing by
executing:

```shell
    uv lock --upgrade
```

## Project

[uv](https://github.com/astral-sh/uv) is used for project management. The project can be
built using:

```shell
    uv build
```

Linting and syntax checking can be run with:

```shell
    uv run ruff check
```

To run the tests and view coverage, execute:

```shell
    uv run pytest
```

## Documentation

The documentation, including API documentation, is generated using ReadtheDocs and
MkDocs with Material. As you change the source code, remember to update the
documentation at `documentation/index.md`.
