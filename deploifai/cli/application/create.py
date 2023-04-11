import os
import click
import re
import docker
from time import sleep
from InquirerPy import prompt
from click_spinner import spinner

from deploifai.cli.api import DeploifaiAPIError
from deploifai.cli.context import pass_deploifai_context_obj, DeploifaiContextObj, is_authenticated, project_found, local_config


@click.command()
@click.argument("name")
@click.option(
    "--env-file",
    help="File path for environment variables (e.g. --env-file path/to/env1 --env-file path/to/env2)",
    multiple=True,
)
@click.option(
    "--env",
    help="Environment variables for the container (e.g. --env VAR1=VAL1 --env VAR2=VAL2)",
    multiple=True,
)
@click.option("--port", "-p", help="Port of container")
@pass_deploifai_context_obj
@is_authenticated
@project_found
def create(context: DeploifaiContextObj, name: str, env_file: tuple, env: tuple, port: int):
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
    if len(name) < 4 or len(name) > 30 or not re.match(r"^[a-z0-9-]+$", name):
        click.secho("Application name must contain only lowercase alphanumeric characters, and -, not contain spaces, "
                    "and must be between 4 and 30 characters long", fg="red")
        raise click.Abort()

    # Check if port is valid
    if port:
        try:
            port = int(port)
        except ValueError:
            click.secho("Port must be an integer", fg="red")
            raise click.Abort()
        if port < 0 or port > 65535:
            click.secho("Port must be between 0 and 65535", fg="red")
            raise click.Abort()

    # Check env files
    formatted_env = []
    for file in env_file:
        if not os.path.isfile(file):
            click.secho(f"Environment file does not exist: {file}", fg="red")
            raise click.Abort()
        with open(file, "r") as f:
            env_vars = f.read().splitlines()
            for env_var in env_vars:
                try:
                    key, val = env_var.split("=", maxsplit=1)
                except ValueError:
                    click.secho(f"Invalid environment variable: {env_var} in file {file}\n"
                                f"Environment variables must be in the format of KEY=VALUE", fg="red")
                    raise click.Abort()
                formatted_env.append({"name": key, "value": val})

    # Check env variables
    for env_var in env:
        try:
            key, val = env_var.split("=", maxsplit=1)
        except ValueError:
            click.secho(f"Invalid environment variable: {env_var}\n"
                        f"Environment variables must be in the format of KEY=VALUE", fg="red")
            raise click.Abort()
        formatted_env.append({"name": key, "value": val})

    # Check cloud profile
    existing_cloud_profiles = context.api.get_cloud_profiles(workspace=workspace)
    if len(existing_cloud_profiles) == 0:
        click.secho("Please create a cloud profile with deploifai cloud-profile create", fg="red")
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

    # Option for local or remote image
    is_local_image = prompt(
        {
            "type": "confirm",
            "message": "Use local docker image?",
            "default": True,
        }
    )[0]

    if is_local_image:
        # Initialize docker client
        try:
            docker_api = docker.APIClient(base_url='unix://var/run/docker.sock')
        except docker.errors.DockerException:
            click.secho("Docker does not seem to be running on your machine", fg="red")
            raise click.Abort()

        # Choose local image, filter out dangling images
        try:
            local_images = docker_api.images(filters={"dangling": False})
        except docker.errors.APIError:
            click.secho("Error while querying local images", fg="red")
            raise click.Abort()

        if len(local_images) == 0:
            click.secho("No local images found", fg="red")
            raise click.Abort()

        image = prompt(
            {
                "type": "list",
                "name": "image",
                "message": "Choose a local image",
                "choices": [{"name": image['RepoTags'], "value": image} for image in local_images]
            }
        )['image']

        # Prompt for tag
        tag = prompt(
            {
                "type": "input",
                "name": "tag",
                "message": "Image tag (default is 'latest')",
                "default": "latest",
            }
        )['tag']
        tag = tag if tag else "latest"

        # Option for existing or new image repository
        is_new_repository = prompt(
            {
                "type": "list",
                "message": "Use new or existing image repository?",
                "choices": [
                    {"name": "Create new image repository (on your cloud account)", "value": True},
                    {"name": "Use existing image repository (on your cloud account or Docker Hub)", "value": False},
                ]
            }
        )[0]

        if is_new_repository:
            # Create new image repository
            click.echo("Creating new image repository... ", nl=False)
            try:
                with spinner():
                    repository = context.api.create_container_registry(project_id, name, cloud_profile.id)
            except DeploifaiAPIError:
                click.secho("Error while creating new image repository", fg="red")
                raise click.Abort()
            click.echo("Done")
        else:
            # Check if deploifai managed container registries exist
            managed_repositories = context.api.get_container_registries(workspace, cloud_profile.id)
            if len(managed_repositories) == 0:
                click.secho("No existing Deploifai-managed repositories found. External repositories are currently not supported.", fg="red")
                raise click.Abort()
            managed_repository = prompt(
                {
                    "type": "list",
                    "name": "repository",
                    "message": "Choose an existing Deploifai-managed repository",
                    "choices": [{"name": repository['name'], "value": repository} for repository in
                                managed_repositories]
                }
            )['repository']
            repository = context.api.get_container_registry(managed_repository['id'])

        # Tag image
        repository_uri = repository['info']['imageUri']
        docker_api.tag(image=image, repository=repository_uri, tag=tag)
        click.echo(f"Tagged image with tag {tag}")

        # Authenticate docker to repository
        username, password = repository['info']['username'], repository['info']['password']
        click.echo("Authenticating to repository... ", nl=False)
        try:
            with spinner():
                docker_api.login(username=username, password=password, registry=repository['info']['loginServer'])
        except docker.errors.APIError:
            click.secho("Error while authenticating to repository", fg="red")
            raise click.Abort()
        click.echo("Done")

        # Push image
        click.echo(f"Pushing image {repository_uri}:{tag}... ", nl=False)
        try:
            with spinner():
                docker_api.push(repository_uri, tag=tag)
        except docker.errors.APIError:
            click.secho("Error while pushing image", fg="red")
            raise click.Abort()
        click.echo("Done")

        # Use repository uri + tag as image uri
        image_uri = repository_uri + ':' + tag
    else:
        # Use publicly accessible image (assume it is valid)
        image_uri = prompt(
            {
                "type": "input",
                "name": "image_uri",
                "message": "Enter public image name (e.g. nginx)",
            }
        )['image_uri']
        if not image_uri:
            click.secho("Please provide a valid image name", fg="red")
            raise click.Abort()

    # Get port
    if not port:
        port = prompt(
            {
                "type": "number",
                "min_allowed": 0,
                "max_allowed": 65535,
                "default": 80,
                "name": "port",
                "message": "Port of the container image"
            }
        )['port']

    try:
        port = int(port) if port else 80
        if port < 0 or port > 65535:
            raise ValueError
    except ValueError:
        click.secho("Please provide a valid port number", fg="red")
        raise click.Abort()

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
            "message": f"Choose a size for the application ({cloud_profile.provider})",
            "choices": [
                {
                    "name": f"{config['plan']} ({config['config']})",
                    "value": config,
                }
                for config in app_config
            ],
        }
    )['config']
    config = {'plan': chosen_config['plan']}

    # Create application
    click.echo(f"Creating application with image {image_uri}... ", nl=False)
    try:
        with spinner():
            application = context.api.create_application(project_id, name, cloud_profile.id, config, image_uri, port, formatted_env)
    except DeploifaiAPIError:
        click.secho("\nError while creating application", fg="red")
        raise click.Abort()
    click.secho(f"\nApplication {application['name']} created successfully", fg="green")

    # Poll for deployment status every 10 seconds
    click.echo("Deploying application (this will take a few minutes, and it's safe to CTRL+C) ... ", nl=False)
    with spinner() as s:
        while True:
            app = context.api.get_application(application['id'])
            status = app['status']
            if status == "DEPLOY_SUCCESS":
                s.stop()
                click.secho(f"\nApplication successfully deployed and is up on {app['hostname']}", fg="green")
                break
            elif status == "DEPLOY_ERROR":
                s.stop()
                click.secho("\nDeployment failed. This could be due to invalid or inaccessible docker image."
                            "Please contact us at contact@deploif.ai to troubleshoot.", fg="red")
                break
            else:
                sleep(10)
