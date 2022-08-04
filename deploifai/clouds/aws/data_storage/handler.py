import typing
from pathlib import Path

import boto3

from deploifai.api import DeploifaiAPI
from deploifai.clouds.utilities.data_storage.handler import DataStorageHandler


class AWSDataStorageHandler(DataStorageHandler):
    def __init__(self, api: DeploifaiAPI, dataset_id: str):
        data = api.get_data_storage_info(dataset_id)

        container_cloud_name = data["containers"][0]['cloudName']

        aws_config_info = data["cloudProviderYodaConfig"]["awsConfig"]

        client = boto3.resource("s3",
                                region_name=aws_config_info["awsRegion"],
                                aws_access_key_id=aws_config_info["awsAccessKey"],
                                aws_secret_access_key=aws_config_info["awsSecretAccessKey"]
                                )

        super().__init__(dataset_id, container_cloud_name, client)

    @staticmethod
    def upload_file(client, file_path: Path, object_key: str, container_cloud_name: str):
        bucket = client.Bucket(container_cloud_name)
        obj = bucket.Object(object_key)

        with open(str(file_path), 'rb') as data:
            obj.upload_fileobj(data)

    def list_files(self, prefix: str = None) -> typing.Generator:
        if prefix is None:
            return self.client.Bucket(self.container_cloud_name).objects.all()
        return self.client.Bucket(self.container_cloud_name).objects.filter(Prefix=prefix)

    @staticmethod
    def download_file(
            client, file, dataset_directory: Path, container_cloud_name: str
    ):
        # getting the name(key) for each file and creating the folders as required
        key = file.key

        if '/' in key:
            DataStorageHandler.make_dirs(key, dataset_directory)

        file_path = str(dataset_directory.joinpath(key))
        bucket = client.Bucket(container_cloud_name)
        obj = bucket.Object(key)

        with open(file_path, 'wb') as file:
            obj.download_fileobj(file)
