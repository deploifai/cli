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
    click.secho("Deploifai Storage ID: {}".format(dataset_id), fg="blue")
    click.secho("Dataset Status: {}".format(storage_details["status"]))

    url = get_dataset_route(workspace_name, project_name, dataset_id)
    click.secho(
        "\nAccess the dataset on deploifai through: \n {}\n".format(url),
        underline=True,
        fg="green",
    )

    if cloud_provider == "AWS":
        click.secho("AWS Storage Account", bold=True, fg="green", underline=True)
        click.secho("Container Name: {}".format(container_name), fg="green")
        click.secho(
            "You could use the AWS CLI to list all the blobs in your container on AWS:",
            underline=True,
        )

        click.secho("aws s3 sync . s3://{}".format(container_name), fg="blue")

    elif cloud_provider == "AZURE":
        storage_account_name = storage_details["cloudProviderYodaConfig"]["azureConfig"]["storageAccount"]

        click.secho("Azure Storage Account", bold=True, fg="blue", underline=True)
        click.secho("Storage Account Name: {}".format(storage_account_name), fg="green")
        click.secho("Container Name: {}".format(container_name), fg="green")
        click.secho(
            "You could use the Azure CLI to list all the blobs in your container on Azure:",
            underline=True,
        )
        click.secho(
            "az storage blob list -c {container_name} --account-name {storage_account_name}".format(
                storage_account_name=storage_account_name, container_name=container_name
            ),
            fg="blue",
        )

    elif cloud_provider == "GCP":
        click.secho("GCP Storage Account", bold=True, fg="green", underline=True)
        click.secho("Container Name: {}".format(container_name), fg="green")
        click.secho(
            "You could use the GCP CLI to list all the blobs in your container on GCP:",
            underline=True,
        )

        click.secho("gsutil -m rsync -r . gs://{}".format(container_name), fg="blue")
