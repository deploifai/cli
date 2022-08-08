import click
from deploifai.dataset.init import init
from deploifai.dataset.info import info
from deploifai.dataset.push import push
from deploifai.dataset.create import create
from deploifai.dataset.list import list_data
from deploifai.dataset.pull import pull


@click.group()
def dataset():
    """
    Manage datasets and dataset storages on Deploifai
    """
    pass


dataset.add_command(init)
dataset.add_command(push)
dataset.add_command(pull)
dataset.add_command(info)
dataset.add_command(create)
dataset.add_command(list_data)
