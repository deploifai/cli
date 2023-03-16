import click
import re
import docker
from InquirerPy import prompt

from deploifai.cli.api import DeploifaiAPIError
from deploifai.cli.context import pass_deploifai_context_obj, DeploifaiContextObj, is_authenticated, project_found, local_config


@click.command()
@click.argument("name")
@click.option("--port", "-p", help="Port of container")
@pass_deploifai_context_obj
@is_authenticated
@project_found
def create(context: DeploifaiContextObj, name: str, port: int):
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
            docker_api.login(username=username, password=password, registry=repository['info']['loginServer'])
        except docker.errors.APIError:
            click.secho("Error while authenticating to repository", fg="red")
            raise click.Abort()
        click.echo("Done")

        # Push image
        click.echo(f"Pushing image {repository_uri}:{tag}... ", nl=False)
        try:
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
    config = {'plan': chosen_config['plan']}

    # Get environment variables
    environment_variables = []
    count = 1
    click.echo("Enter environment variables in key-value pairs separated by spaces (leave blank to finish)")
    while True:
        env_variable = prompt(
            {
                "type": "input",
                "name": "env_variable",
                "message": f"Environment variable {count}"
            }
        )['env_variable']
        if env_variable == "":
            break

        env_variable = env_variable.split(" ")
        if len(env_variable) != 2:
            click.secho("Please provide a valid environment variable", fg="red")
            continue
        environment_variables.append({"name": env_variable[0], "value": env_variable[1]})
        count += 1

    # Create application
    click.echo(f"Creating application with image {image_uri}...",)
    try:
        application = context.api.create_application(project_id, name, cloud_profile.id, config, image_uri, port, environment_variables)
    except DeploifaiAPIError:
        click.secho("Error while creating application", fg="red")
        raise click.Abort()
    print(application)
    click.secho(f"Application {application['name']} created successfully", fg="green")

    # Save local config
    # TODO
