import os
import click
import configparser

cli_environment = os.environ.get("DEPLOIFAI_CLI_ENVIRONMENT", "production")
is_cli_env_dev = cli_environment == "development"

APP_NAME = "deploifai-cli"

config_filename = "deploifai.cfg"

config_directory = (
    click.get_app_dir(APP_NAME)
    if not is_cli_env_dev
    else os.path.dirname(os.path.realpath(__file__))
)
config_filepath = os.path.join(config_directory, config_filename)

config_sections = ["AUTH", "ACCOUNT"]

debug_levels = ["info", "warning", "error"]


class DeploifaiContextObj:
    cli_environment = cli_environment
    is_cli_env_dev = is_cli_env_dev
    config = configparser.ConfigParser()
    debug = False
    debug_level = "info"

    def __init__(self):
        pass

    def read_config(self):
        config = configparser.ConfigParser()

        # read the config file
        config.read(config_filepath)

        # initialise sections if they don't exist already
        for section in config_sections:
            if section not in config.sections():
                config[section] = {}

        self.debug_msg(f"Read config file from {config_filepath}")

        self.config = config

    def save_config(self):
        # create config directory if it doesn't exist already
        if not os.path.isdir(config_directory):
            try:
                os.makedirs(config_directory)
                self.debug_msg("Created directory to save config")
            except OSError:
                self.debug_msg(
                    "Error creating directory to store config file", level="error"
                )
                return

        with open(config_filepath, "w") as configfile:
            self.config.write(configfile)
            self.debug_msg(f"Saved config file as {config_filepath}")

    def debug_msg(self, message, level="info", **kwargs):
        if self.debug:
            debug_level_index = debug_levels.index(self.debug_level)
            message_level_index = debug_levels.index(level)

            # only log debug messages if the message level index is higher than the debug level index
            if message_level_index >= debug_level_index:
                fg = "blue"
                if level is "warning":
                    fg = "yellow"
                elif level is "error":
                    fg = "red"

                kwargs.update({"fg": kwargs["fg"] if "fg" in kwargs else fg})

                click.secho(message, **kwargs)


pass_deploifai_context_obj = click.make_pass_decorator(DeploifaiContextObj, ensure=True)
