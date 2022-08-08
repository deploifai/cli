from pathlib import Path

from deploifai.api import DeploifaiAPI
from deploifai.clouds.azure.data_storage.handler import AzureDataStorageHandler
from deploifai.clouds.aws.data_storage.handler import AWSDataStorageHandler
from deploifai.clouds.gcp.data_storage.handler import GCPDataStorageHandler


class DataStorage:
    def __init__(self, api: DeploifaiAPI, dataset_id: str, handler=None):
        self.api = api
        self.id = dataset_id
        self.handler = handler
        self.register_handler()

    def register_handler(self):
        data = self.api.get_data_storage_info(self.id)
        provider = data["cloudProviderYodaConfig"]["provider"]
        if provider == "AZURE":
            self.handler = AzureDataStorageHandler(self.api, self.id)
        elif provider == "AWS":
            self.handler = AWSDataStorageHandler(self.api, self.id)
        elif provider == "GCP":
            self.handler = GCPDataStorageHandler(self.api, self.id)

    def push(self, target: Path):
        self.handler.push(target)

    def pull(self, target: Path):
        self.handler.pull(target)
