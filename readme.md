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

Commands on the Deploifai CLI:

```shell
auth           Manage Deploifai's authentication state.
cloud-profile  Manage user's cloud profiles
dataset        Manage datasets and dataset storages on Deploifai
mlflow         Set-up and manage the ML FLow Integration
project        Initialise, manage, and deploy an ML project
server         Manage training servers on Deploifai
workspace      Manage, and browse available workspaces
```

Subcommands for each command:

```shell
auth                    Manage Deploifai's authentication state.
deploifai auth login    Login using personal access token
deploifai auth logout   Logout to remove access
```

```shell
  cloud-profile                     Manage user's cloud profiles
  deploifai cloud-profile create    Create a new cloud profile
  deploifai cloud-profile list      List all cloud profiles in the current workspace
```

```shell
  dataset                   Manage datasets and dataset storages on Deploifai
  deploifai dataset create  Create a new dataset
  deploifai dataset info
  deploifai dataset init    Initialise the current directory as a dataset
  deploifai dataset list    Command to list all datasets in the current project
  deploifai dataset push
```

```shell
mlflow                      Set-up and manage the ML FLow Integration
deploifai mlflow get-setup  Get setup to integrate mlflow in training scripts
```

```shell
  project                   Initialise, manage, and deploy an ML project
  deploifai project browse  Command to open a project in the Web Browser
  deploifai project create  Create a new project
  deploifai project list    Command to list all projects in the current workspace
```

```shell
server                   Manage training servers on Deploifai
deploifai server create  Create a new Training Server
deploifai server list    Command to list out all training servers in current workspace
```

```shell
workspace                 Manage, and browse available workspaces
deploifai workspace list  Lists out all available workspaces
deploifai workspace set   Changes current workspace
```