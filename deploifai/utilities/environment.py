import os

cli_environment = os.environ.get("DEPLOIFAI_CLI_ENVIRONMENT", "production")
is_development_env = cli_environment == "development"

backend_url = os.environ.get("DEPLOIFAI_BACKEND_URL", "https://api.deploif.ai")
