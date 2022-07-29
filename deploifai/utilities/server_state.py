import click
from PyInquirer import prompt

from deploifai.api import DeploifaiAPIError
from deploifai.context import pass_deploifai_context_obj, DeploifaiContextObj


@pass_deploifai_context_obj
def change_state(context: DeploifaiContextObj, command: str, ):

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

    context.debug_msg(server_info)

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
                for info in server_info
            ],
        }
    )
    if choose_server == {}:
        raise click.Abort()
    server = choose_server["training server"]

    server_id = server["id"]
    print(server_id)
    server_name = server["name"]
    server_status = server["status"]
    server_state = server["state"]

    if command == "start":

        if server_status != "DEPLOY_SUCCESS":
            click.secho("Cannot start training server, since server status is {}.".format(server_status), fg="red")
            raise click.Abort()

        if server_state != "SLEEPING":
            click.secho("Cannot start training server, since server state is {}.".format(server_state), fg="red")
            raise click.Abort()

        server_info = context.api.start_training_server(server_id=server_id)

    elif command == "stop":

        if server_status != "DEPLOY_SUCCESS":
            click.secho("Cannot stop training server, since server status is {}.".format(server_status), fg="red")
            raise click.Abort()

        if server_state != "RUNNING":
            click.secho("Cannot stop training server, since server state is {}.".format(server_state), fg="red")
            raise click.Abort()

        server_info = context.api.stop_training_server(server_id=server_id)

    click.secho("Server Name: {}".format(server_name), fg="blue")

    click.secho("Server State: {}".format(server_info["state"]), fg="blue")