import abc
import os
import typing
from pathlib import Path
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed

from deploifai.utilities.config.dataset_config import find_config_directory


class DataStorageHandlerException(Exception):
    pass


class DataStorageHandlerEmptyFilesException(DataStorageHandlerException):
    def __str__(self):
        return "DataStorageHandlerEmptyFilesException: No files found in the dataset"


class DataStorageHandlerTargetNotFoundException(DataStorageHandlerException):
    def __str__(self):
        return "DataStorageHandlerTargetNotFoundException: Target not found"


class DataStorageHandler(abc.ABC):
    def __init__(self, dataset_id: str, container_cloud_name: str, client):
        self.id = dataset_id
        self.container_cloud_name = container_cloud_name
        self.client = client
        self.dataset_directory = find_config_directory()

    def push(self, target: Path):
        """
        Uploads files to the cloud in the target directory.
        :param target: The absolute path to the target file or directory to be uploaded.
        """
        self.upload_dataset(target)

    def pull(self, target: Path):
        """
        Downloads files from the cloud in the target directory, overwriting files.
        :param target: The absolute path to the target file or directory to be downloaded.
        """
        self.download_dataset(target)

    @staticmethod
    def upload_file(
        client, file_path: Path, object_key: str, container_cloud_name: str
    ):
        """
        Upload a given file to the cloud dataset.
        :param client: A client from the SDK of a specific cloud service provider.
        :param file_path: The absolute file path to upload.
        :param object_key: The key of the file object in cloud storage.
        :param container_cloud_name: The cloud name of the dataset.
        :return: None
        """
        pass

    def upload_dataset(self, target: Path):
        """
        This function helps upload a directory to the cloud.
        Uses a ThreadPoolExecutor to make uploads faster.
        :param target: The absolute path to target file or directory to be uploaded.
        :return: None
        """
        if not target.exists():
            raise DataStorageHandlerTargetNotFoundException()

        # if target is a file, set it into the files list
        if target.is_file():
            files = [target]
        else:
            # if target is a directory, upload all files in it
            directory_generator = Path(target).glob("**/*")
            files = [f for f in directory_generator if f.is_file()]

            if len(files) == 0:
                raise DataStorageHandlerEmptyFilesException()

        # begin uploading
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

    def list_files(self, prefix: str = None) -> typing.Generator:
        """
        Returns a generator that lists all files in a cloud dataset based on a given prefix.
        :param prefix: The prefix of the files to be listed.
        """
        pass

    @staticmethod
    def download_file(
            client, file, dataset_directory: Path, container_cloud_name: str
    ):
        """
        Download a given file from the cloud to the local dataset.
        :param client: A client from the SDK of a specific cloud service provider.
        :param file: A file object yielded by the list_files generator.
        :param dataset_directory: The absolute directory path of the local dataset.
        :param container_cloud_name: The cloud name of the dataset.
        """
        pass

    @staticmethod
    def make_dirs(object_key: str, dataset_directory: Path):
        """
        Creates the directories of the file in the local dataset.
        :param object_key: The key of the file object.
        :param dataset_directory: The absolute directory path of the local dataset.
        """
        relative_path = object_key.rsplit("/", 1)[0]
        abs_path = str(dataset_directory.joinpath(relative_path))
        os.makedirs(abs_path, exist_ok=True)

    def download_dataset(self, target: Path):
        """
        Downloads files from the cloud in the target directory.
        :param target: The absolute path to the target file or directory to be downloaded.
        """
        if target == self.dataset_directory:
            prefix = None
        else:
            prefix = target.relative_to(self.dataset_directory).as_posix()

        files = self.list_files(prefix)

        with ThreadPoolExecutor(max_workers=5) as ex:
            futures = [
                ex.submit(
                    self.download_file, self.client, file, self.dataset_directory, self.container_cloud_name
                )
                for file in files
            ]

            if len(futures) == 0:
                raise DataStorageHandlerEmptyFilesException()

            with tqdm(total=len(futures)) as pbar:
                for future in as_completed(futures):
                    future.result()
                    pbar.update(1)
