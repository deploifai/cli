import keyring

SERVICE_NAME = "deploifai-cli"


def save_auth_token(username, token):
    keyring.set_password(SERVICE_NAME, username, token)


def get_auth_token(username):
    return keyring.get_password(SERVICE_NAME, username)


def delete_auth_token(username):
    keyring.delete_password(SERVICE_NAME, username)
