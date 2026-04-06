"""
Configuration Module: Load environment variables, initialize LLM, setup logging.
Simple, clean setup with comprehensive error handling.
"""

import os
import sys
import logging
from pathlib import Path
from typing import Optional
from google.auth import default
from google.cloud import storage
# ==========================================
# LOGGING SETUP
# ==========================================
def setup_logging(log_file: str = "app.log", level: int = logging.INFO) -> logging.Logger:
    """
    Configure logging with console + file output.

    Args:
        log_file: Path to log file
        level: Logging level (INFO, DEBUG, ERROR, etc.)

    Returns:
        Configured logger instance
    """
    try:
        logger = logging.getLogger(__name__)
        logger.setLevel(level)

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)

        # File handler
        file_handler = logging.FileHandler(log_file, mode='a')
        file_handler.setLevel(level)

        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(name)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)

        # Add handlers
        if not logger.handlers:
            logger.addHandler(console_handler)
            logger.addHandler(file_handler)

        logger.info("✅ Logging initialized successfully")
        return logger

    except Exception as e:
        print(f"❌ Failed to setup logging: {e}")
        # Fallback to basic logging
        logging.basicConfig(level=level)
        return logging.getLogger(__name__)


# Initialize logger
logger = setup_logging()

# ==========================================
# ENVIRONMENT VARIABLES
# ==========================================
def load_environment_variables() -> dict:
    """
    Load and validate environment variables from .env file.

    Returns:
        Dictionary of loaded environment variables

    Raises:
        Logs warnings for missing keys
    """
    try:
        from dotenv import load_dotenv
        env_path = Path(__file__).parent.parent.parent / '.env'
        print(env_path)

        if not env_path.exists():
            logger.warning(f"⚠️ .env file not found at {env_path}")
        else:
            load_dotenv(env_path)
            logger.info(f"✅ Environment variables loaded from {env_path}")

    except ImportError:
        logger.warning("⚠️ python-dotenv not installed. Using system environment variables only.")
    except Exception as e:
        logger.error(f"❌ Error loading .env file: {e}")

    # Define required keys
    required_keys = {
        'GROQ_API_KEY': 'Groq LLM API key',
        'RAPIDAPI_KEY': 'Cricbuzz API key',
        'TAVILY_API_KEY': 'Tavily Search API key',
        'WEATHER_API_KEY': 'Visual Crossing Weather API key',
    }

    optional_keys = {
        'GOOGLE_API_KEY': 'Google Generative AI key (optional)',
    }

    env_vars = {}

    # Check required keys
    for key, description in required_keys.items():
        value = os.getenv(key)
        if value:
            env_vars[key] = value
            logger.info(f"✅ {key} loaded")
        else:
            logger.warning(f"⚠️ {key} not set ({description})")

    # Check optional keys
    for key, description in optional_keys.items():
        value = os.getenv(key)
        if value:
            env_vars[key] = value
            logger.info(f"✅ {key} loaded (optional)")

    return env_vars


# ==========================================
# LLM INITIALIZATION
# ==========================================
def initialize_llm(model_name: str = 'meta-llama/llama-4-scout-17b-16e-instruct',
                   model_provider: str = 'groq',
                   temperature: float = 0.8):
    """
    Initialize LangChain chat model.

    Args:
        model_name: Model identifier
        model_provider: Provider name (groq, google_genai, etc.)
        temperature: Model temperature (0.0-1.0)

    Returns:
        Initialized chat model or None if failed
    """
    try:
        from langchain.chat_models import init_chat_model

        model = init_chat_model(
            model=model_name,
            model_provider=model_provider,
            temperature=temperature
        )
        logger.info(f"✅ LLM initialized: {model_provider} / {model_name}")
        return model

    except ImportError as e:
        logger.error(f"❌ LangChain not installed: {e}")
        return None
    except Exception as e:
        logger.error(f"❌ Failed to initialize LLM: {e}")
        return None


# ==========================================
# API HEADERS
# ==========================================
def get_api_headers(rapidapi_key: Optional[str] = None) -> dict:
    """
    Build standard API headers for Cricbuzz requests.

    Args:
        rapidapi_key: RapidAPI key (uses env var if not provided)

    Returns:
        Dictionary of headers
    """
    if not rapidapi_key:
        rapidapi_key = os.getenv('RAPIDAPI_KEY', '')

    headers = {
        "x-rapidapi-key": rapidapi_key,
        "x-rapidapi-host": "cricbuzz-cricket.p.rapidapi.com"
    }

    if not rapidapi_key:
        logger.warning("⚠️ RAPIDAPI_KEY not set. API calls will fail.")

    return headers


