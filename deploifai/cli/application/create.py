import click
import re
from InquirerPy import prompt

from deploifai.cli.api import DeploifaiAPIError
from deploifai.cli.context import pass_deploifai_context_obj, DeploifaiContextObj, is_authenticated, project_found, local_config


@click.command()
@click.argument("name")
@click.option("--image", "-i", help="Name of container image")
@click.option("--tag", "-t", help="Tag of container image")
@click.option("--port", "-p", help="Port of container")
@pass_deploifai_context_obj
@is_authenticated
@project_found
def create(context: DeploifaiContextObj, name: str, image: str, tag: str, port: int):
    """
    Create or update a new deployment
    """
    # Query required data
    project_id = context.local_config['PROJECT']['id']
    workspace = context.global_config['WORKSPACE']['username']

    # Check if name is taken
    where_application = {
        "name": {"equals": name},
        "project": {"is": {"id": {"equals": project_id}}},
        "status": {"not": {"equals": "DESTROY_SUCCESS"}}
    }
    try:
        applications = context.api.get_applications(workspace=workspace, where_application=where_application)
        if len(applications) > 0:
            click.secho("Application name already exists", fg="red")
            raise click.Abort()
    except DeploifaiAPIError:
        click.secho("Error while querying applications", fg="red")
        raise click.Abort()

    # Check if name is valid
    if len(name) < 4 or len(name) > 30 or not re.match('^[\w-]+$', name):
        click.secho("Application name must contain only alphanumeric characters, and -, not contain spaces, "
                    "and must be between 4 and 30 characters long", fg="red")
        raise click.Abort()

    # Check cloud profile
    existing_cloud_profiles = context.api.get_cloud_profiles(workspace=workspace)
    if len(existing_cloud_profiles) == 0:
        click.secho("Please create a cloud profile with")
        click.secho("deploifai cloud-profile create", fg="yellow")
        raise click.Abort()

    cloud_profile = prompt(
        {
            "type": "list",
            "name": "cloud_profile",
            "message": "Choose a cloud profile",
            "choices": [
                {
                    "name": "{name}({workspace}) - {provider}".format(
                        name=profile.name,
                        workspace=profile.workspace,
                        provider=profile.provider,
                    ),
                    "value": profile,
                }
                for profile in existing_cloud_profiles
            ],
        }
    )['cloud_profile']

    cloud_profile_id = None
    for existing_cloud_profile in existing_cloud_profiles:
        if existing_cloud_profile.name == cloud_profile.name:
            cloud_profile_id = existing_cloud_profile.id
            context.debug_msg("cloud profile id: {}".format(cloud_profile_id))
            break
    if not cloud_profile_id:
        click.secho("Please provide a valid cloud profile name", fg="red")
        raise click.Abort()

    # Check image
    if not image:
        image = prompt(
            {
                "type": "input",
                "name": "image",
                "message": "Name of the container image"
            }
        )['image']
    if not image:
        click.secho("Please provide a valid container image name", fg="red")
        raise click.Abort()

    # Extract name and tag
    if not tag:
        tag = prompt(
            {
                "type": "input",
                "name": "tag",
                "message": "Tag of the container image (default is 'latest')"
            }
        )['tag']
        tag = tag if tag else 'latest'

    # Get port
    if not port:
        port = prompt(
            {
                "type": "number",
                "min_allowed": 0,
                "max_allowed": 65535,
                "default": 80,
                "name": "port",
                "message": "Port of the container image (default is 80)"
            }
        )['port']

    try:
        port = int(port) if port else 80
        if port < 0 or port > 65535:
            raise ValueError
    except ValueError:
        click.secho("Please provide a valid port number", fg="red")
        raise click.Abort()

    # Check if container registry exists
    # TODO
    # existing_container_registries = context.api.get_container_registries(workspace=workspace)
    # for existing_container_registry in existing_container_registries:
    #     if existing_container_registry.image == f'{image}:{tag}':
    #         click.secho("Container registry already exists", fg="red")
    #         raise click.Abort()

    # Create container registry
    image_uri = f'{image}:{tag}'
    create_container_data = context.api.create_container_registry(project_id, image_uri, cloud_profile_id)

    # Create plan
    try:
        app_config = context.api.get_application_infrastructure_plans(cloud_provider=cloud_profile.provider)
    except DeploifaiAPIError:
        click.secho("Could not find application infrastructure plans", fg="red")
        raise click.Abort()

    # Get app config
    chosen_config = prompt(
        {
            "type": "list",
            "name": "config",
            "message": "Choose a size for the application",
            "choices": [
                {
                    "name": "{plan} ({config_type}) - {provider}".format(
                        plan=config["plan"],
                        config_type=config["config"],
                        provider=cloud_profile.provider,
                    ),
                    "value": config,
                }
                for config in app_config
            ],
        }
    )['config']

    # Get environment variables
    # TODO
    environment_variables = []

    # Create application
    context.api.create_application(project_id, name, cloud_profile_id, chosen_config, image_uri, port, environment_variables)

    # Save local config
    # TODO
