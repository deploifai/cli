import configparser
import pathlib
import click

from deploifai.utilities.config.find_config_filepath import find_config_absolute_path

relative_config_filepath = pathlib.Path(".deploifai/local.cfg")

config_file_path = find_config_absolute_path(relative_config_filepath)

"""
Manages a .deploifai/local.cfg file to store configuration info about a project.

The .deploifai directory lives in the root directory of the project. The user should be encouraged to version control this directory.

config dictionary structure:
{
    "PROJECT": {"id": string},
    "DATA_STORAGE": {"id": string}
}
"""

config_sections = ["PROJECT", "DATASET"]


class DeploifaiAlreadyInitialisedError(Exception):
    """
    Exception when Deploifai has already been initialised.
    """

    def __init__(self, message):
        super(DeploifaiAlreadyInitialisedError, self).__init__(message)


class DeploifaiDataAlreadyInitialisedError(Exception):
    """
    Exception when a data directory has been initialised through Deploifai in an ML project.
    """

    def __init__(self, message):
        super(DeploifaiDataAlreadyInitialisedError, self).__init__(message)


class DeploifaiNotInitialisedError(Exception):
    """
    Exception when Deploifai project is not found.
    """

    def __init__(self, message):
        click.echo(click.style("Project not found. To create a project: ", fg="red") +
                   click.style("deploifai project create NAME", fg="blue")
                   )
        super(DeploifaiNotInitialisedError, self).__init__(message)


def create_config_files(new_project_dir: str = None):
    global config_file_path
    """
    Creates the folder .deploifai that stores all the config files.
    :return: None
    """
    if new_project_dir is None:
        local_config_dir = pathlib.Path().joinpath(".deploifai")
    else:
        local_config_dir = pathlib.Path(new_project_dir).joinpath(".deploifai")
    local_config_dir.mkdir(exist_ok=False)

    config_file_path = local_config_dir.joinpath("local.cfg")

    config_file_path.touch(exist_ok=True)

    config = configparser.ConfigParser()

    with config_file_path.open("w") as config_file:
        config.write(config_file)

    click.secho(
        """A .deploifai directory has been created, which contains configuration that Deploifai requires.
            You should version control this directory.""",
        fg="blue",
    )


def read_config_file() -> configparser.ConfigParser:
    """
    Read the config file in the existing .deploifai/local.cfg file
    :return: A ConfigParser that contains all the configs in the config file
    """
    if config_file_path is None:
        return None

    try:
        config = configparser.ConfigParser()
        # read the config file
        config.read(config_file_path)

        for section in config_sections:
            if section not in config.sections():
                config[section] = {}

        return config
    except FileNotFoundError as err:
        click.secho("Missing .deploifai/local.cfg file", fg="red")
        raise err


def save_config_file(config: configparser.ConfigParser):
    """
    Save the local config from the context in the local.cfg file.
    :param config: A ConfigParser object representing config data
    """
    with config_file_path.open("w") as config_file:
        config.write(config_file)


def set_project_config(project_id: str, config: configparser.ConfigParser):
    """
    Set the project config into the existing config file.
    :param project_id: The id of the project from the database.
    :param config: The current config
    :return:
    """
    config["PROJECT"] = {"id": project_id}

    save_config_file(config)


def add_data_storage_config(data_storage_id: str, config: configparser.ConfigParser):
    """
    Add the storage configs in the existing config file. Usually run when the user initialises the directory as a data
    directory.
    :param data_storage_id: The id of the data storage from the database.
    :param config: The current config
    :return:
    """
    if (
            config is not None
            and "DATASET" in config
            and "id" in config["DATASET"]
            and len(config["DATASET"]["id"]) != 0
    ):
        raise DeploifaiDataAlreadyInitialisedError(
            "This project already has a dataset attached to it."
        )

    elif (
            config is not None
            and "DATASET" in config
    ):

        config["DATASET"] = {"id": data_storage_id}

    save_config_file(config)
