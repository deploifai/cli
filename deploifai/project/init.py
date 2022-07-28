import click
import click_spinner
from PyInquirer import prompt
from click import Abort
import os

from deploifai.api import DeploifaiAPIError
from deploifai.context import (
    pass_deploifai_context_obj,
    DeploifaiContextObj,
    is_authenticated,
)
from deploifai.utilities.config import local_config


@click.command()
@pass_deploifai_context_obj
@is_authenticated
def init(context: DeploifaiContextObj):
    """
    Initialize current working directory as a Deploifai project
    """
    click.secho("Connecting with an existing project", fg="blue")
    deploifai_api = context.api

    command_workspace = context.global_config["WORKSPACE"]["username"]

    if context.local_config is not None:
        click.echo("Project already initialized")
        raise click.Abort()

    fragment = """
                    fragment project on Project {
                        id
                        name
                        cloudProfile{
                            provider
                            }
                    }
                    """

    try:
        with click_spinner.spinner():
            click.echo("Getting project information")
            project_info = deploifai_api.get_projects(
                workspace=command_workspace, fragment=fragment
            )
        if not len(project_info):
            click.echo("No projects in the workspace")
            raise click.Abort()
        questions = [
            {
                "type": "list",
                "name": "project_option",
                "message": "Choose a project to initialize.",
                "choices": [
                    {
                        "name": "{} <{}>".format(
                            x["name"], x["cloudProfile"]["provider"]
                        ),
                        "value": x,
                    }
                    for x in project_info
                ],
            }
        ]
        answers = prompt(questions=questions)
        if answers == {}:
            raise Abort()
        project_info = answers["project_option"]
        context.debug_msg(project_info)
        project_id = project_info["id"]
        project_name = project_info["name"]
    except DeploifaiAPIError as err:
        click.echo(err)
        raise Abort()

    local_config.create_config_files()
    context.local_config = local_config.read_config_file()
    context.debug_msg(context.local_config)

    # storing the project information on the local.cfg file
    local_config.set_project_config(project_id, context.local_config)
