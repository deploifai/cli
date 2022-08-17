import click

from deploifai.context import (
    pass_deploifai_context_obj,
    DeploifaiContextObj,
    is_authenticated,
    dataset_found
)

from deploifai.utilities.frontend_routing import get_dataset_route


@click.command()
@pass_deploifai_context_obj
@is_authenticated
@dataset_found
def info(context: DeploifaiContextObj):
    """
    Get information about the initialized dataset
    """
    deploifai_api = context.api

    dataset_id = context.dataset_config["DATASET"]["id"]

    storage_details = deploifai_api.get_data_storage_info(dataset_id)

    project_name = storage_details["projects"][0]["name"]
    workspace_name = storage_details["account"]["username"]
    cloud_provider = storage_details["cloudProviderYodaConfig"]["provider"]
    container = storage_details["containers"][0]
    container_name = container["cloudName"]

    click.secho("Workspace Name: {}".format(workspace_name), fg="blue")
    click.secho("Project Name: {}".format(project_name), fg="blue")
    click.secho("Deploifai Dataset Name: {}".format(storage_details["name"]), fg="blue")
    click.secho("Dataset Status: {}".format(storage_details["status"]))

    url = get_dataset_route(workspace_name, project_name, dataset_id)
    click.secho(
        "\nAccess the dataset on deploifai through: \n{}\n".format(url),
        underline=True,
        fg="green",
    )

    click.secho("Container name to find the dataset on the cloud datastorage: {}".format(container_name), fg="green")

    if cloud_provider == "AZURE":
        storage_account_name = storage_details["cloudProviderYodaConfig"]["azureConfig"]["storageAccount"]
        click.secho("Storage account name for Azure access: {}".format(storage_account_name), fg="green")
