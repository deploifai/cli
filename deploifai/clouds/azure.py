from pathlib import Path
from tqdm import tqdm
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient, ContainerClient
from concurrent.futures import ThreadPoolExecutor, as_completed


class AzureTools:
  def __init__(self):
    # TODO: Fix this azure credentials. Seems to not work at all.
    self.credential = DefaultAzureCredential()

  @staticmethod
  def upload_blob(container_client: ContainerClient, file_path: Path, pbar: tqdm):
    blob_client = container_client.get_blob_client(str(file_path))
    blob_bytes = file_path.read_bytes()
    blob_client.upload_blob(data=blob_bytes, length=file_path.stat().st_size)
    pbar.update(1)

  def upload_dataset(self, storage: str, container: str, directory: Path):
    storage_account_name = storage
    account_url = "https://{account_name}.blob.core.windows.net/".format(account_name=storage_account_name)
    blob_service_client = BlobServiceClient(
      account_url=account_url,
      credential=self.credential,
    )

    container_client = blob_service_client.get_container_client(container)
    directory_generator = Path(directory).glob("**/*")
    files = [f for f in directory_generator if f.is_file()]

    with tqdm(total=len(files)) as pbar:
      with ThreadPoolExecutor(max_workers=5) as ex:
        futures = [ex.submit(self.upload_blob, container_client, file_path, pbar) for file_path in files]
        for future in as_completed(futures):
          future.result()
