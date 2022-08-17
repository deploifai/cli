import typing
from json import JSONDecodeError

import requests

from deploifai.api.errors import DeploifaiAPIError
from deploifai.utilities.credentials import get_auth_token
from deploifai.utilities.cloud_profile import CloudProfile
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
          isTeam
        }
        teams {
          id
          account {
            id
            username
            isTeam
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

    def get_data_storages(self, workspace: str, where_data_storage: dict = None):
        query = """
      query($username:String $where: DataStorageWhereInput){
        dataStorages(whereAccount:{
          username: $username
        }, whereDataStorage: $where) {
          id
          name
          status
          account {
            username
          }
          cloudProfile{
            provider
          }
        }
      }
    """

        variables = {
            "username": workspace,
            "where": where_data_storage
        }

        query_json = {"query": query, "variables": variables}

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
        account{
          username
        }
        projects {
          id
          name
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
            awsAccessKey
            awsSecretAccessKey
          }
          azureConfig{
            azureRegion
            storageAccount
            storageAccessKey
          }
          gcpConfig{
            gcpServiceAccountKey
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
            project_id: str,
            cloud_profile: CloudProfile,
            region=None,
    ):
        mutation = """
    mutation(
      $whereProject: ProjectWhereUniqueInput!
      $data: CreateDataStorageInput!
    ) {
      createDataStorage(whereProject: $whereProject, data: $data) {
        id
      }
    }
    """
        aws_config = None
        azure_config = None
        gcp_config = None
        # TODO: Support more regions
        if cloud_profile.provider == "AWS":
            aws_config = {"awsRegion": "us-east-1"}
        elif cloud_profile.provider == "AZURE":
            azure_config = {"azureRegion": "East US"}
        elif cloud_profile.provider == "GCP":
            gcp_config = {"gcpRegion": "us-central1", "gcpZone": "us-central1-a"}

        variables = {
            "whereProject": {"id": project_id},
            "data": {
                "name": storage_name,
                "cloudProfileId": cloud_profile.id,
                "cloudProviderYodaConfig": {
                    "awsConfig": aws_config,
                    "azureConfig": azure_config,
                    "gcpConfig": gcp_config
                },
            },
        }
        r = requests.post(
            self.uri,
            json={"query": mutation, "variables": variables},
            headers=self.headers,
        )
        create_mutation_data = r.json()

        if "errors" in create_mutation_data:
            raise DeploifaiAPIError(create_mutation_data['errors'][0]['message'])

        return create_mutation_data["data"]["createDataStorage"]

    def get_cloud_profiles(self, workspace: str) -> typing.List[CloudProfile]:
        query = """
            query($whereAccount: AccountWhereUniqueInput!){
                cloudProfiles(whereAccount: $whereAccount){
                    id 
                    name 
                    provider
                } 
            }
        """

        variables = {"whereAccount": {"username": workspace}}

        r = requests.post(self.uri, json={"query": query, "variables": variables}, headers=self.headers)
        api_data = r.json()

        cloud_profiles_data = api_data["data"]["cloudProfiles"]

        cloud_profiles = list(
            map(
                lambda x: _parse_cloud_profile(
                    x, workspace
                ),
                cloud_profiles_data,
            )
        )

        return cloud_profiles

    def create_cloud_profile(self, provider, name, credentials, workspace: str, fragment):
        mutation = """
            mutation(
              $whereAccount: AccountWhereUniqueInput!
              $data: CloudProfileCreateInput!
            ) {
              createCloudProfile(whereAccount: $whereAccount, data: $data) {
                ...cloud_profile
              }
            }
        """

        variables = {
            "whereAccount": {"username": workspace},
            "data": {
                "name": name,
                "provider": provider.value,
            },
        }

        if provider.value == "AWS":
            variables["data"]["awsCredentials"] = credentials
        elif provider.value == "AZURE":
            variables["data"]["azureCredentials"] = credentials
        elif provider.value == "GCP":
            variables["data"]["gcpCredentials"] = credentials

        try:
            r = requests.post(
                self.uri,
                json={"query": mutation + fragment, "variables": variables},
                headers=self.headers,
            )

            create_mutation_data = r.json()

            return create_mutation_data["data"]["createCloudProfile"]["id"]
        except TypeError:
            raise DeploifaiAPIError("Could not create cloud profile. Please try again.")
        except KeyError:
            raise DeploifaiAPIError("Could not create cloud profile. Please try again.")

    def get_projects(self, workspace: str, fragment: str, where_project=None):
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
                "whereAccount": {"username": workspace},
                "whereProject": where_project,
            }
        else:
            variables = {"whereAccount": {"username": workspace}}

        try:
            r = requests.post(
                self.uri,
                json={"query": query, "variables": variables},
                headers=self.headers,
            )
            api_data = r.json()

            return api_data["data"]["projects"]
        except TypeError:
            raise DeploifaiAPIError("Could not get projects. Please try again.")
        except KeyError:
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
        except TypeError:
            raise DeploifaiAPIError("Could not get project. Please try again.")
        except KeyError:
            raise DeploifaiAPIError("Could not get project. Please try again.")

    def create_project(self, project_name: str, cloud_profile: CloudProfile, fragment: str):
        mutation = """
    mutation(
      $whereAccount: AccountWhereUniqueInput!
      $data: CreateProjectInput!
    ) {
      createProject(whereAccount: $whereAccount, data: $data) {
        ...project
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
                json={"query": mutation + fragment, "variables": variables},
                headers=self.headers,
            )

            create_mutation_data = r.json()

            return create_mutation_data["data"]["createProject"]
        except TypeError:
            raise DeploifaiAPIError("Could not create project. Please try again.")
        except KeyError:
            raise DeploifaiAPIError("Could not create project. Please try again.")

    def get_training_infrastructure_plans(self, uses_gpu: bool, cloud_provider: CloudProfile):
        query = (
            """
            query($usesGpu: Boolean $whereProvider: CloudProvider){
            trainingInfrastructurePlans(usesGpu: $usesGpu provider: $whereProvider){
                plan
                config{
                  ... on AWSFalconDefaultConfig{
                    ec2InstanceType
                  }
                  ... on AzureFalconDefaultConfig{
                    vmSize
                  }
                  ... on GCPFalconDefaultConfig{
                    computeMachineType
                  }
                }
              }
            }
            """
        )
        variables = {
            "usesGpu": uses_gpu,
            "whereProvider": cloud_provider
        }

        try:
            r = requests.post(
                self.uri,
                json={"query": query, "variables": variables},
                headers=self.headers,
            )
            api_data = r.json()

            return api_data["data"]["trainingInfrastructurePlans"]
        except TypeError:
            raise DeploifaiAPIError("Could not get information. Please try again.")
        except KeyError:
            raise DeploifaiAPIError("Could not get information. Please try again.")

    def falcon_ml_config(self, variable):
        query = (
            """    
            query ($where: FalconMLConfigWhereInput)
                {
                    falconMLConfigs(where: $where){
                        id
                        pythonVersion
                        frameworkVersion
                        cudaVersion
                        cudnnVersion
                    }
                }
            """
        )
        variables = {
            "where": variable
        }

        try:
            r = requests.post(
                self.uri,
                json={"query": query, "variables": variables},
                headers=self.headers,
            )
            api_data = r.json()

            return api_data["data"]["falconMLConfigs"]
        except TypeError:
            raise DeploifaiAPIError("Could not get ML Configs. Please try again.")
        except KeyError:
            raise DeploifaiAPIError("Could not get ML Configs. Please try again.")

    def falcon_ml_config_distinct(self, variable, distinct_option: str):
        query = (
            """    
            query ($where: FalconMLConfigWhereInput $distinct: [FalconMLConfigScalarFieldEnum!])
                {
                    falconMLConfigs(where: $where distinct: $distinct){
                        id
                        pythonVersion
                        frameworkVersion
                        cudaVersion
                        cudnnVersion
                    }
                }
            """
        )
        variables = {
            "where": variable,
            "distinct": [distinct_option],
        }

        try:
            r = requests.post(
                self.uri,
                json={"query": query, "variables": variables},
                headers=self.headers,
            )
            api_data = r.json()

            return api_data["data"]["falconMLConfigs"]
        except TypeError:
            raise DeploifaiAPIError("Could not get ML Configs. Please try again.")
        except KeyError:
            raise DeploifaiAPIError("Could not get ML Configs. Please try again.")

    def create_training_server(self, name: str, project_id: str, cloud_profile_id: str,
                               falcon_plan: str, uses_gpu: bool,
                               data_storage_ids: typing.List[str] = None, falcon_ml_config_id: str = None):
        mutation = """
        mutation($whereProject: ProjectWhereUniqueInput! $data: CreateTrainingInput!){
            createTraining(whereProject: $whereProject data: $data){
            name
            status
            }
        }
        """

        variables = {
            "whereProject": {"id": project_id},
            "data": {
                "name": name,
                "cloudProfileId": cloud_profile_id,
                "cloudProviderFalconConfig": {
                    "plan": falcon_plan,
                    "usesGpu": uses_gpu,
                },
                "falconMLConfigId": falcon_ml_config_id,
                "dataStorageIds": data_storage_ids,
            },
        }

        try:
            r = requests.post(
                self.uri,
                json={"query": mutation, "variables": variables},
                headers=self.headers,
            )

            create_mutation_data = r.json()

            return create_mutation_data["data"]["createTraining"]
        except TypeError:
            raise DeploifaiAPIError("Could not create Training Server. Please try again.")
        except KeyError:
            raise DeploifaiAPIError("Could not create Training Server. Please try again.")

    def get_training_servers(self, workspace: str, where_training: dict = None):
        query = """
        query ($whereAccount: AccountWhereUniqueInput! $whereTraining: TrainingWhereInput){
          trainings(whereAccount: $whereAccount whereTraining: $whereTraining){
            id
            name
            status
            state
          }
        }
        """

        variables = {
            "whereAccount": {"username": workspace},
            "whereTraining": where_training,
        }

        try:
            r = requests.post(
                self.uri,
                json={"query": query, "variables": variables},
                headers=self.headers,
            )
            server_info = r.json()

            if "errors" in server_info:
                raise DeploifaiAPIError(server_info['errors'][0]['message'])

            server_details = server_info["data"]["trainings"]

            return server_details

        except TypeError:
            raise DeploifaiAPIError("Could not find Training Server. Please try again.")
        except KeyError:
            raise DeploifaiAPIError("Could not find Training Server. Please try again.")

    def start_training_server(self, server_id: str):
        mutation = """
        mutation($where : TrainingWhereUniqueInput!){
            startTraining(where: $where){
                status state
            }
        }
        """

        variables = {"where": {"id": server_id}}

        try:
            r = requests.post(
                self.uri,
                json={"query": mutation, "variables": variables},
                headers=self.headers,
            )

            create_mutation_data = r.json()

            return create_mutation_data["data"]["startTraining"]
        except TypeError:
            raise DeploifaiAPIError("Could not start Training Server. Please try again.")
        except KeyError:
            raise DeploifaiAPIError("Could not start Training Server. Please try again.")

    def stop_training_server(self, server_id: str):
        mutation = """
        mutation($where : TrainingWhereUniqueInput!){
            stopTraining(where: $where){
                status state
            }
        }
        """

        variables = {"where": {"id": server_id}}

        try:
            r = requests.post(
                self.uri,
                json={"query": mutation, "variables": variables},
                headers=self.headers,
            )

            create_mutation_data = r.json()

            return create_mutation_data["data"]["stopTraining"]
        except TypeError:
            raise DeploifaiAPIError("Could not stop Training Server. Please try again.")
        except KeyError:
            raise DeploifaiAPIError("Could not stop Training Server. Please try again.")
