import boto3


class AWS:
  def __init__(self):
    self.deploifai_api = DeploifaiAPI(context)
  
  def __str__(self):
    return "AWS"

  def upload_dataset(self, storage_account_id, storage_account_name: str, container: str, directory: Path):
    pass
