from pathlib import Path

from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
import boto3


class AWSDataStorageHandler:
    def __init__(self, config, context, api):
        self.client = boto3.client("s3")
        self.containers = config.get("containers")

    def push(self):
        for container in self.containers:
            self.upload_dataset(
                Path("data/{}".format(container.get("name"))), container.get("value")
            )

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
