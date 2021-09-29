import os
import click
import subprocess
import click_spinner
from PyInquirer import prompt
from dvc.main import main as dvc
from deploifai.api import DeploifaiAPIError, DeploifaiAPI
from deploifai.context_obj import pass_deploifai_context_obj, DeploifaiContextObj
from deploifai.utilities.config import add_storage_configs, DeploifaiDataAlreadyInitialisedError


@click.command()
@pass_deploifai_context_obj
def init(context: DeploifaiContextObj):
  """
  Initialise the current directory as a dataset
  """
  try:
    deploifai_api = DeploifaiAPI(context=context)
    with click_spinner.spinner():
      click.echo("Getting account information")
      personal_storages, teams_storages = deploifai_api.get_data_storages()

    questions = [{
      'type': 'list',
      'name': 'storage_option',
      'message': 'Choose the dataset storage to link.',
      'choices': [
       {
         'name': "Crete new data storage",
         'value': "New"
       }] + [
       {
         'name': "{}({})".format(x["name"], x["account"]["username"]),
         'value': x['id']
       } for x in (personal_storages + teams_storages)]
    }, {
      'type': 'list',
      'name': 'container',
      'message': 'Choose the container in the data storage.',
      'choices': lambda ans: deploifai_api.get_containers(ans),
      'when': lambda ans: ans.get('storage_option') != "New"
    }, {
      'type': 'confirm',
      'name': 'VCS',
      'message': 'Use DVC?',
      'default': False
    }]
  except DeploifaiAPIError as err:
    click.echo(err)
    return

  answers = prompt(questions=questions)
  storage_id = answers.get("storage_option", "")
  container_name = answers.get("container")

  if answers["storage_option"] == "New":
    pass

  try:
    os.mkdir("data")
    click.echo("Creating the data directory. If your data is outside the data directory, move it into the the data "
               "directory so that it can be uploaded")
  except FileExistsError as err:
    click.echo("Using the data directory")

  # TODO: Change this storage URL to have the actual URL from the data storage
  storage_url = "s3://mybucket/dvcstore"

  try:
    add_storage_configs(storage_id, container_name, context)
  except DeploifaiDataAlreadyInitialisedError:
    click.echo("""
    A different storage is already initialised in the folder.
    Consider removing it from the config file.
    """)

  if answers["VCS"]:
    result = dvc(["init"])
    if result == 1:
      # This means that the SCM has not been initialised. So just do it for the user.
      click.echo("We will just initialise git for you.")
      subprocess.run(['git', 'init'])
      dvc(["init"])
    dvc(["remote", "add", "-d", "storage", storage_url])
    click.echo("Successfully initialised DVC repo. (Check https://dvc.org for more info)")
    click.echo("Setting up the git repo with DVC...")
    subprocess.run(['git', 'add', 'data/.gitignore', '.dvc/config'])
    subprocess.run(['git', 'commit', '-m', 'Initialise dataset repo'])
    click.echo("Add files to the data directory, and run \"deploifai data upload\"")
