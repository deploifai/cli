from pathlib import Path

from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
import boto3

from deploifai.api import DeploifaiAPI
from deploifai.clouds.utilities.data_storage.handler import DataStorageHandler


class AWSDataStorageHandler(DataStorageHandler):
    def __init__(self, api: DeploifaiAPI, dataset_id: str):
        data = api.get_data_storage_info(self.id)
        
        container_cloud_name = data["containers"][0]['cloudName']
        
        client = boto3.client("s3")
        
        super().__init__(dataset_id, container_cloud_name, client)

    def push(self):
        # assume the current working directory is the root directory of the dataset
        # pushes all files recursively to the container
        root_directory = Path.cwd()
        self.upload_dataset(root_directory, self.container_cloud_name)

    @staticmethod
    def upload_file(client, file: Path, directory:Path, container_cloud_name: str):
        client.upload_file(
            str(file), container_cloud_name, str(file.relative_to(directory))
        )

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
