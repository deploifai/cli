import pathlib
from pathlib import Path

from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
from google.cloud import storage
import os
from deploifai.utilities.config.find_config_filepath import find_config_absolute_path

from deploifai.api import DeploifaiAPI


class GCPDataStorageHandler:
    def __init__(self, api: DeploifaiAPI, dataset_id: str):
        relative_path = pathlib.Path("service-account-key.json")
        path = find_config_absolute_path(relative_path)
        self.path_str = str(path)
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = self.path_str
        self.client = storage.Client()
        self.id = dataset_id
        data = api.get_data_storage_info(self.id)
        self.container_cloud_name = data["containers"][0]['cloudName']

    def push(self):
        # assume the current working directory is the root directory of the dataset
        # pushes all files recursively to the container
        root_directory = Path.cwd()
        self.upload_dataset(root_directory, self.container_cloud_name)

    def upload_file(self, file: Path, directory, container_name, pbar):
        name = str(file.relative_to(directory))
        bucket_client = self.client.get_bucket(container_name)
        blob_client = storage.Blob(name, bucket_client)
        blob_client.upload_from_filename(name)
        pbar.update(1)

    def upload_dataset(self, directory: Path, container_name):
        directory_generator = Path(directory).glob("**/*")
        files = [f for f in directory_generator if f.is_file()]
        with tqdm(total=len(files)) as pbar:
            with ThreadPoolExecutor(max_workers=5) as ex:
                futures = [
                    ex.submit(
                        self.upload_file,
                        file_path,
                        directory,
                        container_name,
                        pbar=pbar,
                    )
                    for file_path in files
                ]
                for future in as_completed(futures):
                    future.result()
