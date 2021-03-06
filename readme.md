# Deploifai CLI

### Installation

```shell
pip install deploifai
```

### Usage

```shell
# ensure the cli is accessible
which deploifai
# show help message
deploifai --help
# show version
deploifai --version
```

## Contribute

### Setup Development Environment

Create python virtual environment:

```shell
python -m venv .venv
source .venv/bin/activate
````

Install dev dependencies:

```shell
pip install -U pip
pip install -r requirements.txt
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
