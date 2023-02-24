from enum import Enum

class Provider(Enum):
    AWS = "AWS"
    AZURE = "AZURE"
    GCP = "GCP"

class CloudProfile:
    def __init__(self, id, name, provider, workspace):
        self.id = id
        self.name = name
        self.provider = provider
        self.workspace = workspace
