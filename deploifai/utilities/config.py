import yaml
from yaml import Loader
import pathlib
import click
from deploifai.api import DeploifaiAPI

config_file_path = pathlib.Path(".deploifai").joinpath("config.yml")


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


def create_config_files():
  """
  Creates the folder .deploifai that stores all the config files.
  :return: None
  """
  if pathlib.Path(".deploifai").exists():
    raise DeploifaiAlreadyInitialisedError("Deploifai has already been initialised in this directory.")

  pathlib.Path(".deploifai").mkdir()
  config_file_path.touch(exist_ok=True)


def read_config_file():
  """
  Read the config file in the existing .deploifai/config.yml file
  :return: A dictionary that contains all the configs in the config file
  """
  try:
    with config_file_path.open('r') as config_file:
      yaml_config_dict = yaml.load(config_file, Loader=Loader)
    return yaml_config_dict
  except FileNotFoundError as err:
    click.secho("Initialise the Deploifai data storage first.", fg="red")
    click.secho("deploifai data init", bold=True, fg="red")
    raise err


def add_storage_configs(storage_id, containers, context):
  """
  Add the storage configs in the existing config file. Usually run when the user initialises the directory as a data
  directory.
  :param context:
  :param containers:
  :param storage_id: The id of the data storage from the database.
  :return:
  """
  deploifai_api = DeploifaiAPI(context=context)
  storage_details = deploifai_api.get_data_storage_info(storage_id)

  cloud_provider = storage_details["cloudProviderYodaConfig"]["provider"]
  data_storage_config = {
    "id": storage_id,
    "provider": cloud_provider
  }
  if cloud_provider == "AZURE":
    data_storage_config["storage"] = storage_details["cloudProviderYodaConfig"]["azureConfig"]["storageAccount"]
    data_storage_config["containers"] = list(containers)
  elif cloud_provider == "AWS":
    data_storage_config["containers"] = list(containers)

  if not config_file_path.exists():
    create_config_files()
  yaml_config_dict = read_config_file()
  if yaml_config_dict is not None:
    if yaml_config_dict.get("datastorage"):
      raise DeploifaiDataAlreadyInitialisedError("This folder already has a storage attached to it.")
  else:
    yaml_config_dict = {}

  yaml_config_dict["datastorage"] = data_storage_config
  with pathlib.Path(".deploifai").joinpath("config.yml").open('w') as config_file:
    yaml.dump(yaml_config_dict, config_file)
