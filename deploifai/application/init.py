import os
import io
import zipfile
import click
import requests

from deploifai.context import pass_deploifai_context_obj, DeploifaiContextObj

# TODO: figure out how to make this usable
# This clones the deploifai/basic-starter-template which is intended for ML deployments
@click.command()
@pass_deploifai_context_obj
@click.argument("name")
def init(deploifai: DeploifaiContextObj, name: str):
    """
    Initialise a new project called NAME
    """
    url = "https://api.github.com/repos/deploifai/basic-starter-template/zipball/main"
    r = requests.get(url)

    with zipfile.ZipFile(io.BytesIO(r.content)) as zip_ref:
        # create a new project directory
        directory = os.path.join(os.getcwd(), name)
        if not os.path.isdir(directory):
            try:
                os.makedirs(directory)
                deploifai.debug_msg("Created new project directory")
            except OSError:
                deploifai.debug_msg("Error creating project directory", level="error")
                return

        deploifai.debug_msg(f"Zip file namelist: {zip_ref.namelist()}")

        files_list = zip_ref.namelist()[1:]

        for file in files_list:
            filepath = directory + "/" + "/".join(file.split("/")[1:])
            deploifai.debug_msg(f"Write to {filepath}")
            with open(filepath, "wb") as new_file:
                new_file.write(zip_ref.read(file))

        deploifai.debug_msg(f"Extracted zip file contents to {directory}")

    click.echo(f"Created a new project called {name}")
