import click
from deploifai.context import (
    pass_deploifai_context_obj,
    DeploifaiContextObj,
    is_authenticated,
)
from deploifai.utilities.user import parse_user_profiles


@click.command('set')
@click.argument("workspace")
@pass_deploifai_context_obj
@is_authenticated
def set_workspace(context: DeploifaiContextObj, workspace: str):
    """
    Changes current workspace
    """
    deploifai_api = context.api

    user_data = deploifai_api.get_user()
    personal_workspace, team_workspaces = parse_user_profiles(user_data)

    workspaces_from_api = [personal_workspace] + team_workspaces

    # checking validity of workspace, and prompting workspaces choices if not specified
    if workspace and len(workspace):
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

    current_workspace = context.global_config["WORKSPACE"]["username"]

    if current_workspace == command_workspace["username"]:
        click.secho(f"Already in the workspace {current_workspace}", fg="yellow")
        raise click.Abort()

    context.global_config["WORKSPACE"]["username"] = command_workspace["username"]

    context.save_config()

    click.secho(f"Successfully switched to {command_workspace['username']}", fg="green")