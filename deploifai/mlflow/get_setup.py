import click

from deploifai.context import pass_deploifai_context_obj, DeploifaiContextObj


@click.command('get-setup')
@pass_deploifai_context_obj
def get_setup(context: DeploifaiContextObj):
    # assume that the user should be in a project directory, that contains local configuration file
    if 'id' in context.local_config['PROJECT']:
        project_id = context.local_config['PROJECT']['id']
        fragment = """
                    fragment project on Project {
                        name
                        experiments{
                          name
                        }
                        account{
                            username
                        }
                    }
                    """

    else:
        click.secho("Please run code in project directory")
    pass
