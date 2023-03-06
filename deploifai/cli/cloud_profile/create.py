import base64
import json

import click
import boto3
from botocore.exceptions import ClientError
from google.oauth2 import service_account
from googleapiclient import discovery, errors
from InquirerPy import prompt
from deploifai.cli.utilities.cloud_profile import Provider
from deploifai.cli.context import (
    pass_deploifai_context_obj,
    DeploifaiContextObj,
    is_authenticated,
)
from deploifai.cli.api import DeploifaiAPIError


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
        try:
            provider = prompt(
                {
                    "type": "list",
                    "name": "provider",
                    "message": "Choose a provider for the new cloud profile",
                    "choices": [{"name": p.value, "value": p} for p in Provider]
                }
            )["provider"]
        except KeyError:
            click.secho('Mouse click detected', fg="red")
            raise click.Abort()
    else:
        provider = Provider(provider)   # Cast to Provider enum

    cloud_credentials = {}
    if provider == Provider.AWS:
        s = boto3.session.Session()
        profiles = s.available_profiles
        profile = 'default'
        if not profiles:
            click.secho('AWS credentials not found. Please set it up with "aws configure", or go to '
                        'https://docs.deploif.ai/cloud-services/connect-your-account/aws to learn how to create AWS '
                        'credentials for Deploifai on the dashboard.', fg="red")
            raise click.Abort()
        if len(profiles) > 1:
            try:
                profile = prompt(
                    {
                        "type": "list",
                        "name": "profile",
                        "message": "Choose an AWS profile to use",
                        "choices": [{"name": p, "value": p} for p in profiles]
                    }
                )["profile"]
                s = boto3.session.Session(profile_name=profile)
            except KeyError:
                click.secho('Mouse click detected', fg="red")
                raise click.Abort()

        local_creds = s.get_credentials()
        iam = boto3.client('iam', aws_access_key_id=local_creds.access_key, aws_secret_access_key=local_creds.secret_key)

        # Log in attempt - use an arbitrary service
        try:
            iam.list_users()
        except ClientError as err:
            if err.response['Error']['Code'] == 'InvalidClientTokenId':
                click.secho(f"Invalid credentials for profile '{profile}'", fg="red")
            else:
                click.secho(err, fg="red")
            raise click.Abort()
        except Exception as err:
            click.secho(err, fg="red")
            raise click.Abort()

        # Attempt to create user
        try:
            iam.create_user(Path="/", UserName=name)
            click.echo(f"Created IAM user '{name}'")
        except ClientError as err:
            if err.response['Error']['Code'] == 'EntityAlreadyExists':
                click.secho(f"IAM user '{name}' already exists", fg="red")
            else:
                click.secho(err, fg="red")
            raise click.Abort()
        except Exception as err:
            click.secho(err, fg="red")
            raise click.Abort()

        try:
            # Attach policies
            iam.attach_user_policy(UserName=name, PolicyArn="arn:aws:iam::aws:policy/PowerUserAccess")
            iam.attach_user_policy(UserName=name, PolicyArn="arn:aws:iam::aws:policy/IAMFullAccess")
            click.echo("Attached policies")

            # Create access key
            access_key = iam.create_access_key(UserName=name)['AccessKey']
            click.echo("Created access keys")
            cloud_credentials["awsAccessKey"] = access_key['AccessKeyId']
            cloud_credentials["awsSecretAccessKey"] = access_key['SecretAccessKey']
        except Exception as err:
            click.secho(err, fg="red")
            raise click.Abort()
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
        gcp_service_account_key_file = prompt(
            {
                "type": "input",
                "name": "gcp_service_account_key_file",
                "message": "File path for the GCP Service Account Key File (We'll keep these secured and encrypted)",
            }
        )["gcp_service_account_key_file"]

        with open(gcp_service_account_key_file) as f:
            project_id = json.load(f)['project_id']

        credentials = service_account.Credentials.from_service_account_file(
            gcp_service_account_key_file,
            scopes=["https://www.googleapis.com/auth/cloud-platform"],
        )

        service = discovery.build("iam", "v1", credentials=credentials)

        # Create service account
        try:
            gcp_service_account = service.projects().serviceAccounts().create(
                name='projects/' + project_id,
                body={
                    "accountId": name,
                    "serviceAccount": {
                        "displayName": name
                    }
                }
            ).execute()
        except errors.HttpError as err:
            if err.status_code == 409:
                click.secho(f"Service account '{name}' already exists", fg="red")
            else:
                click.secho(err, fg="red")
            raise click.Abort()

        # Create key
        service_account_email = name + '@' + project_id + '.iam.gserviceaccount.com'
        key = service.projects().serviceAccounts().keys().create(name=f'projects/{project_id}/serviceAccounts/{service_account_email}', body={}).execute()
        json_key_file = base64.b64decode(key['privateKeyData']).decode('utf-8')

        cloud_credentials["gcpProjectId"] = project_id
        cloud_credentials["gcpServiceAccountKey"] = json_key_file

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
