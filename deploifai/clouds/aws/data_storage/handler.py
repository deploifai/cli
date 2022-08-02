from pathlib import Path

from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
import boto3

from deploifai.api import DeploifaiAPI
from deploifai.clouds.utilities.data_storage.handler import DataStorageHandler


class AWSDataStorageHandler(DataStorageHandler):
    def __init__(self, api: DeploifaiAPI, dataset_id: str):
        data = api.get_data_storage_info(dataset_id)

        container_cloud_name = data["containers"][0]['cloudName']

        aws_config_info = data["cloudProviderYodaConfig"]["awsConfig"]

        client = boto3.client("s3",
                              region_name=aws_config_info["awsRegion"],
                              aws_access_key_id=aws_config_info["awsAccessKey"],
                              aws_secret_access_key=aws_config_info["awsSecretAccessKey"]
                              )

        super().__init__(dataset_id, container_cloud_name, client)

    @staticmethod
    def upload_file(client, file: Path, directory: Path, container_cloud_name: str):
        client.upload_file(
            str(file), container_cloud_name, str(file.relative_to(directory))
        )
