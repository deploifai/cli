import click
from PyInquirer import prompt

from deploifai.api import DeploifaiAPIError
from deploifai.context import pass_deploifai_context_obj, DeploifaiContextObj, is_authenticated, project_found


@click.command()
@pass_deploifai_context_obj
@is_authenticated
@project_found
def start(context: DeploifaiContextObj, project: str):
    """
        Command to start the training server
    """

    current_workspace = context.global_config["WORKSPACE"]["username"]

    click.secho("Workspace Name: {}".format(current_workspace), fg="blue")

    project_id = context.local_config["PROJECT"]["id"]
    where_project = {"id": {"equals": project_id}}

    fragment = """
                fragment project on Project {
                trainings{
                        id name status state
                    }
                }
                """
    projects_data = context.api.get_projects(workspace=current_workspace, where_project=where_project, fragment=fragment)

    server_info = projects_data[0]["trainings"]

    choose_server = prompt(
        {
            "type": "list",
            "name": "training server",
            "message": "Choose a training server",
            "choices": [
                {
                    "name": "{} <{}> - {}".format(info["name"], info["status"], info["state"]),
                    "value": info
                }
                for info in projects_data
            ],
        }
    )
    if choose_server == {}:
        raise click.Abort()
    server = choose_server["training server"]

    server_name = server["name"]
    server_status = server["status"]
    server_state = server["state"]

    if server_status != "DEPLOY_SUCCESS":
        click.secho("Cannot start training server, since server status is {}.".format(server_status), fr="red")
        raise click.Abort()

    if server_state != "SLEEPING":
        click.secho("Cannot start training server, since server state is {}.".format(server_state), fr="red")
        raise click.Abort()

    
