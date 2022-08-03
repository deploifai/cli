import os
import typing
from pathlib import Path
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed

from deploifai.utilities.config.dataset_config import find_config_path


class DataStorageHandler:
    def __init__(self, dataset_id: str, container_cloud_name: str, client):
        self.id = dataset_id
        self.container_cloud_name = container_cloud_name
        self.client = client

    def push(self):
        # assume the current working directory is the root directory of the dataset
        # pushes all files recursively to the container
        # overwrites all files in cloud
        root_directory = Path.cwd()
        self.upload_dataset(root_directory)

    def pull(self):
        # assume the current working directory is the root directory of the dataset
        # pulls all files recursively to the current working directory
        # overwrites all files in local
        root_directory = Path.cwd()
        self.download_dataset(root_directory)

    @staticmethod
    def upload_file(
        client, file_path: Path, directory: Path, container_cloud_name: str
    ):
        """
        Upload a given file to the cloud dataset.
        :param client: A client from the SDK of a specific cloud service provider.
        :param file_path: The file path to upload from pathlib.
        :param directory: The directory used to calculate a relative file path of the given file.
        :param container_cloud_name: The cloud name of the dataset.
        :return: None
        """
        pass

    def upload_dataset(self, directory: Path):
        """
        This function helps upload a directory to a container in a storage account.
        Uses a ThreadPoolExecutor to make uploads faster.
        :param directory: Root directory of the dataset.
        :return: None
        """
        directory_generator = Path(directory).glob("**/*")
        files = [f for f in directory_generator if f.is_file()]

        dataset_directory = find_config_path()
        os.chdir(dataset_directory)

        with tqdm(total=len(files)) as pbar:
            with ThreadPoolExecutor(max_workers=5) as ex:
                futures = [
                    ex.submit(
                        self.upload_file, self.client, file_path, dataset_directory, self.container_cloud_name
                    )
                    for file_path in files
                ]
                for future in as_completed(futures):
                    future.result()
                    pbar.update(1)

    def list_files(self) -> typing.Generator:
        """
        Returns a generator that lists all files in a cloud dataset.
        """
        pass

    @staticmethod
    def download_file(
            client, file, directory: Path, container_cloud_name: str
    ):
        pass

    def download_dataset(self, directory: Path):
        files = self.list_files()
        with ThreadPoolExecutor(max_workers=5) as ex:
            futures = [
                ex.submit(
                    self.download_file, self.client, file, directory, self.container_cloud_name
                )
                for file in files
            ]
            with tqdm(total=len(futures)) as pbar:
                for future in as_completed(futures):
                    future.result()
                    pbar.update(1)
