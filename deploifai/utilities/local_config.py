import configparser
import pathlib
import click


def _find_local_config_dir():
    """
    Traverse up the file system and checks for a .deploifai directory.
    If does not exist, raise error not found.
    :return: if local config file exists, return pathlib.Path object that points to the config file
    """
    path = pathlib.Path.cwd()
    while not path.joinpath(".deploifai").exists() and path != path.parent:
        path = path.parent

    if path == path.parent:
        raise DeploifaiNotInitialisedError("Deploifai project not found.")

    return path.joinpath(".deploifai", "local.cfg")


config_file_path = _find_local_config_dir()

"""
Manages a .deploifai/local.cfg file to store configuration info about a project.

The .deploifai directory lives in the root directory of the project. The user should be encouraged to version control this directory.

config dictionary structure:
{
    "PROJECT": {"id": string},
    "DATA_STORAGE": {"id": string}
}
"""

config_sections = ["PROJECT", "DATA_STORAGE"]


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
        super(DeploifaiNotInitialisedError, self).__init__(message)


def create_config_files(new_project_dir: str):
    """
    Creates the folder .deploifai that stores all the config files.
    :return: None
    """
    if config_file_path.parent.exists():
        raise DeploifaiAlreadyInitialisedError(
            "Deploifai has already been initialised in this directory."
        )

    pathlib.Path(new_project_dir).join
    pathlib.Path(".deploifai").mkdir()
    config_file_path.touch(exist_ok=True)

    # initialise sections if they don't exist already
    config = configparser.ConfigParser()

    with config_file_path.open("w") as config_file:
        config.write(config_file)

    click.secho(
        """A .deploifai directory has been created, which contains configuration that Deploifai requires.
        You should version control this directory.
        """,
        fg="blue",
    )


def read_config_file() -> configparser.ConfigParser:
    """
    Read the config file in the existing .deploifai/local.cfg file
    :return: A ConfigParser that contains all the configs in the config file
    """
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
    if "id" in config["DATA_STORAGE"] and len(config["DATA_STORAGE"]["id"]) > 0:
        raise DeploifaiDataAlreadyInitialisedError(
            "This project already has a data storage attached to it."
        )

    config["DATA_STORAGE"] = {"id": data_storage_id}

    save_config_file(config)
