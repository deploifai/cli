from pathlib import Path
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
from azure.storage.blob import ContainerClient, BlobServiceClient

from deploifai.api import DeploifaiAPI


class AzureDataStorageHandler:
    def __init__(self, api: DeploifaiAPI, id: str):
        self.api = api

        data = api.get_data_storage(fragment)

        # todo: get all such information from graphql api
        self.storage_account_name = data["storageAccount"]
        self.storage_access_key = data['storageAccessKey']
        self.container_cloud_name = data['cloudName']

    def push(self):
        # assume the current working directory is the root directory of the dataset
        # pushes all files recursively to the container
        root_directory = Path.cwd()
        self.upload_dataset(root_directory, self.container_cloud_name)

    @staticmethod
    def upload_blob(
        container_client: ContainerClient, file_path: Path, directory: Path, pbar: tqdm
    ):
        """
        Upload a given blob to Azure Blob storage.
        :param container_client: ContainerClient from Azure SDK that has credentials already.
        :param file_path: The file path to upload from pathlib
        :param directory: The parent directory of the dataset
        :param pbar: tqdm progress bar.
        :return: None
        """
        blob = str(file_path.relative_to(directory))

        blob_client = container_client.get_blob_client(
            blob
        )
        blob_bytes = file_path.read_bytes()
        blob_client.upload_blob(
            data=blob_bytes, length=file_path.stat().st_size, overwrite=True
        )
        pbar.update(1)

    def upload_dataset(self, directory: Path, container_name: str):
        """
        This function helps upload a directory to a container in a storage account.
        Uses a ThreadPoolExecutor to make uploads faster.
        :param directory: Root directory of the dataset.
        :param container_name: Name of the container in the storage account.
        :return: None
        """
        account_url = "{account_name}.blob.core.windows.net".format(
            account_name=self.storage_account_name
        )
        blob_service_client = BlobServiceClient(
            account_url=account_url,
            credential=self.storage_access_key,
        )
        container_client = blob_service_client.get_container_client(container_name)
        directory_generator = Path(directory).glob("**/*")
        files = [f for f in directory_generator if f.is_file()]

        with tqdm(total=len(files)) as pbar:
            with ThreadPoolExecutor(max_workers=5) as ex:
                futures = [
                    ex.submit(
                        self.upload_blob, container_client, file_path, directory, pbar
                    )
                    for file_path in files
                ]
                for future in as_completed(futures):
                    future.result()
