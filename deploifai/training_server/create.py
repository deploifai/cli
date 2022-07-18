import click
from PyInquirer import prompt

from deploifai.context import pass_deploifai_context_obj, DeploifaiContextObj, is_authenticated, project_found
from deploifai.utilities.version_comparision import compare, multi_compare
from deploifai.utilities.python_supported import supported

framework_options = ["tensorflow", "pytorch", "no_framework"]
server_options = ["SMALL", "MEDIUM", "LARGE"]


@click.command()
@click.argument("name")
@click.option("--framework", '-fw', type=str,
              help='ML framework to be installed in the server: {}'.format(framework_options))
@click.option("--framework-version", '-fwv', type=str, help="ML framework version to be installed")
@click.option("--python-version", '-py', type=str, help="Python version to be installed (works with selected ML framework)")
@click.option("--datastorage", "-ds", type=str, help="Name of datastorage to be used(type <no_datastorage> to work without one)")
@click.option("--cloud-profile-name", "-cp", type=str, help="Name of cloud profile to be used")
@click.option("--use-gpu/--dont-use-gpu", "-use/-dont", default=True, show_default=True,
              help="Create training server with or without GPU")
@click.option("--server-size", "-size", type=str, help="Size of server to be generated: {}".format(server_options))
@pass_deploifai_context_obj
@is_authenticated
@project_found
def create(context: DeploifaiContextObj, name, framework, framework_version, python_version,
           datastorage, cloud_profile_name, use_gpu, server_size):
    """
    Create a new Training Server
    """
    context.debug_msg(use_gpu)
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

    if framework_version and not framework:
        click.secho("Missing --framework option", fg="red")
        raise click.Abort()

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

    # obtaining the desired datastorage
    datastorage_info = project_data["dataStorages"]
    empty_option = {"name": "no_datastorage"}
    datastorage_info.append(empty_option)
    if datastorage:
        pick_datastorage = False
        for info in datastorage_info:
            if info["name"] == datastorage:
                pick_datastorage = info
                context.debug_msg("datastorage_info: {}".format(pick_datastorage))
        if not pick_datastorage:
            click.secho("Please provide a valid datastorage name", fg="red")
            raise click.Abort()
    else:
        choose_datastorage = prompt(
            {
                "type": "list",
                "name": "datastorage",
                "message": "Choose a datastorage",
                "choices": [
                    {
                        "name": "{}".format(info["name"]),
                        "value": info
                    }
                    for info in datastorage_info
                ],
            }
        )
        if choose_datastorage == {}:
            raise click.Abort()
        pick_datastorage = choose_datastorage["datastorage"]
    use_datastorage = True
    if pick_datastorage["name"] == "no_datastorage":
        use_datastorage = False
    context.debug_msg("use_datastorage: {}".format(use_datastorage))
    if use_datastorage:
        # extract all the datastorage information required
        datastorage = pick_datastorage
        datastorage_id = datastorage["id"]

    # extracting cloud profile information
    cloud_profiles = context.api.get_cloud_profiles(workspace=workspace_name)
    if len(cloud_profiles) == 0:
        click.secho("Please create a cloud profile with")
        click.secho("deploifai cloud-profile create", fg="yellow")
        raise click.Abort()
    if cloud_profile_name:
        cloud_profile = False
        for profile in cloud_profiles:
            if profile.name == cloud_profile_name:
                cloud_profile = profile
                context.debug_msg("cloud profile info: {}".format(cloud_profile))
        if not cloud_profile:
            click.secho("Please provide a valid cloud profile name", fg="red")
            raise click.Abort()
    else:
        choose_cloud_profile = prompt(
            {
                "type": "list",
                "name": "cloud_profile",
                "message": "Choose a cloud profile for training server",
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
        cloud_profile = choose_cloud_profile["cloud_profile"]

    # extracting the cloud profile information
    cloud_profile_id = cloud_profile.id
    cloud_profile_provider = cloud_profile.provider

    # Obtaining information of python and framework version if using framework

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

    if framework != "no_framework":
        if not python_version:
            if not framework and framework_version:
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

        falcon_config_exists = True

        if use_gpu:
            cuda_version = config_info["cudaVersion"]
            cudnn_version = config_info["cudnnVersion"]
            click.secho("Cuda Version: {}".format(cuda_version), fg="blue")
            click.secho("Cudnn Version: {}".format(cudnn_version), fg="blue")

    else:
        falcon_config_exists = False

    context.debug_msg(falcon_config_exists)

    # extracting and choosing server instance size
    falcon_config = context.api.cloud_provider_falcon_config(use_gpu=use_gpu, cloud_provider=cloud_profile_provider)
    if server_size:
        if use_gpu:
            server_size = server_size + "_GPU"
        else:
            server_size = server_size + "_CPU"
        falcon_config_chosen = False
        for config in falcon_config:
            if config["plan"] == server_size:
                falcon_config_chosen = config
        if not falcon_config_chosen:
            click.secho("Please provide a valid server size: {}".format(server_options))
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
    if falcon_config_exists:
        if use_datastorage:
            server_info = context.api.create_training_server(name=name, data_storage_id=datastorage_id,
                                                             cloud_profile_id=cloud_profile_id,
                                                             falcon_plan=falcon_plan, falcon_gpu=use_gpu,
                                                             falcon_id=falcon_config_id, project_id=project_id)
        else:
            server_info = context.api.create_training_server(name=name,
                                                             cloud_profile_id=cloud_profile_id,
                                                             falcon_plan=falcon_plan, falcon_gpu=use_gpu,
                                                             falcon_id=falcon_config_id, project_id=project_id)
    else:
        if use_datastorage:
            server_info = context.api.create_training_server(name=name, data_storage_id=datastorage_id,
                                                             cloud_profile_id=cloud_profile_id,
                                                             falcon_plan=falcon_plan, falcon_gpu=use_gpu,
                                                             project_id=project_id)
        else:
            server_info = context.api.create_training_server(name=name,
                                                             cloud_profile_id=cloud_profile_id,
                                                             falcon_plan=falcon_plan, falcon_gpu=use_gpu,
                                                             project_id=project_id)
    server_name = server_info["name"]
    server_status = server_info["status"]

    click.secho("Training Server with name <{}> is being deployed".format(server_name), fg="green")
    context.debug_msg(server_status)
