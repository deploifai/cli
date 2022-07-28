from pathlib import Path

from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
import boto3

from deploifai.api import DeploifaiAPI


class AWSDataStorageHandler:
    def __init__(self, api: DeploifaiAPI, dataset_id: str):
        self.client = boto3.client("s3")
        self.id = dataset_id
        data = api.get_data_storage_info(self.id)
        self.container_cloud_name = data["containers"][0]['cloudName']

    def push(self):
        # assume the current working directory is the root directory of the dataset
        # pushes all files recursively to the container
        root_directory = Path.cwd()
        self.upload_dataset(root_directory, self.container_cloud_name)

    def upload_file(self, file: Path, directory, container_name, pbar):
        self.client.upload_file(
            str(file), container_name, str(file.relative_to(directory))
        )
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

    def get_client_credentials(self):
        query = """
      query($id:String){
        dataStorage(where:{id:$id}){
          cloudProviderYodaConfig{
            awsConfig {
              storageAccount
              storageAccessKey
            }
          }
        }
      }
    """
