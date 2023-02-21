import click
import boto3
from botocore.exceptions import ClientError
from PyInquirer import prompt
from deploifai.utilities.cloud_profile import Provider
from deploifai.context import (
    pass_deploifai_context_obj,
    DeploifaiContextObj,
    is_authenticated,
)
from deploifai.api import DeploifaiAPIError


@click.command()
@click.argument("name")
@click.option(
    "-p",
    "--provider",
    type=click.Choice([p.value for p in Provider]),
    help="Provider for the new cloud profile"
)
@pass_deploifai_context_obj
@is_authenticated
def create(context: DeploifaiContextObj, name: str, provider: str):
    """
    Create a new cloud profile
    """
    deploifai_api = context.api

    command_workspace = context.global_config["WORKSPACE"]["username"]

    try:
        cloud_profiles = deploifai_api.get_cloud_profiles(workspace=command_workspace)
    except DeploifaiAPIError as err:
        click.secho(err, fg="red")
        return

    existing_names = [cloud_profile.name for cloud_profile in cloud_profiles]

    if name in existing_names:
        click.echo(click.style("Cloud profile name taken. Existing names: ", fg="red") + ' '.join(existing_names))
        raise click.Abort()

    if not provider:
        provider = prompt(
            {
                "type": "list",
                "name": "provider",
                "message": "Choose a provider for the new cloud profile",
                "choices": [{"name": p.value, "value": p} for p in Provider]
            }
        )["provider"]
    else:
        provider = Provider(provider)   # Cast to Provider enum

    cloud_credentials = {}
    if provider == Provider.AWS:
        # Attempt to log in using .aws credentials
        iam = None
        try:
            iam = boto3.client('iam')
        except ClientError as err:
            click.echo(err)
            # TODO: Prompt user for credentials if .aws not found
            raise click.Abort()

        # Attempt to create user
        try:
            # Create user
            click.echo(f"Creating IAM user '{name}'...")
            iam.create_user(Path="/", UserName=name)

            # Attach policy
            click.echo("Created successfully. Attaching policies...")
            user = boto3.resource('iam').User(name)
            user.attach_policy(PolicyArn="arn:aws:iam::aws:policy/AdministratorAccess")

            # Create access key
            click.echo("Policies attached. Creating access keys...")
            access_key = iam.create_access_key(UserName=name)['AccessKey']
            cloud_credentials["awsAccessKey"] = access_key['AccessKeyId']
            cloud_credentials["awsSecretAccessKey"] = access_key['SecretAccessKey']
        except Exception as err:
            click.echo(err)
            # Delete user if error?
            raise click.Abort()

        # cloud_credentials["awsAccessKey"] = prompt(
        #     {
        #         "type": "input",
        #         "name": "awsAccessKey",
        #         "message": "AWS Access Key ID (We'll keep these secured and encrypted)",
        #     }
        # )["awsAccessKey"]
        # cloud_credentials["awsSecretAccessKey"] = prompt(
        #     {
        #         "type": "input",
        #         "name": "awsSecretAccessKey",
        #         "message": "AWS Secret Access Key (We'll keep these secured and encrypted)",
        #     }
        # )["awsSecretAccessKey"]
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

    context.debug_msg(cloud_credentials)
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
