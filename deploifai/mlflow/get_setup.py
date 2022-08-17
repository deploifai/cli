from enum import Enum

import click
import pyperclip
from PyInquirer import prompt

from deploifai.context import pass_deploifai_context_obj, DeploifaiContextObj, is_authenticated, project_found


class Environment(Enum):
    # Experiment Environment, DEPLOIFAI means usage of a managed runner, EXTERNAL means lack of a managed runner
    DEPLOIFAI = 'DEPLOIFAI'
    EXTERNAL = 'EXTERNAL'


@click.command('get-setup')
@click.option("--external", is_flag=True, help="Use mlflow integration outside of Deploifai managed runner")
@pass_deploifai_context_obj
@is_authenticated
@project_found
def get_setup(context: DeploifaiContextObj, external):
    """
    Get setup to integrate mlflow in training scripts
    """

    # assume that the user should be in a project directory, that contains local configuration file
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
                        resourceAccessToken {
                            token
                        }
                    } 
                }
                """
    context.debug_msg(project_id)
    project_data = context.api.get_project(project_id=project_id, fragment=fragment)
    project_name = project_data["name"]
    workspace_name = project_data["account"]["username"]
    experiment_data = project_data["experiments"]

    click.secho("Workspace: {}".format(workspace_name), fg='blue')
    click.secho("Project: {}<{}>".format(project_name, project_id), fg='blue')

    # selecting experiment name from the options
    if len(experiment_data) == 0:
        click.secho("No experiments exist for the project", fg='yellow')
        return
    else:
        choose_experiment = prompt(
            {
                "type": "list",
                "name": "experiment",
                "message": "Choose a experiment",
                "choices": [
                    {
                        "name": "{}".format(experiment_data["name"]),
                        "value": experiment_data
                    }
                    for experiment_data in experiment_data
                ],
            }
        )
        if choose_experiment == {}:
            raise click.Abort()
        experiment = choose_experiment["experiment"]

    experiment_name = experiment["name"]
    experiment_environment = experiment["environment"]
    experiment_token = experiment["resourceAccessToken"]['token']

    click.secho("Experiment: {}".format(experiment_name), fg='blue')

    link = f"{workspace_name}/{project_name}/{experiment_name}"
    line4 = "# setup mlflow for this experiment\n"
    line5 = "mlflow.set_tracking_uri('https://community.mlflow.deploif.ai')\n"
    line6 = 'mlflow.set_experiment("{}")\n'.format(link)

    if external or experiment_environment == Environment.EXTERNAL.value:

        line1 = "# only if running an experiment outside deploifai (this must come before setting mlflow tracking uri and experiment)\n"
        line2 = 'os.environ["MLFLOW_TRACKING_USERNAME"] = "{}" \n'.format(link)
        line3 = 'os.environ["MLFLOW_TRACKING_PASSWORD"] = "{}" \n'.format(experiment_token)
        required_code: str = line1 + line2 + line3 + line4 + line5 + line6

    else:
        required_code: str = line4 + line5 + line6

    click.secho("The following code snippet needs to be added after importing mlflow", fg='green')
    click.secho(required_code)
    pyperclip.copy(required_code)
    click.secho("It has also been copied to your clipboard", fg='green')
