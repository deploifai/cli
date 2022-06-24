from deploifai.clouds.azure.data_storage.handler import AzureDataStorageHandler
from deploifai.clouds.aws.data_storage.handler import AWSDataStorageHandler


class DataStorage:
    def __init__(self, context, api, config=None, handler=None):
        self.config = config
        self.context = context
        self.handler = handler
        if config is not None:
            self.register_handler(config, api)

    def register_handler(self, configs, api):
        config = configs["datastorage"]
        if config.get("provider") == "AZURE":
            self.handler = AzureDataStorageHandler(config, self.context, api)

        if config.get("provider") == "AWS":
            self.handler = AWSDataStorageHandler(config, self.context, api)

    def push(self):
        self.handler.push()
