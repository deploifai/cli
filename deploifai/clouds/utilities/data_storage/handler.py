import typing
from pathlib import Path
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed

from deploifai.utilities.config.dataset_config import find_config_directory
from colorama import Fore


class DataStorageHandler:
    def __init__(self, dataset_id: str, container_cloud_name: str, client):
        self.id = dataset_id
        self.container_cloud_name = container_cloud_name
        self.client = client
        self.dataset_directory = find_config_directory()

    def push(self, target: str = None):
        # assume the current working directory is the directory that contains all files that need to be uploaded
        # pushes all files recursively to the container
        # overwrites all files in cloud
        root_directory = Path.cwd()
        self.upload_dataset(root_directory, target)

    def pull(self, target: str):
        # assume the current working directory is the root directory of the dataset
        # pulls all files recursively to the current working directory
        # overwrites all files in local
        root_directory = Path.cwd()
        self.download_dataset(root_directory, target)

    @staticmethod
    def upload_file(
        client, file_path: Path, object_key: str, container_cloud_name: str
    ):
        """
        Upload a given file to the cloud dataset.
        :param client: A client from the SDK of a specific cloud service provider.
        :param file_path: The absolute file path to upload.
        :param object_key: The key of the file object in cloud storage
        :param container_cloud_name: The cloud name of the dataset.
        :return: None
        """
        pass

    def upload_dataset(self, directory: Path, target: str):
        """
        This function helps upload a directory to a container in a storage account.
        Uses a ThreadPoolExecutor to make uploads faster.
        :param directory: Root directory of the dataset.
        :param target: directory to be uploaded
        :return: None
        """
        directory_generator = Path(directory).glob("**/*")
        files = [f for f in directory_generator if f.is_file()]

        if target is not None:
            check = directory / target
            files = [f for f in files if check in f.parents]

        if len(files) == 0:
            print(Fore.YELLOW + "No files to upload in the cwd, please check the file pathing")
            return
        
        with tqdm(total=len(files)) as pbar:
            with ThreadPoolExecutor(max_workers=5) as ex:
                futures = [
                    ex.submit(
                        self.upload_file, self.client, file_path, str(file_path.relative_to(self.dataset_directory).as_posix()), self.container_cloud_name
                    )
                    for file_path in files
                ]
                for future in as_completed(futures):
                    future.result()
                    pbar.update(1)

    def list_files(self, directory, target) -> typing.Generator:
        """
        Returns a generator that lists all files in a cloud dataset.
        """
        pass

    @staticmethod
    def download_file(
            client, file, dataset_directory: Path, container_cloud_name: str
    ):
        pass

    def download_dataset(self, directory: Path, target: str):
        files = self.list_files(directory, target)

        with ThreadPoolExecutor(max_workers=5) as ex:
            futures = [
                ex.submit(
                    self.download_file, self.client, file, self.dataset_directory, self.container_cloud_name
                )
                for file in files
            ]
            if len(futures) == 0:
                print(Fore.YELLOW + "No files to download, please check the file pathing")
                return
            with tqdm(total=len(futures)) as pbar:
                for future in as_completed(futures):
                    future.result()
                    pbar.update(1)
