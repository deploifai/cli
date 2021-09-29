import click
from deploifai.data.init import init
from .push import push


@click.group()
def data():
  """
  Manage datasets and data storages on Deploifai
  """
  pass


data.add_command(init)
data.add_command(push)
