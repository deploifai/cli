import click

from deploifai.api import DeploifaiAPIError
from deploifai.context import (
    pass_deploifai_context_obj,
    DeploifaiContextObj,
    is_authenticated, project_found,
)


@click.command()
@pass_deploifai_context_obj
@is_authenticated
@project_found
def info(context: DeploifaiContextObj):
    """
    Get information about a project
    """

    project_id = context.local_config["PROJECT"]["id"]

    fragment = """
                fragment project on Project {
                    name status
                    account{
                        username
                    }
                    cloudProfile{
                        provider
                    }
                    experiments{
                        name status environment
                    }
                    dataStorages{
                        name status
                    }
                    trainings{
                        name status state
                    }
                    applications{
                        applicationName
                    }
                }
                """
    project_data = context.api.get_project(project_id=project_id, fragment=fragment)

    click.secho("Workspace Name: {}".format(project_data["account"]["username"]), fg="blue")

    click.secho("Project Name: {}".format(project_data["name"]), fg="blue")

    click.secho("Cloud Provider: {}".format(project_data["cloudProfile"]["provider"]))

    click.echo("Experiments:")
    for experiment in project_data["experiments"]:
        click.echo("{} <{}> - {}".format(experiment["name"], experiment["status"], experiment["environment"]))

    click.echo("Datasets:")
    for dataset in project_data["dataStorages"]:
        click.echo("{} <{}>".format(dataset["name"], dataset["status"]))

    click.echo("Training Servers:")
    for server in project_data["trainings"]:
        click.echo("{} <{}> - {}".format(server["name"], server["status"], server["state"]))

    click.echo("Deployments:")
    for application in project_data["applications"]:
        click.echo("{}".format(application["applicationName"]))