# ==========================================
# CONFIGURATION OBJECT
# ==========================================
class Config:
    """Central configuration object."""

    def __init__(self):
        """Initialize all configuration."""
        try:
            # Load environment
            self.env_vars = load_environment_variables()

            # Setup API headers
            self.HEADERS = get_api_headers(self.env_vars.get('RAPIDAPI_KEY'))

            # Initialize LLM
            self.model = initialize_llm()
            self.model_validator = initialize_llm(model_name='openai/gpt-oss-120b')
            self.is_cloud=os.environ.get("PROD_RUN", "").lower() == "true"
            print(f"the cloid is {self.is_cloud}")

        # 2. Set Paths (Use /tmp in Cloud, current folder on Local)
            if self.is_cloud:
                self.CACHE_FILE = "/tmp/cricket_cache.json"
                self.BUCKET_NAME = "cricket_bucket_ak"
                self._download_from_gcs() # <--- Download at startup
            else:
                self.CACHE_FILE = "/mnt/c/workspaces/agent_project/src/tmp/cricket_cache.json"
             # 2. Set Paths (Use /tmp in Cloud, current folder on Local)


            # Cache files


            self.DAILY_MATCHES_FILE = "daily_matches.json"
            self.MATCH_HISTORY_FILE = "match_history.json"

            # Google Sheets configuration
            self.GOOGLE_SHEETS_ENABLED = False
            self.GOOGLE_SERVICE_ACCOUNT_FILE = "/mnt/c/workspaces/agent_project/src/credentials.json"
            self.GOOGLE_SPREADSHEET_NAME = "Cricket_Project_DB."
            self.spreadsheet = None  # Will be initialized if service account exists
            scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

            # Try to enable Google Sheets if service account file exists
            if Path(self.GOOGLE_SERVICE_ACCOUNT_FILE).exists():
                try:
                    print('inside the localfile')
                    import gspread
                    from oauth2client.service_account import ServiceAccountCredentials


                    creds = ServiceAccountCredentials.from_json_keyfile_name(
                        self.GOOGLE_SERVICE_ACCOUNT_FILE, scope
                    )
                    client = gspread.authorize(creds)
                    self.spreadsheet = client.open(self.GOOGLE_SPREADSHEET_NAME)
                    self.GOOGLE_SHEETS_ENABLED = True
                    logger.info(f"✅ Google Sheets initialized: {self.GOOGLE_SPREADSHEET_NAME}")
                except Exception as e:
                    logger.error(f"❌ Failed to initialize Google Sheets: {e}")
                    self.GOOGLE_SHEETS_ENABLED = False
                    self.spreadsheet = None
            else:
        # --- CLOUD MODE ---
                print("☁️ [CLOUD] No local key found. Connecting via Cloud Run Service Identity...")
                try:
                    import gspread
                    from oauth2client.service_account import ServiceAccountCredentials


                    creds, project = default(scopes=scope)
                    client= gspread.authorize(creds)
                    self.spreadsheet = client.open(self.GOOGLE_SPREADSHEET_NAME)
                    self.GOOGLE_SHEETS_ENABLED = True
                except Exception as e:
                    raise Exception(f"❌ Failed to connect to Google Sheets in any environment: {e}")

            # Logging
            self.logger = logger

            logger.info("✅ Configuration initialized successfully")

        except Exception as e:
            logger.error(f"❌ Failed to initialize configuration: {e}")
            raise


    def get_model(self):
        """The safe way to call for the model."""
        if not self.model:
            raise ValueError("❌ Config is not ready. Check your API Keys!")
        return self.model
    def get_model_validator(self):
        """The safe way to call for the model."""
        if not self.model_validator:
            raise ValueError("❌ Config is not ready. Check your API Keys!")
        return self.model_validator

    def _download_from_gcs(self):
        """Downloads the JSON from Google Cloud to /tmp folder."""
        try:
            client = storage.Client()
            bucket = client.bucket(self.BUCKET_NAME)
            blob = bucket.blob("cricket_cache.json")
            if blob.exists():
                blob.download_to_filename(self.CACHE_FILE)
                print(f"📥 [CLOUD] Downloaded cache to {self.CACHE_FILE}")
        except Exception as e:
            print(f"⚠️ Could not download cache: {e}")

    def save_to_gcs(self):
        """Uploads the local /tmp file back to the Cloud Bucket."""
        print(f"the is cloud is {self.is_cloud}")
        if not self.is_cloud:
            print("💻 [LOCAL] Skipping GCS upload.")
            return

        try:
            client = storage.Client()
            bucket = client.bucket(self.BUCKET_NAME)
            blob = bucket.blob("cricket_cache.json")
            blob.upload_from_filename(self.CACHE_FILE)
            print("📤 [CLOUD] Uploaded updated cache to GCS.")
        except Exception as e:
            print(f"❌ Failed to upload cache: {e}")


# ==========================================
# GLOBAL CONFIGURATION INSTANCE
# ==========================================
try:
    config = Config()
    logger.info("✅ Global config instance created")
except Exception as e:
    logger.error(f"❌ Failed to create global config: {e}")
    config = None
