import subprocess
import os
import json

import click
import boto3
from botocore.exceptions import ClientError
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
        s = boto3.session.Session()
        profiles = s.available_profiles
        profile = 'default'
        if not profiles:
            click.secho('AWS credentials not found. Please set it up with "aws configure", or go to '
                        'https://docs.deploif.ai/cloud-services/connect-your-account/aws to learn how to create AWS '
                        'credentials for Deploifai on the dashboard.', fg="red")
            raise click.Abort()
        if len(profiles) > 1:
            profile = prompt(
                {
                    "type": "list",
                    "name": "profile",
                    "message": "Choose an AWS profile to use",
                    "choices": [{"name": p, "value": p} for p in profiles]
                }
            )["profile"]
            s = boto3.session.Session(profile_name=profile)

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
        # Select projects
        res = subprocess.run('gcloud projects list --format=json', shell=True, capture_output=True)
        if res.returncode != 0:
            raise click.Abort()
        projects = json.loads(res.stdout.decode('utf-8'))

        # Filter out inactive projects
        projects = [p for p in projects if p['lifecycleState'] == 'ACTIVE']
        if not projects:
            click.secho('No active Google Cloud projects found. Please create one using gcloud cli or at https://console.cloud.google.com/home/dashboard', fg="red")
            raise click.Abort()

        project_id = prompt(
            {
                "type": "list",
                "name": "project",
                "message": "Choose a Google Cloud project to use for this cloud profile",
                "choices": [{"name": f"{p['name']} ({p['projectId']})", "value": p['projectId']} for p in projects]
            }
        )["project"]

        cloud_credentials["gcpProjectId"] = project_id

        # Set project
        res = subprocess.run(f'gcloud config set project {project_id}', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if res.returncode != 0:
            raise click.Abort()
        click.echo(f"Set project to {project_id}")

        # Enable services
        res = subprocess.run('gcloud services enable artifactregistry.googleapis.com compute.googleapis.com iam.googleapis.com iamcredentials.googleapis.com storage-api.googleapis.com', shell=True)
        if res.returncode != 0:
            raise click.Abort()

        # Create service account
        res = subprocess.run(f'gcloud iam service-accounts create {name} --display-name {name} --description "Service account for Deploifai"', shell=True)
        if res.returncode != 0:
            raise click.Abort()

        # Get service account email
        res = subprocess.run(f'gcloud iam service-accounts list --filter="displayName:{name}" --format="value(email)"', shell=True, capture_output=True)
        if res.returncode != 0:
            raise click.Abort()
        service_account_email = res.stdout.decode('utf-8').strip()

        # Attach policies
        roles = ['roles/editor', 'roles/resourcemanager.projectIamAdmin', 'roles/storage.admin', 'roles/run.admin']
        for role in roles:
            res = subprocess.run(f"gcloud projects add-iam-policy-binding {project_id} --member=serviceAccount:{service_account_email} --role={role}", shell=True, capture_output=True)
            if res.returncode != 0:
                click.secho(res.stderr.decode('utf-8'), fg="red")
                raise click.Abort()
            click.echo(f"Attached role {role}")

        # Generate key file '.key.json' in current directory
        res = subprocess.run(f'gcloud iam service-accounts keys create .key.json --iam-account={service_account_email} --key-file-type=json', shell=True, capture_output=True)
        if res.returncode != 0:
            click.secho(res.stderr.decode('utf-8'), fg="red")
            raise click.Abort()

        # Extract key and delete key file
        try:
            with open(".key.json") as gcp_service_account_key_json:
                cloud_credentials["gcpServiceAccountKey"] = gcp_service_account_key_json.read()
            os.remove(".key.json")
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
