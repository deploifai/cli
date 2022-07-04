import click
import webbrowser
import requests

from deploifai.context import pass_deploifai_context_obj, DeploifaiContextObj


@click.command()
@pass_deploifai_context_obj
@click.option("--workspace", help="Workspace name", type=str)
@click.option("--project", help="Project name", type=str)
def browse(context: DeploifaiContextObj, project: str, workspace='unassigned'):
    """
    Command to open a project in the Web Browser
    """

    if workspace:
        if project:
            # query for list of projects to obtain project id
            fragment = """
                            fragment project on Project {
                                id name 
                            }
                            """
            projects = context.api.get_projects(workspace=workspace, fragment=fragment)

            # obtain project id using project name provided
            project_names = [project["name"] for project in projects]
            project_ids = [project["id"] for project in projects]
            temp = -1
            for i, x in enumerate(project_names):
                if x == project:
                    temp = i
            project_id = project_ids[temp]

        else:
            click.secho("Missing project name, use --project option to pass the name of the project", fg='yellow')
            return

    elif project:
        click.secho("Missing workspace name, use --workspace option...", fg='yellow')

    else:
        # assume that the user should be in a project directory, that contains local configuration file

        if 'id' in context.local_config['PROJECT']:
            project_id = context.local_config['PROJECT']['id']

            # query for workspace name from api
            fragment = """
                            fragment project on Project {
                                workspace 
                            }
                            """
            projects = context.api.get_workspace(project_id=project_id, fragment=fragment)
            project_workspace = [project["workspace"] for project in projects]
            workspace = project_workspace[0]

        else:
            click.secho("Missing workspace name and project name, use --work...")

    if workspace and project_id:
        # defining the url
        url = 'https://deploif.ai/dashboard/' + workspace + '/projects/' + project_id
        # checking if the url leads to a valid webpage
        response = requests.head(url)
        if response.status_code == 200:
            # opening the url in default browser
            webbrowser.open(url, new=2)
        else:
            click.secho("Invalid workspace or project name")

    click.echo("Browse a project")
