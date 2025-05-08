import os

from dotenv import load_dotenv


class Settings:
    def __init__(self):
        # Load environment variables from .env file
        load_dotenv()

        # API Keys
        self.DB_URL = os.getenv("DB_URL")
        self.AGENT_STUDIO_CHAT_URL = os.getenv("AGENT_STUDIO_CHAT_URL")
        self.LYZR_API_KEY = os.getenv("LYZR_API_KEY")

        self.TELEMETRY_AGENT_ID = os.getenv("TELEMETRY_AGENT_ID")
        self.TICKET_AGENT_ID = os.getenv("TICKET_AGENT_ID")
        self.TROUBLESHOOTING_AGENT_ID = os.getenv("TROUBLESHOOTING_AGENT_ID")
        self.OCR_AGENT_ID = os.getenv("OCR_AGENT_ID")
        self.KG_AGENT = os.getenv("KG_AGENT")
        self.CORROSION_AGENT_ID = os.getenv("CORROSION_AGENT_ID")
        self.MANAGER_AGENT_ID = os.getenv("MANAGER_AGENT_ID")
        self.OCR_ENDPOINT = os.getenv("OCR_ENDPOINT")
        self.FEEDBACK_RAG_ID = os.getenv("FEEDBACK_RAG_ID")
        self.AGENT_LEARNING_FEEDBACK_URL = os.getenv("AGENT_LEARNING_FEEDBACK_URL")

    def __getattr__(self, name):
        """Return None if attribute doesn't exist"""
        return None


settings = Settings()
