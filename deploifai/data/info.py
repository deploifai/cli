import click

from deploifai.context import pass_deploifai_context_obj, DeploifaiContextObj


@click.command()
@pass_deploifai_context_obj
def info(context: DeploifaiContextObj):
    data_storage_config = context.local_config["DATA_STORAGE"]

    if "id" not in data_storage_config:
        click.secho("No data storage configured for this project", fg="red")
        return

    deploifai_api = context.api

    data_storage_id = data_storage_config["id"]
    storage_details = deploifai_api.get_data_storage_info(data_storage_id)

    project_id = storage_details["project"]["id"]
    cloud_provider = storage_details["cloudProviderYodaConfig"]["provider"]
    container = storage_details["containers"][0]
    container_name = container["directoryName"]

    if cloud_provider == "AWS":
        click.secho("AWS data storages CLI support is coming soon.", fg="blue")

    elif cloud_provider == "AZURE":
        storage_account_name = storage_details["cloudProviderYodaConfig"][
            "azureConfig"
        ]["storageAccount"]

        click.secho("Deploifai Storage ID: {}".format(data_storage_id), fg="green")
        click.secho(
            "https://deploif.ai/dashboard/{username}/projects/{project_id}/datasets/{data_storage_id}\n".format(
                username=context.global_config["AUTH"]["username"],
                project_id=project_id,
                data_storage_id=data_storage_id,
            ),
            underline=True,
            fg="green",
        )
        click.secho("Azure Storage Account", bold=True, fg="blue", underline=True)
        click.secho("Storage Account Name: {}".format(storage_account_name), fg="blue")
        click.secho("Container Name: {}".format(container_name), fg="blue")
        click.secho(
            "\nYou could use the Azure CLI to list all the blobs in your container on Azure:",
            underline=True,
        )
        click.secho(
            "az storage blob list -c {container_name} --account-name {storage_account_name}".format(
                storage_account_name=storage_account_name, container_name=container_name
            ),
            fg="yellow",
        )

    elif cloud_provider == "GCP":
        click.secho("GCP data storages CLI support is coming soon.", fg="blue")
