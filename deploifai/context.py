import functools
import os
import click
import configparser
import requests
from click import pass_context

from .api import DeploifaiAPI
from .utilities import environment, local_config

from deploifai.utilities.credentials import get_auth_token

APP_NAME = "deploifai-cli"

global_config_filename = "deploifai.cfg"
global_config_directory = (
    click.get_app_dir(APP_NAME)
    if not environment.is_development_env
    else os.path.dirname(os.path.realpath(__file__))
)
global_config_filepath = os.path.join(global_config_directory, global_config_filename)
global_config_sections = ["AUTH"]

debug_levels = ["info", "warning", "error"]


class DeploifaiContextObj:
    global_config = configparser.ConfigParser()
    local_config = configparser.ConfigParser()
    debug = False
    debug_level = "info"
    api: DeploifaiAPI = None

    def __init__(self):
        pass

    def read_config(self):
        global_config = configparser.ConfigParser()

        # read the global config file
        global_config.read(global_config_filepath)

        # initialise sections if they don't exist already
        for section in global_config_sections:
            if section not in global_config.sections():
                global_config[section] = {}

        self.debug_msg(f"Read global config file from {global_config_filepath}")

        self.global_config = global_config

        # read local config file
        self.local_config = local_config.read_config_file()

    def save_config(self):
        # create global config directory if it doesn't exist already
        if not os.path.isdir(global_config_directory):
            try:
                os.makedirs(global_config_directory)
                self.debug_msg("Created directory to save global config")
            except OSError:
                self.debug_msg(
                    "Error creating directory to store global config file",
                    level="error",
                )
                return

        with open(global_config_filepath, "w") as configfile:
            self.global_config.write(configfile)
            self.debug_msg(f"Saved global config file as {global_config_filepath}")

        # save local config file
        local_config.save_config_file(self.local_config)

    def initialise_api(self):
        if "username" in self.global_config["AUTH"]:
            token = get_auth_token(self.global_config["AUTH"]["username"])
            self.api = DeploifaiAPI(token)
        else:
            self.api = DeploifaiAPI()

    def debug_msg(self, message, level="info", **kwargs):
        if self.debug:
            debug_level_index = debug_levels.index(self.debug_level)
            message_level_index = debug_levels.index(level)

            # only log debug messages if the message level index is higher than the debug level index
            if message_level_index >= debug_level_index:
                fg = "blue"
                if level == "warning":
                    fg = "yellow"
                elif level == "error":
                    fg = "red"

                kwargs.update({"fg": kwargs["fg"] if "fg" in kwargs else fg})

                click.secho(message, **kwargs)

    def is_authenticated(self):
        if "username" not in self.global_config["AUTH"]:
            return False
        username = self.global_config["AUTH"]["username"]

        url = f"{environment.backend_url}/auth/check/cli"
        token = get_auth_token(username)

        response = requests.post(
            url,
            json={"username": username},
            headers={"authorization": token},
        )

        if response.status_code == 200:
            return True
        return False


pass_deploifai_context_obj = click.make_pass_decorator(DeploifaiContextObj, ensure=True)


def is_authenticated(f):
    @pass_context
    def wrapper(click_context, *args, **kwargs):
        deploifai_context = click_context.find_object(DeploifaiContextObj)

        if "username" in deploifai_context.global_config["AUTH"]:
            username = deploifai_context.global_config["AUTH"]["username"]

            url = f"{environment.backend_url}/auth/check/cli"
            token = get_auth_token(username)

            response = requests.post(
                url,
                json={"username": username},
                headers={"authorization": token},
            )

            if response.status_code == 200:
                return click_context.invoke(f, *args, **kwargs)

        click.echo(
            click.style("Auth Missing: you need to login using ", fg="red")
            + click.style("deploifai auth login", fg="blue")
        )
        raise click.Abort()

    return functools.update_wrapper(wrapper, f)
