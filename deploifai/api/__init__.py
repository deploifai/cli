import itertools
from json import JSONDecodeError

import click
import requests

from deploifai.api.errors import DeploifaiAPIError
from deploifai.auth.credentials import get_auth_token
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

  def get_containers(self, answers):
    data_storage_id = answers["storage_option"]
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
    data_storage_containers = r.json()['data']['dataStorage']['containers']
    data_storage_containers = map(lambda d: {'name': d.get('directoryName'), 'value': d.get('cloudName')},
                                  data_storage_containers)
    return data_storage_containers

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
