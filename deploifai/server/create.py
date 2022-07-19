import click
from PyInquirer import prompt

from deploifai.context import pass_deploifai_context_obj, DeploifaiContextObj, is_authenticated, project_found
from deploifai.utilities.version_comparison import compare, multi_compare
from deploifai.utilities.python_supported import supported

framework_options = ["tensorflow", "pytorch"]
server_options = ["small", "medium", "large"]

server_sizes = {
    "cpu": {"small": "SMALL_CPU", "medium": "MEDIUM_CPU", "large": "LARGE_CPU"},
    "gpu": {"small": "SMALL_GPU", "medium": "MEDIUM_GPU", "large": "LARGE_GPU"},
}


@click.command()
@click.argument("name")
@click.option("--no-dataset", is_flag=True, default=False, show_default=True,
              help="Do not mount any datasets on the server")
@click.option("--dataset", "-d", type=str, help="Name of dataset to be mounted on the server")
@click.option("--cloud-profile", "-c", type=str, help="Name of cloud profile to be used")
@click.option("--gpu/--no-gpu", default=True, show_default=True, help="Create training server with or without GPU")
@click.option("--no-framework", is_flag=True, default=False, show_default=True,
              help="Do not install ML frameworks in the server")
@click.option("--framework", '-fw', type=str,
              help='ML framework to be installed in the server: {}'.format(framework_options))
