import click

from deploifai.context import (
    pass_deploifai_context_obj,
    DeploifaiContextObj,
    is_authenticated,
)
from deploifai.utilities import local_config
from deploifai.api import DeploifaiAPIError
from deploifai.utilities.user import parse_user_profiles
from PyInquirer import prompt


@click.command()
@click.option("--name", "-n", help="Experiment name", type=str, required=True)
@pass_deploifai_context_obj
@is_authenticated
def create(context: DeploifaiContextObj, name: str):
    # get project
    if "id" not in context.local_config["PROJECT"]:
        click.secho("Local configuration file missing!", fg="yellow")
        click.echo(click.style("Create a project first by doing ", fg="yellow") + click.style("deploifai project create", fg="blue"))
        return

    project_id = context.local_config["PROJECT"]["id"]

    # query for project and workspace name from api
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

    # query for project and workspace name from api
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

    name_taken_err_msg = f"Experiment name taken. Existing names in current project: {' '.join(experiment_names)}\nChoose a unique experiment name:"
    err_msg = name_taken_err_msg

    is_valid_name = not (name in experiment_names)

    while not is_valid_name:
        prompt_name = prompt(
            {
                "type": "input",
                "name": "experiment_name",
                "message": err_msg,
            }
        )

        new_experiment_name = prompt_name["experiment_name"]

        if len(new_experiment_name) == 0 or new_experiment_name.isspace():
            err_msg = "Experiment name cannot be empty.\nChoose a non-empty Experiment name:"
        elif new_experiment_name in experiment_names:
            err_msg = name_taken_err_msg
        else:
            name = new_experiment_name
            is_valid_name = True

    click.secho(f"Created new experiment {name} on project {project_name}.",fg="green")
