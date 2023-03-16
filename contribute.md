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

## Build

### Python build

To build a distributable wheel, run:

```shell
python -m build
```

It should now be available in `dist` directory.

### Homebrew

To create a dependency file for homebrew.

First, create a new virtual environment, and install `deploifai`.

```shell
python -m venv .venv-homebrew
source .venv-homebrew/bin/activate
pip install -U pip wheel setuptools
pip install --editable .
```

Then, install `homebrew-pypi-poet`.

```shell
pip install homebrew-pypi-poet
```

Finally, run `poet` to generate the dependency file.

```shell
poet --formula deploifai > deploifai.rb
```

The generated `resource` stanzas are the python dependencies. Copy them to the `Formula/deploifai.rb` file in [homebrew-deploifai](https://github.com/deploifai/homebrew-deploifai) repository.
**Do not copy the entire file.**

Bump the `version` and git `tag` in the `Formula/deploifai.rb` file.

## Developer Documentation

MKDocs is used to generate the documentation for the `deploifai.cli` module. It is already installed in `requirements/dev.txt`.

It uses `mkdocs-click` plugin to generate content from the `click` commands.

```shell
mkdocs serve
```

See `docs` directory for setup of different pages.

## CI/CD

Github actions are used to automatically release this package to pypi, and generate a formula for homebrew.

To release on homebrew, simply copy the generated [release/homebrew/deploifai.rb] file to the `Formula/deploifai.rb` file in [homebrew-deploifai](https://github.com/deploifai/homebrew-deploifai) repository.