@click.option("--framework-version", '-fwv', type=str, help="ML framework version to be installed")
@click.option("--python-version", '-py', type=str, help="Python version to be installed (works with selected ML framework)")
@click.option("--server-size", "-size", type=str, help="Size of training server: {}".format(server_options))
@pass_deploifai_context_obj
@is_authenticated
@project_found
def create(context: DeploifaiContextObj, name, no_dataset, dataset, cloud_profile, gpu,
           no_framework, framework, framework_version, python_version, server_size):
    """
    Create a new Training Server
    """
    # checking if provided python version is supported or is substring of a supported version
    if python_version:
        python_supported = supported(python_version)
        if not python_supported:
            click.secho("The python version <{}> provided is not supported by Deploifai".format(python_version), fg="red")
            raise click.Abort()

    # checking if correct framework is provided
    if framework and framework not in framework_options:
        click.secho("The ML framework <{}> provided is not supported by Deploifai".format(framework), fg="red")
        raise click.Abort()

    # checking if framework version exists when framework is not specified
    if framework_version and not framework:
        click.secho("Missing --framework option", fg="red")
        raise click.Abort()

    # validating server size input
    if server_size:
        if server_size not in server_options:
            click.secho("Server size <{}> is not supported. Please choose from one of {}".format(server_size, server_options), fg="red")
            raise click.Abort()

    # assume that the user should be in a project directory, that contains local configuration file
    project_id = context.local_config['PROJECT']['id']
    context.debug_msg(project_id)
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
          cloudProfile{
            provider
          }
        }
    }
    """
    project_data = context.api.get_project(project_id=project_id, fragment=fragment)
    workspace_name = project_data["account"]["username"]

    click.secho("Workspace Name: {}".format(workspace_name), fg="blue")
    click.secho("Project Name: {}".format(project_data["name"]), fg="blue")

    # extracting cloud profile information
    existing_cloud_profiles = context.api.get_cloud_profiles(workspace=workspace_name)
    if len(existing_cloud_profiles) == 0:
        click.secho("Please create a cloud profile with")
        click.secho("deploifai cloud-profile create", fg="yellow")
        raise click.Abort()
    if cloud_profile:
        profile = None
        for existing_cloud_profile in existing_cloud_profiles:
            if existing_cloud_profile.name == cloud_profile:
                profile = existing_cloud_profile
                context.debug_msg("cloud profile info: {}".format(profile))
                break
        if not profile:
            click.secho("Please provide a valid cloud profile name", fg="red")
            raise click.Abort()

    # obtaining the desired dataset
    context.debug_msg(no_dataset)
    if not no_dataset:
        dataset_info = project_data["dataStorages"]
        if dataset:
            pick_dataset = None
            for info in dataset_info:
                if info["name"] == dataset:
                    pick_dataset = info
                    context.debug_msg("dataset_info: {}".format(pick_dataset))
                    break
            if not pick_dataset:
                click.secho("Please provide a valid dataset name", fg="red")
                raise click.Abort()
        else:
            choose_dataset = prompt(
                {
                    "type": "list",
                    "name": "dataset",
                    "message": "Choose a dataset",
                    "choices": [
                        {
                            "name": "{} <{}>".format(info["name"], info["cloudProfile"]["provider"]),
                            "value": info
                        }
                        for info in dataset_info
                    ],
                }
            )
            if choose_dataset == {}:
                raise click.Abort()
            pick_dataset = choose_dataset["dataset"]
        dataset_ids = [pick_dataset["id"]]
    else:
        dataset_ids = None

    # extracting cloud profile information
    if not cloud_profile:
        choose_cloud_profile = prompt(
            {
                "type": "list",
                "name": "cloud_profile",
                "message": "Choose a cloud profile for training server",
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
        )
        if choose_cloud_profile == {}:
            raise click.Abort()
        profile = choose_cloud_profile["cloud_profile"]

    # extracting the cloud profile information
    cloud_profile_id = profile.id
    cloud_profile_provider = profile.provider

    # Obtaining information of python and framework version if using framework

    if not no_framework:
        if not framework:
            questions = [
                {
                    "type": "list",
                    "name": "ML Framework",
                    "message": "Which ML Framework will you be using?",
                    "choices": framework_options
                },
            ]
            version = prompt(questions=questions)
            if version == {}:
                raise click.Abort()
            framework = version["ML Framework"]

        if not python_version:
            if not framework_version:
                variable = {"pythonVersion": {"endsWith": '.0'}}
                distinct = "pythonVersion"
                py_options = context.api.falcon_ml_config_distinct(variable, distinct)
                py_version = [info["pythonVersion"] for info in py_options]
                index, py_option = compare(py_version)
                py_option = [element[:-2] for element in py_option]
                choose_python = prompt(
                    {
                        "type": "list",
                        "name": "python_version",
                        "message": "Choose a version of python you would like to use",
                        "choices": [
                            {
                                "name": "{}".format(option),
                                "value": option,
                            }
                            for option in py_option
                        ],
                    }
                )
                if choose_python == {}:
                    raise click.Abort()
                python_version = choose_python["python_version"]
            elif framework and framework_version:
                variable = {"pythonVersion": {"endsWith": '.0'},
                            "framework": {"equals": framework},
                            "frameworkVersion": {"startsWith": framework_version}}
                distinct = "pythonVersion"
                py_options = context.api.falcon_ml_config_distinct(variable, distinct)
                py_version = [info["pythonVersion"] for info in py_options]
                index, py_option = compare(py_version)
                py_option = [element[:-2] for element in py_option]
                choose_python = prompt(
                    {
                        "type": "list",
                        "name": "python_version",
                        "message": "Choose a version of python you would like to use",
                        "choices": [
                            {
                                "name": "{}".format(option),
                                "value": option,
                            }
                            for option in py_option
                        ],
                    }
                )
                if choose_python == {}:
                    raise click.Abort()
                python_version = choose_python["python_version"]

        if not framework_version:
            variable = {"pythonVersion": {"startsWith": python_version},
                        "framework": {"equals": framework}}
            distinct = "frameworkVersion"
            fm_options = context.api.falcon_ml_config_distinct(variable, distinct)
            fm_version = [info["frameworkVersion"] for info in fm_options]
            index, fm_option = compare(fm_version)
            choose_framework = prompt(
                {
                    "type": "list",
                    "name": "framework_version",
                    "message": "Choose a version of {} you would like to use".format(framework),
                    "choices": [
                        {
                            "name": "{}".format(option),
                            "value": option,
                        }
                        for option in fm_option
                    ],
                }
            )
            if choose_framework == {}:
                raise click.Abort()
            framework_version = choose_framework["framework_version"]

        variable = {"pythonVersion": {"startsWith": python_version},
                    "framework": {"equals": framework},
                    "frameworkVersion": {"startsWith": framework_version}}

        ml_config = context.api.falcon_ml_config(variable)
        if len(ml_config) == 0:
            click.secho("No matches for the versions provided, Please select framework version again",
                        fg="yellow")

            # Selecting framework version
            variable = {"pythonVersion": {"startsWith": python_version},
                        "framework": {"equals": framework}}
            distinct = "frameworkVersion"
            fm_options = context.api.falcon_ml_config_distinct(variable, distinct)
            fm_version = [info["frameworkVersion"] for info in fm_options]
            index, fm_option = compare(fm_version)
            choose_framework = prompt(
                {
                    "type": "list",
                    "name": "framework_version",
                    "message": "Choose a version of {} you would like to use".format(framework),
                    "choices": [
                        {
                            "name": "{}".format(option),
                            "value": option,
                        }
                        for option in fm_option
                    ],
                }
            )
            if choose_framework == {}:
                raise click.Abort()
            framework_version = choose_framework["framework_version"]

            variable = {"pythonVersion": {"startsWith": python_version},
                        "framework": {"equals": framework},
                        "frameworkVersion": {"startsWith": framework_version}}

            ml_config = context.api.falcon_ml_config(variable)

            if len(ml_config) == 0:
                click.secho("No matches for the versions provided, Please check your python and framework version",
                            fg="red")
                raise click.Abort()

        py_version = [info["pythonVersion"] for info in ml_config]
        index, return_list = compare(py_version)
        fm_version = [info["frameworkVersion"] for info in ml_config]
        specific_index = multi_compare(fm_version, index)
        config_info = ml_config[specific_index]

        framework_version = config_info["frameworkVersion"]
        python_version = config_info["pythonVersion"]
        falcon_config_id = config_info["id"]
        click.secho("Python Version: {}".format(python_version), fg="blue")
        click.secho("Framework Version: {}".format(framework_version), fg="blue")

        if gpu:
            cuda_version = config_info["cudaVersion"]
            cudnn_version = config_info["cudnnVersion"]
            click.secho("Cuda Version: {}".format(cuda_version), fg="blue")
            click.secho("Cudnn Version: {}".format(cudnn_version), fg="blue")

    else:
        falcon_config_id = None

    # extracting and choosing server instance size
    falcon_config = context.api.get_training_infrastructure_plans(uses_gpu=gpu, cloud_provider=cloud_profile_provider)
    if server_size:
        if gpu:
            server_family = server_sizes['gpu']
        else:
            server_family = server_sizes["cpu"]
        size = server_family[server_size]

        falcon_config_chosen = None
        for config in falcon_config:
            if config["plan"] == size:
                falcon_config_chosen = config
                break

    else:
        choose_falcon_config = prompt(
            {
                "type": "list",
                "name": "falcon",
                "message": "Choose a server instance size",
                "choices": [
                    {
                        "name": "{plan} ({config_type}) - {provider}".format(
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
        if choose_falcon_config == {}:
            raise click.Abort()
        falcon_config_chosen = choose_falcon_config["falcon"]
    falcon_plan = falcon_config_chosen["plan"]

    # creating server info and providing its information to user
    server_info = context.api.create_training_server(name=name, data_storage_ids=dataset_ids,
                                                     cloud_profile_id=cloud_profile_id,
                                                     falcon_plan=falcon_plan, uses_gpu=gpu,
                                                     falcon_ml_config_id=falcon_config_id, project_id=project_id)
    server_name = server_info["name"]
    server_status = server_info["status"]

    click.secho("Training Server with name <{}> is being deployed".format(server_name), fg="green")
    context.debug_msg(server_status)
