import click
from deploifai.data.init import init


@click.group()
def data():
  """
  Manage datasets and data storages on Deploifai
  """
  pass


data.add_command(init)