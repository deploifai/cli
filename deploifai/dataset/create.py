import click
import click_spinner
from PyInquirer import prompt
import os
from time import sleep

from deploifai.api import DeploifaiAPIError
from deploifai.context import (
    pass_deploifai_context_obj,
    DeploifaiContextObj,
    is_authenticated,
    project_found,
)
from deploifai.utilities.config import dataset_config


@click.command()
@pass_deploifai_context_obj
@project_found
@is_authenticated
def create(context: DeploifaiContextObj):
    """
    Create a new dataset
    """

    deploifai_api = context.api
    # assume that the user should be in a project directory, that contains local configuration file
    project_id = context.local_config["PROJECT"]["id"]

    # query for workspace name from api
    fragment = """
                    fragment project on Project {
                        name
                        account{
                            username
                        }
                    }
                    """
    context.debug_msg(project_id)
    project_data = context.api.get_project(project_id=project_id, fragment=fragment)
    project_name = project_data["name"]
    command_workspace = project_data["account"]["username"]
    context.debug_msg(command_workspace)
    click.secho("Workspace:{}\n".format(command_workspace), fg='green')
    click.secho("Project:{}<{}>\n".format(project_name, project_id), fg='green')

    try:
        cloud_profiles = deploifai_api.get_cloud_profiles(
            workspace=command_workspace
        )
    except DeploifaiAPIError as err:
        click.echo("Could not fetch cloud profiles. Please try again.")
        return
    new_storage_questions = [
        {
            "type": "input",
            "name": "storage_name_input",
            "message": "Name the dataset",
        },
        {
            "type": "list",
            "name": "cloud_profile",
            "message": "Choose a cloud profile for dataset",
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
        },
    ]
    new_storage_answers = prompt(questions=new_storage_questions)
    if new_storage_answers == {}:
        raise click.Abort()
    storage_name = new_storage_answers["storage_name_input"]
    cloud_profile = new_storage_answers["cloud_profile"]

    click.secho("Cloud Profile:{}".format(cloud_profile), fg='green')
    click.secho("Dataset Name:{}".format(storage_name), fg='green')

    click.secho("Creating a new dataset.", fg="blue")

    context.debug_msg(cloud_profile)

    try:
        create_storage_response = deploifai_api.create_data_storage(
            storage_name, project_id, cloud_profile
        )
    except DeploifaiAPIError as err:
        click.secho(err, fg='red')
        raise click.Abort()

    context.debug_msg(create_storage_response)

    with click_spinner.spinner():
        click.echo("Deploying dataset")
        while True:
            data_storage_info = deploifai_api.get_data_storage_info(
                create_storage_response["id"]
            )
            if data_storage_info["status"] == "DEPLOY_SUCCESS":
                click.echo("Deployment success!")
                break
            elif data_storage_info["status"] == "DEPLOY_ERROR":
                click.echo("There was an error in deployment.")
                break
            sleep(10)

    # Obtaining information of cloud provider for dataset created
    storage_id = create_storage_response["id"]
    cloud_data = context.api.get_data_storage_info(storage_id=storage_id)

    dataset_name = cloud_data["name"]
    cloud_provider = cloud_data["cloudProviderYodaConfig"]["provider"]

    click.secho("Storage Name: {}".format(dataset_name), fg="blue")
    click.secho("Cloud Provider: {}".format(cloud_provider), fg="blue")
    context.debug_msg(cloud_data["containers"][0])
    context.debug_msg(cloud_data["cloudProviderYodaConfig"])

    if cloud_provider == "AWS":
        cloud_name = cloud_data["containers"][0]["cloudName"]
        link = "s3://" + cloud_name
        click.secho("AWS s3 link: {}".format(link))
    elif cloud_provider == "GCP":
        cloud_name = cloud_data["containers"][0]["cloudName"]
        link = "gs://" + cloud_name
        click.secho("GCP link: {}".format(link))
    elif cloud_provider == "AZURE":
        cloud_name = cloud_data["containers"][0]["cloudName"]
        azure_account = cloud_data["cloudProviderYodaConfig"]["azureConfig"]["storageAccount"]
        click.secho("account-name: {}".format(azure_account))
        click.secho("container-name: {}".format(cloud_name))

    # create a dataset directory locally, along with dataset.cfg file within
    try:
        os.mkdir(storage_name)
    except OSError:
        click.secho("An error occurred when creating the dataset locally", fg="red")
        click.echo("But the dataset has been created on Deploifai")
        raise click.Abort()

    click.secho(f"A new directory named {storage_name} has been created locally.", fg="green")

    dataset_path = os.path.join(os.getcwd(), storage_name)
    dataset_config.create_config_files(dataset_path)

    # storing the dataset information in the dataset.cfg file
    context.dataset_config = dataset_config.read_config_file()
    # set dataset id in dataset config file
    dataset_config.add_data_storage_config(create_storage_response["id"], context.dataset_config)