import os
from dotenv import load_dotenv

load_dotenv()

cli_environment = os.environ.get("DEPLOIFAI_CLI_ENVIRONMENT", "production")
is_development_env = cli_environment == "development"

backend_url = os.environ.get("DEPLOIFAI_BACKEND_URL", "https://api.deploif.ai")
frontend_url = os.environ.get("DEPLOIFAI_FRONTEND_URL", "https://deploif.ai")
