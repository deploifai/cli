import pathlib


def find_config_absolute_path(relative_filepath: pathlib.Path) -> pathlib.Path:
    """
    Traverse up the file system and checks if a file at the relative filepath exists.
    If it does not exist, return None.
    :return: if local config file exists, return pathlib.Path object that points to the config file
    """
    path = pathlib.Path.cwd()
    while not path.joinpath(relative_filepath).exists() and path != path.parent:
        path = path.parent

    if path == path.parent:
        return None

    return path.joinpath(relative_filepath)
