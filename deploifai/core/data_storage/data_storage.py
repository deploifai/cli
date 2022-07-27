from deploifai.api import DeploifaiAPI
from deploifai.clouds.azure.data_storage.handler import AzureDataStorageHandler
from deploifai.clouds.aws.data_storage.handler import AWSDataStorageHandler


class DataStorage:
    def __init__(self,  api: DeploifaiAPI, dataset_id: str, handler=None):
        self.api = api
        self.id = dataset_id
        self.handler = handler
        self.register_handler()

    def register_handler(self):
        data = self.api.get_data_storage_info(self.id)
        if data["cloudProviderYodaConfig"]["provider"] == "AZURE":
            self.handler = AzureDataStorageHandler(self.api, self.id)
        # if data.get("provider") == "AWS":
        #   self.handler = AWSDataStorageHandler(config, self.context, api)

    def push(self):
        self.handler.push()
