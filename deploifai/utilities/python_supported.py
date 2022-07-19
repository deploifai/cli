from deploifai.api import DeploifaiAPI


def supported(python_version: str):
    variable = {"pythonVersion": {"startsWith": python_version}}
    api = DeploifaiAPI()
    ml_config = api.falcon_ml_config(variable)
    if len(ml_config) == 0:
        python_supported = False
    else:
        python_supported = True

    return python_supported
