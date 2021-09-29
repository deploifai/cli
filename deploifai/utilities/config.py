import yaml
import pathlib

from deploifai.api import DeploifaiAPI

config_file_path = pathlib.Path(".deploifai").joinpath("config.yml")


class DeploifaiAleardyInitialisedError(Exception):
  """
  Exception when API calls result in an error.
  """

  def __init__(self, message):
    super(DeploifaiAleardyInitialisedError, self).__init__(message)


class DeploifaiDataAlreadyInitialisedError(Exception):
  """
  Exception when API calls result in an error.
  """

  def __init__(self, message):
    super(DeploifaiDataAlreadyInitialisedError, self).__init__(message)


def create_config_files():
  """
  Creates the folder .deploifai that stores all the config files.
  :return: None
  """
  if pathlib.Path(".deploifai").exists():
    raise DeploifaiAleardyInitialisedError("Deploifai has already been initialised in this directory.")

  pathlib.Path(".deploifai").mkdir()
  config_file_path.touch(exist_ok=True)


def read_config_file():
  """
  Read the config file in the existing .deploifai/config.yml file
  :return: A dictionary that contains all the configs in the config file
  """
  with config_file_path.open('r') as config_file:
    yaml_config_dict = yaml.load(config_file)
  return yaml_config_dict


def add_storage_configs(storage_id, container, context):
  """
  Add the storage configs in the existing config file. Usually run when the user initialises the directory as a data
  directory.
  :param context:
  :param container:
  :param storage_id: The id of the data storage from the database.
  :param storage_url: The storage URL for the storage.
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
    data_storage_config["container"] = container
  elif cloud_provider == "AWS":
    pass

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
