import click
import pyperclip

from deploifai.api import DeploifaiAPIError
from deploifai.context import pass_deploifai_context_obj, DeploifaiContextObj
from PyInquirer import prompt


@click.command('get-setup')
@click.option("--external", is_flag=True, help="Use code externally")
@pass_deploifai_context_obj
def get_setup(context: DeploifaiContextObj, external):
    """
    Command to obtain code for mlflow integration
    """

    # assume that the user should be in a project directory, that contains local configuration file
    if 'id' in context.local_config['PROJECT']:
        project_id = context.local_config['PROJECT']['id']
        # getting all the required information to provide the code
        fragment = """
                    fragment project on Project {
                        name
                        account{
                            username
                        }
                        experiments{
                          name
                          environment
                          resourceAccessTokenString
                        }
                        
                    }
                    """
        project_data = context.api.get_project(
            project_id=project_id, fragment=fragment
        )
        project_name = project_data["name"]
        workspace_name = project_data["account"]["username"]
        experiment_data = project_data["experiment"]
        experiment_names = [experiment["name"] for experiment in experiment_data]
        experiment_environments = [experiment["environment"] for experiment in experiment_data]
        experiment_tokens = [experiment["resourceAccessTokenString"] for experiment in experiment_data]

        # selecting experiment name from the options
        if len(experiment_names) == 0:
            click.secho("No experiments exist for the project")
        # elif len(experiment_names) == 1:
        # experiment_name = experiment_names[0]
        else:
            choose_experiment = prompt(
                {
                    "type": "list",
                    "name": "experiment",
                    "message": "Choose a experiment",
                    "choices": [
                        exp for exp in experiment_names
                    ],
                }
            )
            if choose_experiment == {}:
                raise click.Abort()
            experiment_name = choose_experiment["experiment"]

        index = -1
        for i, x in enumerate(experiment_names):
            if x == experiment_name:
                index = i

        # selecting corresponding experiment environment and token
        experiment_environment = experiment_environments[index]
        experiment_token = experiment_tokens[index]

        link = f"{workspace_name}/{project_name}/{experiment_name}"
        line4 = "# setup mlflow for this experiment\n"
        line5 = "mlflow.set_tracking_uri('https://community.mlflow.deploif.ai')\n"
        line6 = 'mlflow.set_experiment("{}")\n'.format(link)
        if external or experiment_environment == "EXTERNAL":

            line1 = "# only if running an experiment outside deploifai (this must come before setting mlflow tracking uri and experiment)\n"
            line2 = 'os.environ["MLFLOW_TRACKING_USERNAME"] = {} \n'.format(link)
            line3 = 'os.environ["MLFLOW_TRACKING_PASSWORD"] = {} \n'.format(experiment_token)
            required_code: str = line1+line2+line3+line4+line5+line6

        else:
            required_code: str = line4+line5+line6

        click.secho("The following code needs to be added for mlflow integration", fg='green')
        click.secho(required_code)
        pyperclip.copy(required_code)
        click.secho("The code has been copied to your clipboard", fg='green')
    else:
        click.secho("Please run code in project directory")
