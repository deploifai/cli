import click

from deploifai.api import DeploifaiAPIError
from deploifai.context import pass_deploifai_context_obj, DeploifaiContextObj, is_authenticated, project_found
from PyInquirer import prompt


@click.command()
@click.argument("name")
@pass_deploifai_context_obj
@is_authenticated
@project_found
def create(context: DeploifaiContextObj, name):
    """
    Create a new Training Server
    """

    # assume that the user should be in a project directory, that contains local configuration file
    project_id = context.local_config['PROJECT']['id']
    # getting all the information required from the get project api call
    fragment = """
    fragment project on Project {
        name
        account{
            username
        }
        dataStorages{
          id
          name
          cloudProfileId
          cloudProfile{
            provider
          }
          cloudProviderYodaConfig{
            awsConfig{
              awsRegion
            }
            azureConfig{
              azureRegion
            }
            gcpConfig{
              gcpZone
              gcpRegion
            }
          }
        }
    }
    """
    project_data = context.api.get_project(project_id=project_id, fragment=fragment)
    workspace_name = project_data["account"]["username"]
    workspace_id = project_data["account"]["id"]

    click.secho("Workspace Name: ".format(workspace_name), fg="blue")
    click.secho("Project Name: ".format(project_data["name"]), fg="blue")
    context.debug_msg(workspace_id)

    # obtaining the desired datastorage
    datastorage_info = project_data["dataStorages"]
    if len(datastorage_info) == 0:
        click.secho("Please use deploifai data create command to create a datastorage", fg="yellow")
        raise click.Abort()
    choose_datastorage = prompt(
        {
            "type": "list",
            "name": "datastorage",
            "message": "Choose a datastorage",
            "choices": [
                {
                    "name": "{}<{}>".format(info["name"], info["cloudProfile"]["provider"]),
                    "value": info
                }
                for info in datastorage_info
            ],
        }
    )
    if choose_datastorage == {}:
        raise click.Abort()

    # extract all the datastorage information required
    datastorage = choose_datastorage["datastorage"]
    datastorage_id = datastorage["id"]
    datastorage_name = datastorage["name"]
    datastorage_cloud_id = datastorage["cloudProfileId"]
    datastorage_cloud_provider = datastorage["cloudProfile"]["provider"]

    datastorage_aws_config = None
    datastorage_azure_config = None
    datastorage_gcp_config = None
    if datastorage_cloud_provider == "AWS":
        config = datastorage["cloudProviderYodaConfig"]["awsConfig"]["awsRegion"]
        datastorage_aws_config = {"awsRegion": config}
    elif datastorage_cloud_provider == "AZURE":
        config = datastorage["cloudProviderYodaConfig"]["azureConfig"]["azureRegion"]
        datastorage_azure_config = {"azureRegion": config}
    elif datastorage_cloud_provider == "GCP":
        config_region = datastorage["cloudProviderYodaConfig"]["gcpConfig"]["gcpRegion"]
        config_zone = datastorage["cloudProviderYodaConfig"]["gcpConfig"]["gcpZone"]
        datastorage_gcp_config = {"gcpRegion": config_region, "gcpZone": config_zone}

    # extracting cloud profile information
    cloud_profiles = context.api.get_cloud_profiles(workspace=workspace_name)
    if len(cloud_profiles) == 0:
        click.secho("Please use deploifai cloud-profile create command to create a cloud profile", fg="yellow")
        raise click.Abort()
    choose_cloud_profile = prompt(
        {
            "type": "list",
            "name": "cloud_profile",
            "message": "Choose a cloud profile for data storage",
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
    if choose_cloud_profile == {}:
        raise click.Abort()

    # extracting the cloud profile information
    cloud_profile = choose_cloud_profile["cloud_profile"]
    cloud_profile_id = cloud_profile["id"]
    cloud_profile_provider = cloud_profile["provider"]

    gpu_prompt = prompt(
        {
            "type": "list",
            "name": "use_gpu",
            "message": "Would you like the training server to use GPU?",
            "choices": ["Yes", "No"]
        }
    )
    if gpu_prompt == {}:
        raise click.Abort()
    gpu_option = gpu_prompt["use_gpu"]
    if gpu_option == "Yes":
        use_gpu = True
    elif gpu_option == "No":
        use_gpu = False

    # obtaining information of python version and ML Framework
    questions = [
        {
            "type": "list",
            "name": "ML Framework",
            "message": "Which ML Framework will you be using?",
            "choices": ["tenserflow", "pytorch"]
        },
        {
            "type": "input",
            "name": "Framework version",
            "message": "Please state which Framework version you will be using",
        },
        {
            "type": "input",
            "name": "python version",
            "message": "Please state which Python version you will be using",
        },
    ]

    ml_config = []
    while len(ml_config) == 0:
        version = prompt(questions=questions)
        ml_framework = version["ML Framework"]
        framework_version = version["Framework version"]
        python_version = version["python version"]
        ml_config = context.api.falcon_ml_config(python_version=python_version,
                                                 framework=ml_framework, framework_version=framework_version)
        if len(ml_config) == 0:
            click.secho("No matches for the versions provided, Please check your python and framework version",
                        fg="yellow")

    config_info = ml_config[-1]
    framework_version = config_info["frameworkVersion"]
    python_version = config_info["pythonVersion"]
    falcon_config_id = config_info["id"]
    click.secho("Framework Version: ".format(framework_version), fg="blue")
    click.secho("Python Version: ".format(python_version), fg="blue")

    if use_gpu:
        cuda_version = config_info["cudaVersion"]
        cudnn_version = config_info["cudnnVersion"]
        click.secho("Cuda Version: ".format(cuda_version), fg="blue")
        click.secho("Cudnn Version: ".format(cudnn_version), fg="blue")

    # extracting and choosing server instance size
    falcon_config = context.api.cloud_provider_falcon_config(use_gpu=use_gpu, cloud_provider=cloud_profile_provider)
    choose_falcon_config = prompt(
        {
            "type": "list",
            "name": "falcon",
            "message": "Choose a server instance size",
            "choices": [
                {
                    "name": "{plan}({config_type}) - {provider}".format(
                        plan=config["plan"],
                        config_type=config["config"],
                        provider=cloud_profile_provider,
                    ),
                    "value": config,
                }
                for config in falcon_config
            ],
        }
    )
