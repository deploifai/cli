from pathlib import Path
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
from azure.storage.blob import ContainerClient, BlobServiceClient


class AzureDataStorageHandler:
    def __init__(self, config, context, api):
        self.api = api
        self.context = context
        self.storage_account_id = config.get("id")
        self.storage_account_name = config.get("storage")
        self.containers = config.get("containers")

    def push(self):
        for container in self.containers:
            self.upload_dataset(
                Path("data/{}".format(container.get("name"))), container.get("value")
            )

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
        blob_client = container_client.get_blob_client(
            str(file_path.relative_to(directory))
        )
        blob_bytes = file_path.read_bytes()
        blob_client.upload_blob(
            data=blob_bytes, length=file_path.stat().st_size, overwrite=True
        )
        pbar.update(1)

    def upload_dataset(self, directory: Path, container_name):
        """
        This function helps upload a directory to a container in a storage account.
        Uses a ThreadPoolExecutor to make uploads faster.
        :param directory: Directory of the dataset.
        :return: None
        """
        account_url = "{account_name}.blob.core.windows.net".format(
            account_name=self.storage_account_name
        )
        blob_service_client = BlobServiceClient(
            account_url=account_url,
            credential=self.api.get_storage_account_access_key(self.storage_account_id),
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
