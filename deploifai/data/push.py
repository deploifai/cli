import click
from pathlib import Path
from deploifai.clouds.azure import AzureTools
from deploifai.utilities.config import read_config_file


@click.command()
def push():
  configs = read_config_file()
  datastorage_config = configs['datastorage']
  if datastorage_config.get("provider") == "AZURE":
    azure_tools = AzureTools()
    storage_account_name = datastorage_config.get("storage")
    container_name = datastorage_config.get("container")
    azure_tools.upload_dataset(storage_account_name, container_name, Path("data"))
  else:
    pass
