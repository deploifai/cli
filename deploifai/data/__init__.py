import click
from deploifai.data.init import init
from deploifai.data.info import info
from deploifai.data.push import push


@click.group()
def data():
    """
    Manage datasets and data storages on Deploifai
    """
    pass


data.add_command(init)
data.add_command(push)
data.add_command(info)
