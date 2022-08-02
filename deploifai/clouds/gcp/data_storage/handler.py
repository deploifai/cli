import json
import pathlib
from pathlib import Path

from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
from google.cloud import storage
from google.oauth2.service_account import Credentials

import os
from deploifai.utilities.config.find_config_filepath import find_config_absolute_path
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
    def upload_file(client, file: Path, directory: Path, container_cloud_name: str):
        name = str(file.relative_to(directory))
        bucket_client = client.get_bucket(container_cloud_name)
        blob_client = storage.Blob(name, bucket_client)
        blob_client.upload_from_filename(name)
