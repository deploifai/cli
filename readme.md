# Deploifai CLI

## Installation

```shell
pip install deploifai
```

Or, install from homebrew:

```shell
brew tap deploifai/deploifai
brew install deploifai
```

## Usage

Ensure that you have installed correctly.

```shell
# show help message
deploifai --help
# show version
deploifai --version
```

### Authentication

First, generate a personal access token on your Deploifai [dashboard](https://deploif.ai/dashboard) settings.

Then, login to the cli tool:

```shell
deploifai auth login -u [username] -t [token]
```

## Documentation

See the [documentation](https://docs.deploif.ai/cli/commands/quick-start) for more information about the CLI.
