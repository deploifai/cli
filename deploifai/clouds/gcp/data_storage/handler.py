import json
import typing
from pathlib import Path

from google.cloud import storage
from google.oauth2.service_account import Credentials

from deploifai.api import DeploifaiAPI
from deploifai.clouds.utilities.data_storage.handler import DataStorageHandler


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
        blob_client = bucket_client.blob(object_key)
        blob_client.upload_from_filename(str(file_path))

    def list_files(self, prefix: str = None) -> typing.Generator:
        if prefix is None:
            return self.client.list_blobs(self.container_cloud_name)
        return self.client.list_blobs(self.container_cloud_name, prefix=prefix)

    @staticmethod
    def download_file(
            client, file, dataset_directory: Path, container_cloud_name: str
    ):
        # getting the name for each file and creating the folders as required
        name = file.name
        if '/' in name:
            DataStorageHandler.make_dirs(name, dataset_directory)

        bucket_client = client.get_bucket(container_cloud_name)
        blob_client = bucket_client.blob(name)

        file_path = str(dataset_directory.joinpath(name))

        blob_client.download_to_filename(file_path)
