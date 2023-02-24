# Contribute

## Setup Development Environment

Create python virtual environment:

```shell
python -m venv .venv
source .venv/bin/activate
````

Install dev dependencies:

```shell
pip install -U pip wheel setuptools
pip install -r requirements/deploifai.txt requirements/cli.txt requirements/dev.txt
```

Copy `sample.env` to `.env`:

```text
DEPLOIFAI_CLI_ENVIRONMENT=development
DEPLOIFAI_BACKEND_URL=http://localhost:4000
```

Run the deploifai cli script directly for testing:

```shell
python dev.py
```

Or, install `deploifai` cli tool in virtual environment for testing:

```shell
pip install --editable . 
```

It will generate a `deploifai` executable in `.venv/bin` directory.

## Developer Documentation

MKDocs is used to generate the documentation for the `deploifai.cli` module. It is already installed in `requirements/dev.txt`.

It uses `mkdocs-click` plugin to generate content from the `click` commands.

```shell
mkdocs serve
```

See `docs` directory for setup of different pages.
