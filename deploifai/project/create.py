import click

from deploifai.context import pass_deploifai_context_obj, DeploifaiContextObj
from deploifai.utilities import local_config
from deploifai.api import DeploifaiAPI, DeploifaiAPIError
from deploifai.utilities.user import parse_user_profiles
from PyInquirer import prompt


@click.command()
@click.argument("name")
@click.option("--workspace", help="Workspace name", type=str)
@pass_deploifai_context_obj
def create(context: DeploifaiContextObj, name:str, workspace):
    """
    Create a new project
    """
    if not context.is_authenticated():
        click.echo("Login using deploifai login first")
        raise click.Abort()

    # TODO: abort if project name existed

    deploifai_api = DeploifaiAPI(context=context)

    user_data = deploifai_api.get_user()
    personal_workspace, team_workspaces = parse_user_profiles(user_data)

    workspaces_from_api = [personal_workspace] + team_workspaces

    # checking validity of workspace, and prompting workspaces choices if not specified
    if workspace and len(workspace):
        if any(ws["username"] == workspace for ws in workspaces_from_api):
            for w in workspaces_from_api:
                if w["username"] == workspace:
                    command_workspace = w
                    break
        else:
            # the workspace user input does not match with any of the workspaces the user has access to
            click.secho(
                f"{workspace} cannot be found. Please put in a workspace you have access to.",
                fg="red",
            )
            raise click.Abort()
    else:
        _choose_workspace = prompt(
            {
                "type": "list",
                "name": "workspace",
                "message": "Choose a workspace",
                "choices": [
                    {"name": ws["username"], "value": ws} for ws in workspaces_from_api
                ],
            }
        )
        if _choose_workspace == {}:
            raise click.Abort()
        command_workspace = _choose_workspace["workspace"]

    try:
        cloud_profiles = deploifai_api.get_cloud_profiles(
            workspace=command_workspace
        )
    except DeploifaiAPIError as err:
        click.echo("Could not fetch cloud profiles. Please try again.")
        return

    # TODO: prompt user if no existing cloud profiles exist
    choose_cloud_profile = prompt(
        {
            "type": "list",
            "name": "cloud_profile",
            "message": "Choose a cloud profile for project",
            "choices": [
                {
                    "name": "{name}({workspace}) - {provider}".format(
                        name=cloud_profile.name,
                        workspace=cloud_profile.workspace,
                        provider=cloud_profile.provider,
                    ),
                    "value": cloud_profile,
                }
                for cloud_profile in cloud_profiles
            ],
        }
    )

    cloud_profile = choose_cloud_profile["cloud_profile"]

    project_id = deploifai_api.create_project(name, cloud_profile)

    local_config.set_project_config(project_id, context.local_config)
