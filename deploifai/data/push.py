import click
from pathlib import Path

from deploifai.api import DeploifaiAPI
from deploifai.clouds.azure import Azure
from deploifai.context_obj import DeploifaiContextObj, pass_deploifai_context_obj
from deploifai.utilities.config import read_config_file


@click.command()
@pass_deploifai_context_obj
def push(context: DeploifaiContextObj):
  try:
    configs = read_config_file()
  except FileNotFoundError:
    return
  datastorage_config = configs['datastorage']
  if datastorage_config.get("provider") == "AZURE":
    azure_tools = Azure(context)
    storage_account_id = datastorage_config.get("id")
    storage_account_name = datastorage_config.get("storage")
    container_name = datastorage_config.get("container")
    azure_tools.upload_dataset(storage_account_id, storage_account_name, container_name, Path("data"))
  elif datastorage_config.get("provider") == "AWS":
    click.secho("Support for AWS is coming soon.", fg="red")
  else:
    click.secho("Provider is not supported. Consider resetting your configurations.", fg="red")
