import click


@click.group()
def cli():
    pass


@cli.command()
def init():
    click.echo("Going to put init stuff here!")


@cli.command()
def login():
    click.echo("Going to put login stuff here!")
