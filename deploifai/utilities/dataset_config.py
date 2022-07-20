import configparser
import pathlib
import click

"""
Manages a .dataset.cfg file to store configuration info about a project.

config dictionary structure:
{
    "DATA_STORAGE": {"id": string}
}
"""

config_file_path = pathlib.Path().joinpath("dataset.cfg")

config_sections = ["DATA_STORAGE"]


class DeploifaiDataAlreadyInitialisedError(Exception):
    """
    Exception when a data directory has been initialised through Deploifai in an ML project.
    """

    def __init__(self, message):
        super(DeploifaiDataAlreadyInitialisedError, self).__init__(message)


def create_config_files():
    """
    Creates the folder .deploifai that stores all the config files.
    :return: None
    """
    global config_file_path
    dataset_config_dir = pathlib.Path()
    dataset_config_dir.mkdir(exist_ok=True)

    config_file_path = dataset_config_dir.joinpath("dataset.cfg")

    config_file_path.touch(exist_ok=False)

    # initialise sections if they don't exist already
    config = configparser.ConfigParser()

    with config_file_path.open("w") as config_file:
        config.write(config_file)


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
            and "DATA_STORAGE" in config
            and "id" in config["DATA_STORAGE"]
    ):
        raise DeploifaiDataAlreadyInitialisedError(
            "This project already has a data storage attached to it."
        )

    elif (
            config is not None
            and "DATA_STORAGE" in config
    ):

        config["DATA_STORAGE"] = {"id": data_storage_id}

    else:
        print("DATA_STORAGE missing from deploifai.cfg")
        return

    save_config_file(config)
