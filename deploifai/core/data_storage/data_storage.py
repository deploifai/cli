from deploifai.api import DeploifaiAPI
from deploifai.clouds.azure.data_storage.handler import AzureDataStorageHandler
from deploifai.clouds.aws.data_storage.handler import AWSDataStorageHandler


class DataStorage:
    def __init__(self,  api: DeploifaiAPI, id: str, handler=None):
        self.api = api
        self.id = id
        self.handler = handler

        self.register_handler()

    def register_handler(self):
        # if config.get("provider") == "AZURE":
        self.handler = AzureDataStorageHandler(self.api, self.id)

        # if config.get("provider") == "AWS":
        #     self.handler = AWSDataStorageHandler(config, self.context, api)

    def push(self):
        self.handler.push()
