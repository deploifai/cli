import click
from PyInquirer import prompt
from deploifai.utilities.cloud_profile import Provider
from deploifai.context import (
    pass_deploifai_context_obj,
    DeploifaiContextObj,
    is_authenticated,
)
from deploifai.utilities.user import parse_user_profiles
from deploifai.api import DeploifaiAPIError


@click.command()
@click.option("--name", "-n", help="Cloud profile name", prompt="Choose a cloud profile name")
@click.option("--workspace", "-w", help="Workspace name", type=str)
@pass_deploifai_context_obj
@is_authenticated
def create(context: DeploifaiContextObj, name: str, workspace: str):
    """
    Create a new cloud profile
    """
    deploifai_api = context.api

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
        cloud_profiles = deploifai_api.get_cloud_profiles(workspace=command_workspace)
    except DeploifaiAPIError as err:
        click.secho(err, fg="red")
        return

    existing_names = [cloud_profile.name for cloud_profile in cloud_profiles]

    if name in existing_names:
        click.echo(click.style("Cloud profile name taken. Existing names: ", fg="red") + ' '.join(existing_names))
        raise click.Abort()

    provider = prompt(
        {
            "type": "list",
            "name": "provider",
            "message": "Choose a provider for the new cloud profile",
            "choices": [{"name": provider.value, "value": provider} for provider in Provider]
        }
    )["provider"]

    cloud_credentials = {}
    if provider == Provider.AWS:
        cloud_credentials["awsAccessKey"] = prompt(
            {
                "type": "input",
                "name": "awsAccessKey",
                "message": "AWS Access Key ID (We'll keep these secured and encrypted)",
            }
        )["awsAccessKey"]
        cloud_credentials["awsSecretAccessKey"] = prompt(
            {
                "type": "input",
                "name": "awsSecretAccessKey",
                "message": "AWS Secret Access Key (We'll keep these secured and encrypted)",
            }
        )["awsSecretAccessKey"]
    elif provider == Provider.AZURE:
        cloud_credentials["azureSubscriptionId"] = prompt(
            {
                "type": "input",
                "name": "azureSubscriptionId",
                "message": "Azure Account Subscription ID (We'll keep these secured and encrypted)",
            }
        )["azureSubscriptionId"]
        cloud_credentials["azureTenantId"] = prompt(
            {
                "type": "input",
                "name": "azureTenantId",
                "message": "Azure Active Directory Tenant ID (We'll keep these secured and encrypted)",
            }
        )["azureTenantId"]
        cloud_credentials["azureClientId"] = prompt(
            {
                "type": "input",
                "name": "azureClientId",
                "message": "Azure Client ID (We'll keep these secured and encrypted)",
            }
        )["azureClientId"]
        cloud_credentials["azureClientSecret"] = prompt(
            {
                "type": "input",
                "name": "azureClientSecret",
                "message": "Azure Client Secret / Password (We'll keep these secured and encrypted)",
            }
        )["azureClientSecret"]
    else:
        cloud_credentials["gcpProjectId"] = prompt(
            {
                "type": "input",
                "name": "gcpProjectId",
                "message": "GCP Project ID (We'll keep these secured and encrypted)",
            }
        )["gcpProjectId"]

        gcp_service_account_key_file = prompt(
            {
                "type": "input",
                "name": "gcp_service_account_key_file",
                "message": "File path for the GCP Service Account Key File (We'll keep these secured and encrypted)",
            }
        )["gcp_service_account_key_file"]

        try:
            with open(gcp_service_account_key_file) as gcp_service_account_key_json:
                cloud_credentials["gcpServiceAccountKey"] = gcp_service_account_key_json.read()
        except FileNotFoundError:
            click.secho("File not found. Please input the correct file path.", fg="red")
            raise click.Abort()

    try:
        cloud_profile_fragment = """
        fragment cloud_profile on CloudProfile {
            id
        }
        """
        _ = deploifai_api.create_cloud_profile(
            provider,
            name,
            cloud_credentials,
            command_workspace,
            cloud_profile_fragment
        )
    except DeploifaiAPIError as err:
        click.secho(err, fg="red")
        raise click.Abort()

    click.secho(f"Successfully created a new cloud profile named {name}.", fg="green")