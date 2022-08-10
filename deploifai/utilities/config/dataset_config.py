import configparser
import pathlib
import click

from deploifai.utilities.config.find_config_filepath import find_config_absolute_path

"""
Manages a .dataset.cfg file to store configuration info about a project.

config dictionary structure:
{
    "DATASET": {"id": string}
}
"""

relative_config_filepath = pathlib.Path("dataset.cfg")

config_file_path = find_config_absolute_path(relative_config_filepath)

config_sections = ["DATASET"]


class DeploifaiDataAlreadyInitialisedError(Exception):
    """
    Exception when a data directory has been initialised through Deploifai in an ML project.
    """

    def __init__(self, message):
        super(DeploifaiDataAlreadyInitialisedError, self).__init__(message)


class DatasetNotInitialisedError(Exception):
    """
    Exception when dataset config is not found.
    """

    def __init__(self, message):
        super(DatasetNotInitialisedError, self).__init__(message)


def create_config_files(new_dataset_dir: str = None):
    """
    Creates the .dataset config files.
    :return: None
    """
    global config_file_path

    if new_dataset_dir is None:
        dataset_config_dir = pathlib.Path()
    else:
        dataset_config_dir = pathlib.Path(new_dataset_dir)

    config_file_path = dataset_config_dir.joinpath("dataset.cfg")

    config_file_path.touch(exist_ok=False)

    config = configparser.ConfigParser()

    with config_file_path.open("w") as config_file:
        config.write(config_file)


def read_config_file() -> configparser.ConfigParser:
    """
    Read the dataset.cfg file
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
        click.secho("Missing .dataset.cfg file", fg="red")
        raise err


def save_config_file(config: configparser.ConfigParser):
    """
    Save the dataset config from the context in the dataset.cfg file.
    :param config: A ConfigParser object representing config data
    """
    with config_file_path.open("w") as config_file:
        config.write(config_file)


def find_config_directory() -> pathlib.Path:
    """
    Find the absolute path to the directory that contains the dataset.cfg file
    """
    return config_file_path.parent


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
