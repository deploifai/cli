import click


@click.command()
def logout():
    """
    Logout as a Deploifai user
    """
    click.echo("should logout!")
