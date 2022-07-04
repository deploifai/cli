import typing
from json import JSONDecodeError

import requests

from deploifai.api.errors import DeploifaiAPIError
from deploifai.utilities.credentials import get_auth_token
from deploifai.cloud_profile.cloud_profile import CloudProfile
from deploifai.utilities import environment


def _parse_cloud_profile(cloud_profile_json, workspace) -> CloudProfile:
    """
    Re-usable function that can help parse cloud profile JSON.

    For example:
    cloudProfiles{
      id
      name
      provider
    }
    :param cloud_profile_json: JSON of Cloud profile
    :param workspace: The workspace/account where the cloud profile should belong to
    :return: CloudProfile
    """
    cloud_profile = CloudProfile(
        id=cloud_profile_json["id"],
        name=cloud_profile_json["name"],
        provider=cloud_profile_json["provider"],
        workspace=workspace,
    )
    return cloud_profile


class DeploifaiAPI:
    def __init__(self, auth_token: str = None):
        self.uri = "{backend_url}/graphql".format(backend_url=environment.backend_url)
        self.headers = {"authorization": auth_token} if auth_token else {}

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
        query_response = requests.post(
            self.uri, headers=self.headers, json={"query": query}
        )
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
        r = requests.post(
            self.uri,
            json={"query": query, "variables": {"id": data_storage_id}},
            headers=self.headers,
        )
        try:
            data_storage_containers = r.json()["data"]["dataStorage"]["containers"]
            data_storage_containers = map(
                lambda d: {"name": d.get("directoryName"), "value": d.get("cloudName")},
                data_storage_containers,
            )
            return data_storage_containers
        except TypeError:
            return []

    def get_data_storages(self, workspace):
        query = """
      query($id:String){
        dataStorages(whereAccount:{
          id: $id
        }, whereDataStorage:{
          status: {
            equals: DEPLOY_SUCCESS
          }
        }) {
          id
          name
          status
          account {
            username
          }
        }
      }
    """
        query_json = {"query": query, "variables": {"id": workspace["id"]}}

        try:
            query_response = requests.post(
                self.uri, headers=self.headers, json=query_json
            )
            query_response_json = query_response.json()
            return query_response_json["data"]["dataStorages"]
        except JSONDecodeError as err:
            """
            Handle errors when the JSON is not decoded
            For Python3
            """
            raise DeploifaiAPIError("The API did not return a JSON object")
        except ValueError as err:
            """
            Handle errors when the JSON is not decoded
            For Python2
            """
            raise DeploifaiAPIError("The API did not return a JSON object")

    def get_data_storage_info(self, storage_id):
        query = """
    query($id:String){
      dataStorage(where:{id:$id}){
        name
        status
        project {
          id
        }
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
        r = requests.post(
            self.uri,
            json={"query": query, "variables": {"id": storage_id}},
            headers=self.headers,
        )
        storage_details = r.json()["data"]["dataStorage"]
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
        r = requests.post(
            self.uri,
            json={"query": query, "variables": {"id": storage_id}},
            headers=self.headers,
        )
        return r.json()["data"]["dataStorage"]["cloudProviderYodaConfig"][
            "azureConfig"
        ]["storageAccessKey"]

    def create_data_storage(
        self,
        storage_name: str,
        container_names: typing.List[str],
        cloud_profile: CloudProfile,
        region=None,
    ):
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
        if cloud_profile.provider == "AWS":
            aws_config = {"awsRegion": "us-east-1"}
        elif cloud_profile.provider == "AZURE":
            azure_config = {"azureRegion": "East US"}

        variables = {
            "whereAccount": {"username": cloud_profile.workspace},
            "data": {
                "name": storage_name,
                "containerNames": container_names,
                "cloudProfileId": cloud_profile.id,
                "cloudProviderYodaConfig": {
                    "awsConfig": aws_config,
                    "azureConfig": azure_config,
                },
            },
        }
        r = requests.post(
            self.uri,
            json={"query": mutation, "variables": variables},
            headers=self.headers,
        )
        create_mutation_data = r.json()
        return create_mutation_data["data"]["createDataStorage"]

    def get_cloud_profiles(self, workspace=None) -> typing.List[CloudProfile]:
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
          username
          cloudProfiles{
            id
            name
            provider
          }
        }
      }
    }
    """
        r = requests.post(self.uri, json={"query": query}, headers=self.headers)
        api_data = r.json()

        personal_cloud_profile_account = api_data["data"]["me"]["account"]
        personal_cloud_profiles_json = personal_cloud_profile_account["cloudProfiles"]
        # Get personal cloud profiles from a part of the query
        personal_cloud_profiles = list(
            map(
                lambda x: _parse_cloud_profile(
                    x, personal_cloud_profile_account["username"]
                ),
                personal_cloud_profiles_json,
            )
        )

        team_cloud_profiles_json = api_data["data"]["me"]["teams"]
        team_cloud_profiles_accounts = list(
            map(lambda teams: teams["account"], team_cloud_profiles_json)
        )

        team_cloud_profiles = []
        for team_cloud_profiles_account in team_cloud_profiles_accounts:
            cps = list(
                map(
                    lambda x: _parse_cloud_profile(
                        x, team_cloud_profiles_account["username"]
                    ),
                    team_cloud_profiles_account["cloudProfiles"],
                )
            )
            team_cloud_profiles += cps

        cloud_profiles = personal_cloud_profiles + team_cloud_profiles

        if workspace:
            return [
                cloud_profile
                for cloud_profile in cloud_profiles
                if cloud_profile.workspace == workspace["username"]
            ]
        return cloud_profiles

    def get_projects(self, workspace, fragment: str, where_project=None):
        query = (
            """    
            query($whereAccount: AccountWhereUniqueInput!, $whereProject: ProjectWhereInput) {
              projects(whereAccount: $whereAccount, whereProject: $whereProject) {
                ...project
              }
            }
            """
            + fragment
        )

        if where_project:
            variables = {
                "whereAccount": {"username": workspace["username"]},
                "whereProject": where_project,
            }
        else:
            variables = {"whereAccount": {"username": workspace["username"]}}

        try:
            r = requests.post(
                self.uri,
                json={"query": query, "variables": variables},
                headers=self.headers,
            )
            api_data = r.json()

            return api_data["data"]["projects"]
        except TypeError as err:
            raise DeploifaiAPIError("Could not get projects. Please try again.")
        except KeyError as err:
            raise DeploifaiAPIError("Could not get projects. Please try again.")

    def get_project(self, project_id: str, fragment: str):
        query = (
            """    
                query ($where: ProjectWhereUniqueInput!){
                    project(where: $where) {
                    ...project
                  }
                }
                """
            + fragment
        )

        variables = {
            "where": {"id": project_id},
        }

        try:
            r = requests.post(
                self.uri,
                json={"query": query, "variables": variables},
                headers=self.headers,
            )
            api_data = r.json()

            return api_data["data"]["project"]
        except TypeError as err:
            raise DeploifaiAPIError("Could not get project. Please try again.")
        except KeyError as err:
            raise DeploifaiAPIError("Could not get project. Please try again.")

    def create_project(self, project_name: str, cloud_profile: CloudProfile):
        mutation = """
    mutation(
      $whereAccount: AccountWhereUniqueInput!
      $data: CreateProjectInput!
    ) {
      createProject(whereAccount: $whereAccount, data: $data) {
        id
      }
    }
    """

        variables = {
            "whereAccount": {"username": cloud_profile.workspace},
            "data": {
                "name": project_name,
                "cloudProfileId": cloud_profile.id,
            },
        }

        try:
            r = requests.post(
                self.uri,
                json={"query": mutation, "variables": variables},
                headers=self.headers,
            )

            create_mutation_data = r.json()

            return create_mutation_data["data"]["createProject"]
        except TypeError as err:
            raise DeploifaiAPIError("Could not create project. Please try again.")
        except KeyError as err:
            raise DeploifaiAPIError("Could not create project. Please try again.")
