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
    click.secho("Dataset Name: {}".format(storage_details["name"]), fg="blue")
    click.secho("Dataset Status: {}".format(storage_details["status"]), fg="blue")

    url = get_dataset_route(workspace_name, project_name, dataset_id)
    click.secho("\nBrowse the dataset on Deploifai: \n{}\n".format(url))

    click.secho("To find this dataset on {} cloud service portal:".format(cloud_provider))

    if cloud_provider == "AZURE":
        storage_account_name = storage_details["cloudProviderYodaConfig"]["azureConfig"]["storageAccount"]
        click.secho("Storage Account Name: {}".format(storage_account_name))
    click.secho("Container Name: {}".format(container_name))
