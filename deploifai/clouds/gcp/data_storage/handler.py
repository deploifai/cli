import json
import os
import typing
from pathlib import Path

from google.cloud import storage
from google.oauth2.service_account import Credentials

from deploifai.clouds.utilities.data_storage.handler import DataStorageHandler

from deploifai.api import DeploifaiAPI


class GCPDataStorageHandler(DataStorageHandler):
    def __init__(self, api: DeploifaiAPI, dataset_id: str):
        data = api.get_data_storage_info(dataset_id)

        container_cloud_name = data["containers"][0]['cloudName']

        gcp_config_info = data["cloudProviderYodaConfig"]["gcpConfig"]

        service_account_key_json = json.loads(gcp_config_info["gcpServiceAccountKey"])

        credentials = Credentials.from_service_account_info(service_account_key_json)

        client = storage.Client(credentials=credentials)

        super().__init__(dataset_id, container_cloud_name, client)

    @staticmethod
    def upload_file(client, file_path: Path, object_key: str, container_cloud_name: str):
        bucket_client = client.get_bucket(container_cloud_name)
        blob_client = storage.Blob(object_key, bucket_client)
        blob_client.upload_from_filename(str(file_path))

    def list_files(self, directory: Path, target) -> typing.Generator:
        prefix = str(directory.relative_to(self.dataset_directory).as_posix())
        if prefix == ".":
            if target is None:
                return self.client.list_blobs(self.container_cloud_name)
            else:
                return self.client.list_blobs(self.container_cloud_name, prefix=target)
        else:
            if target is None:
                return self.client.list_blobs(self.container_cloud_name, prefix=prefix)
            else:
                prefix = prefix + "/" + target
                return self.client.list_blobs(self.container_cloud_name, prefix=prefix)

    @staticmethod
    def download_file(
            client, file, dataset_directory: Path, container_cloud_name: str
    ):
        # getting the name for each file and creating the folders as required
        name = file.name
        bucket_client = client.get_bucket(container_cloud_name)
        blob_client = bucket_client.blob(name)
        if "/" in name:
            folder_name = name.rsplit("/", 1)[0]
            folder_name = str(dataset_directory) + "/" + folder_name
            os.makedirs(folder_name, exist_ok=True)

        # defining a prefix for file import, and editing file path accordingly
        directory = Path.cwd()
        prefix = str(directory.relative_to(dataset_directory).as_posix())
        if prefix == ".":
            path = name
        else:
            prefix = prefix + "/"
            path = name.replace(prefix, "")

        blob_client.download_to_filename(path)
