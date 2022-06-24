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

Install `deploifai` cli tool for testing:

```shell
pip install --editable . 
```
