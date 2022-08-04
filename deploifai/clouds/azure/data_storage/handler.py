import os
import typing
from pathlib import Path
from azure.storage.blob import ContainerClient, BlobServiceClient, BlobProperties

from deploifai.api import DeploifaiAPI
from deploifai.clouds.utilities.data_storage.handler import DataStorageHandler


class AzureDataStorageHandler(DataStorageHandler):
    def __init__(self, api: DeploifaiAPI, dataset_id: str):
        data = api.get_data_storage_info(dataset_id)

        self.storage_account_name = data["cloudProviderYodaConfig"]["azureConfig"]["storageAccount"]
        self.storage_access_key = data["cloudProviderYodaConfig"]["azureConfig"]['storageAccessKey']
        container_cloud_name = data["containers"][0]['cloudName']

        account_url = "{account_name}.blob.core.windows.net".format(
            account_name=self.storage_account_name
        )
        blob_service_client = BlobServiceClient(
            account_url=account_url,
            credential=self.storage_access_key,
        )
        client = blob_service_client.get_container_client(container_cloud_name)

        super().__init__(dataset_id, container_cloud_name, client)

    @staticmethod
    def upload_file(
        client: ContainerClient, file_path: Path, object_key: str, container_cloud_name: str
    ):
        blob_client = client.get_blob_client(object_key)
        blob_bytes = file_path.read_bytes()
        blob_client.upload_blob(
            data=blob_bytes, length=file_path.stat().st_size, overwrite=True
        )

    def list_files(self, directory: Path, target) -> typing.Generator:
        prefix = str(directory.relative_to(self.dataset_directory).as_posix())
        if prefix == ".":
            if target is None:
                return self.client.list_blobs()
            else:
                return self.client.list_blobs(name_starts_with=target)
        else:
            if target is None:
                return self.client.list_blobs(name_starts_with=prefix)
            else:
                prefix = prefix + "/" + target
                return self.client.list_blobs(name_starts_with=prefix)

    @staticmethod
    def download_file(
            client: ContainerClient, file: BlobProperties, dataset_directory: Path, container_cloud_name: str
    ):
        file_name = file.name
        blob_client = client.get_blob_client(file_name)
        if "/" in file_name:
            names = file_name.rsplit("/", 1)[0]
            names = str(dataset_directory) + "/" + names
            os.makedirs(names, exist_ok=True)

        download_file_path = os.path.join(dataset_directory, file_name)
        with open(download_file_path, "wb") as download_file:
            download_file.write(blob_client.download_blob().readall())
