import os
import click
from appdirs import AppDirs
import configparser

cli_environment = os.environ.get("DEPLOIFAI_CLI_ENVIRONMENT", "production")
is_cli_env_dev = cli_environment == "development"

dirs = AppDirs(".deploifai-cli", "Deploifai Limited")
config_filename = "deploifai.cfg"
config_directory = (
    dirs.user_config_dir
    if not is_cli_env_dev
    else os.path.dirname(os.path.realpath(__file__))
)
config_filepath = os.path.join(config_directory, config_filename)

config_sections = ["AUTH"]


class DeploifaiContextObj:
    cli_environment = cli_environment
    is_cli_env_dev = is_cli_env_dev

    def __init__(self):
        config = configparser.ConfigParser()

        click.echo(config_filepath)

        # read the config file
        config.read(config_filepath)

        # initialise sections if they don't exist already
        for section in config_sections:
            if section not in config.sections():
                config[section] = {}

        self.config = config

    def save_config(self):
        # create config directory if it doesn't exist already
        if not os.path.isdir(dirs.user_config_dir):
            try:
                os.makedirs(dirs.user_config_dir)
            except OSError:
                click.secho("Error creating directory to store config file")
                return

        with open(config_filepath, "w") as configfile:
            self.config.write(configfile)


pass_deploifai_context_obj = click.make_pass_decorator(DeploifaiContextObj, ensure=True)
