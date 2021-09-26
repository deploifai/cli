import os
import sys
import click
import subprocess
import click_spinner
from PyInquirer import prompt
from dvc.main import main as dvc
from deploifai.api import DeploifaiAPIError, DeploifaiAPI
from deploifai.context_obj import pass_deploifai_context_obj, DeploifaiContextObj


@click.command()
@pass_deploifai_context_obj
def init(context: DeploifaiContextObj):
  """
  Initialise the current directory as a dataset
  """
  result = dvc(['init'])
  if result == 1:
    # The repo is not tracked using Git
    click.clear()
    click.echo("You might wanna init this directory as a Git repo first.")
    return
  try:
    deploifai_api = DeploifaiAPI(context=context)
    click.echo("Successfully initialised DVC repo. (Check https://dvc.org for more info)")
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
    }]

    answers = prompt(questions=questions)

    if answers["storage_option"] == "New":
      pass

    try:
      os.mkdir("data")
    except FileExistsError as err:
      click.echo("The data directory already exists, not going to create")

    click.echo("Adding remote storage to DVC")

    # TODO: Change this storage URL to have the actual URL from the data storage
    storage_url = "s3://mybucket/dvcstore"
    dvc(["remote", "add", "-d", "storage", storage_url])

    click.echo("Setting up the git repo...")
    subprocess.run(['git', 'add', 'data/.gitignore', '.dvc/config'])
    subprocess.run(['git', 'commit', '-m', 'Initialise dataset repo'])
    click.echo("Add files to the data directory, and run \"deploifai data upload\"")
  except DeploifaiAPIError as err:
    click.echo(err)
    return
