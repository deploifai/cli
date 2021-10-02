import click

from deploifai.context_obj import pass_deploifai_context_obj, DeploifaiContextObj
from deploifai.utilities.config import read_config_file


@click.command()
@pass_deploifai_context_obj
def info(context: DeploifaiContextObj):
  try:
    configs = read_config_file()
  except FileNotFoundError:
    return
  datastorage_config = configs['datastorage']
  storage_account_id = datastorage_config.get("id")
  storage_account_name = datastorage_config.get("storage")
  container_name = datastorage_config.get("container")
  cloud_provider = datastorage_config.get("provider")

  if cloud_provider == "AZURE":
    click.secho("Deploifai Storage ID: {}".format(storage_account_id), fg="green")
    click.secho("https://deploif.ai/dashboard/{username}/data-storages/{storage_account_id}\n".format(
      username=context.config["AUTH"]["username"],
      storage_account_id=storage_account_id
    ), underline=True, fg="green")
    click.secho("Azure Storage Account", bold=True, fg="blue", underline=True)
    click.secho("Storage Account Name: {}".format(storage_account_name), fg="blue")
    click.secho("Container Name: {}".format(container_name), fg="blue")
    click.secho("\nYou could use the Azure CLI to list all the blobs in your container on Azure:", underline=True)
    click.secho("az storage blob list -c {container_name} --account-name {storage_account_name}".format(
      storage_account_name=storage_account_name,
      container_name=container_name
    ), fg="yellow")

  else:
    click.secho("AWS data storages CLI support is coming soon.", fg="green")
