from .environment import frontend_url


def get_dashboard_route(workspace: str) -> str:
    return f"{frontend_url}/dashboard/{workspace}"


def get_project_route(workspace: str, project_name: str) -> str:
    return f"{get_dashboard_route(workspace)}/projects/{project_name}"


def get_dataset_route(workspace: str, project_name: str, dataset_id: str) -> str:
    return f"{get_project_route(workspace, project_name)}/datasets/{dataset_id}"
