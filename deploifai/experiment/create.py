import click

from deploifai.context import (
    pass_deploifai_context_obj,
    DeploifaiContextObj,
    is_authenticated,
    project_found
)
from deploifai.api import DeploifaiAPIError
from PyInquirer import prompt
from enum import Enum


class Environment(Enum):
    DEPLOIFAI = "DEPLOIFAI"
    EXTERNAL = "EXTERNAL"


@click.command()
@click.option("--name", "-n", help="Experiment name", type=str, prompt="Choose an experiment name")
@pass_deploifai_context_obj
@is_authenticated
@project_found
def create(context: DeploifaiContextObj, name: str):
    # get project
    if "id" not in context.local_config["PROJECT"]:
        click.secho("Local configuration file missing!", fg="yellow")
        return

    project_id = context.local_config["PROJECT"]["id"]

    # query for project name and workspace from api
    fragment = """
    fragment project on Project {
        name
        account{
            username
        }
    }
    """
    project_data = context.api.get_project(
        project_id=project_id, fragment=fragment
    )

    workspace = project_data["account"]["username"]
    project_name = project_data["name"]

    can_create = context.api.can_create_experiment(workspace)

    if not can_create:
        click.secho("You are not authorized to create any experiments.", fg="red")
        raise click.Abort()

    # query for existing experiment names from api
    fragment = """
    fragment project on Project {
        experiments {
            name
        }
    }
    """
    project_data = context.api.get_project(
        project_id=project_id, fragment=fragment
    )
    experiment_names = [experiment["name"] for experiment in project_data["experiments"]]

    err_msg = ""

    is_valid_name = True

    if name in experiment_names:
        is_valid_name = False
        err_msg = f"Experiment name taken. Existing names in current project: {' '.join(experiment_names)}"
    elif name.isspace():
        is_valid_name = False
        err_msg = f"Experiment name cannot be empty."

    if not is_valid_name:
        click.secho(err_msg, fg="red")
        raise click.Abort()

    is_deploifai_environment = prompt(
        {
            "type": "confirm",
            "name": "is_deploifai_environment",
            "message": "Run experiments on a managed runner on your own cloud service",
        }
    )["is_deploifai_environment"]

    # TODO: prompt user for more info if run experiment in deploifai
    if is_deploifai_environment:
        pass
    else:
        environment = Environment.EXTERNAL
        try:
            context.api.create_experiment(name, environment, project_id)
        except DeploifaiAPIError as err:
            click.secho(err, fg="red")
            raise click.Abort()

    click.secho(f"Created new experiment {name} on project {project_name}.",fg="green")
