import itertools
from json import JSONDecodeError

import click
import requests

from deploifai.api.errors import DeploifaiAPIError
from deploifai.auth.credentials import get_auth_token
from deploifai.constants.yoda import cloud_provider_yoda_versions
from deploifai.utilities import environment


class DeploifaiAPI:
  def __init__(self, context=None):
    token = get_auth_token(context.config["AUTH"]["username"])
    self.uri = "{backend_url}/graphql".format(backend_url=environment.backend_url)
    self.headers = {'authorization': "deploifai-{token}".format(token=token)}

  @staticmethod
  def _parse_data_storages(api_data):
    personal_data_storages = api_data['data']['me']['account']['dataStorages']

    team_data_storages = list(map(lambda x: x['account']['dataStorages'], api_data['data']['me']['teams']))
    team_data_storages = list(itertools.chain(*team_data_storages))

    return personal_data_storages, team_data_storages

  def get_user(self):
    query = """
    query {
      me {
        id
        account {
          id
          username
        }
        teams {
          id
          account {
            id
            username
          }
        }
      }
    }
    """
    query_response = requests.post(self.uri, headers=self.headers, json={'query': query})
    user_data = query_response.json()
    return user_data["data"]["me"]

  def get_containers(self, data_storage_id):
    query = """
    query($id:String){
      dataStorage(where:{id:$id}){
        containers{
          id
          directoryName
          cloudName
        }
      }
    }
    """
    r = requests.post(self.uri, json={'query': query, 'variables': {'id': data_storage_id}},
                      headers=self.headers)
    try:
      data_storage_containers = r.json()['data']['dataStorage']['containers']
      data_storage_containers = map(lambda d: {'name': d.get('directoryName'), 'value': d.get('cloudName')},
                                    data_storage_containers)
      return data_storage_containers
    except TypeError:
      return []

  def get_data_storages(self):
    query = """
      query{
        me{
          account{
            dataStorages(where:{status: {equals:DEPLOY_SUCCESS}}){
              id
              name
              status
              account {
                username
              }
            }
          }

          teams {
            account {
              dataStorages(where:{status: {equals:DEPLOY_SUCCESS}}){
                id
                name
                status
                account {
                  username
                }
              }
            }
          }
        }
      }
    """
    query_json = {"query": query}

    try:
      query_response = requests.post(self.uri, headers=self.headers, json=query_json)
      query_response_json = query_response.json()
      return DeploifaiAPI._parse_data_storages(query_response_json)
    except JSONDecodeError as err:
      """
      Handle errors when the JSON is not decoded
      For Python3
      """
      click.echo("Could not get information from Deploifai.")
      raise DeploifaiAPIError("The API did not return a JSON object")
    except ValueError as err:
      """
      Handle errors when the JSON is not decoded
      For Python2
      """
      click.echo("Could not get information from Deploifai.")
      raise DeploifaiAPIError("The API did not return a JSON object")

  def get_data_storage_info(self, storage_id):
    query = """
    query($id:String){
      dataStorage(where:{id:$id}){
        name
        status
        containers{
          id
          directoryName
          cloudName
        }
        cloudProviderYodaConfig{
          provider
          awsConfig{
            awsRegion
          } 
          azureConfig{
            azureRegion
            storageAccount
          }
        }
      }
    }
    """
    r = requests.post(self.uri, json={'query': query, 'variables': {'id': storage_id}},
                      headers=self.headers)
    storage_details = r.json()['data']['dataStorage']
    return storage_details

  def get_storage_account_access_key(self, storage_id: str):
    query = """
    query($id:String){
      dataStorage(where:{id:$id}){
        cloudProviderYodaConfig{
          azureConfig{
            storageAccount
            storageAccessKey
          }
        }
      }
    }
    """
    r = requests.post(self.uri, json={'query': query, 'variables': {'id': storage_id}},
                      headers=self.headers)
    return r.json()["data"]["dataStorage"]["cloudProviderYodaConfig"]["azureConfig"]["storageAccessKey"]

  def create_data_storage(self, storage_name, container_names, cloud_profile, workspace, region=None):
    mutation = """
    mutation(
      $whereAccount: AccountWhereUniqueInput!
      $data: CreateDataStorageInput!
    ) {
      createDataStorage(whereAccount: $whereAccount, data: $data) {
        id
      }
    }
    """
    aws_config = None
    azure_config = None
    # TODO: Support more regions
    if cloud_profile["profile"]["provider"] == 'AWS':
      aws_config = {
        'awsRegion': 'us-east-1'
      }
    elif cloud_profile["profile"]["provider"] == "AZURE":
      azure_config = {
        'azureRegion': 'East US'
      }

    variables = {
      'whereAccount': {
        'username': workspace["username"]
      },
      'data': {
        'name': storage_name,
        'containerNames': container_names,
        'cloudProfileId': cloud_profile["profile"]["id"],
        'cloudProviderYodaConfig': {
          'version': cloud_provider_yoda_versions[cloud_profile["profile"]["provider"]],
          'awsConfig': aws_config,
          'azureConfig': azure_config
        }
      }
    }
    r = requests.post(self.uri, json={'query': mutation, 'variables': variables}, headers=self.headers)
    create_mutation_data = r.json()
    return create_mutation_data["data"]["createDataStorage"]

  def get_cloud_profiles(self):
    query = """
    query{
      me{
        teams{
          account{
            username
            cloudProfiles{
              id
              name
              provider
            }
          }
        }
        account{
          cloudProfiles{
            id
            name
            provider
          }
        }
      }
    }
    """
    r = requests.post(self.uri,
                      json={'query': query},
                      headers=self.headers)
    api_data = r.json()

    personal_cloud_profiles_json = api_data["data"]["me"]["account"]["cloudProfiles"]
    team_cloud_profiles_json = api_data["data"]["me"]["teams"]
    personal_cloud_profiles = map(lambda ps: {'workspace': "Personal", 'profile': ps},
                                  personal_cloud_profiles_json)
    team_cloud_profiles_accounts = list(map(lambda teams: teams["account"], team_cloud_profiles_json))
    team_cloud_profiles_workspaces = list(map(lambda cp: {'workspace': cp["username"], 'profiles': cp["cloudProfiles"]},
                                              team_cloud_profiles_accounts))
    team_cloud_profiles = []
    for team_cloud_profiles_workspace in team_cloud_profiles_workspaces:
      for profile in team_cloud_profiles_workspace["profiles"]:
        team_cloud_profiles.append({
          'workspace': team_cloud_profiles_workspace['workspace'],
          'profile': profile
        })
    return list(personal_cloud_profiles), list(team_cloud_profiles)
