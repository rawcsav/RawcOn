import logging
import os
import smtplib
from email.message import EmailMessage
from logging.handlers import RotatingFileHandler
from typing import Optional


class AppLogger:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "initialized"):
            self.initialized = True
            self.log_dir = "logs"
            self.admin_email = os.getenv("ADMIN_EMAIL")
            self.email_password = os.getenv("EMAIL_PASSWORD")  # Gmail App Password
            self.setup_logging()

    def setup_logging(self):
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)

        standard_formatter = logging.Formatter("%(asctime)s | %(levelname)-8s | %(name)s | %(message)s")

        error_formatter = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s | %(pathname)s:%(lineno)d"
        )

        standard_handler = RotatingFileHandler(
            os.path.join(self.log_dir, "app.log"), maxBytes=10_485_760, backupCount=5, encoding="utf-8"  # 10MB
        )
        standard_handler.setLevel(logging.INFO)
        standard_handler.setFormatter(standard_formatter)

        error_handler = RotatingFileHandler(
            os.path.join(self.log_dir, "error.log"), maxBytes=10_485_760, backupCount=5, encoding="utf-8"  # 10MB
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(error_formatter)

        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(standard_formatter)

        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)

        root_logger.handlers.clear()

        root_logger.addHandler(standard_handler)
        root_logger.addHandler(error_handler)
        root_logger.addHandler(console_handler)

    def send_error_email(self, subject: str, error_message: str):
        if not all([self.admin_email, self.email_password]):
            return

        try:
            msg = EmailMessage()
            msg.set_content(error_message)
            msg["Subject"] = f"RawcOn Error: {subject}"
            msg["From"] = self.admin_email
            msg["To"] = self.admin_email

            with smtplib.SMTP("smtp.gmail.com", 587) as server:
                server.starttls()
                server.login(self.admin_email, self.email_password)
                server.send_message(msg)

        except Exception as e:
            logging.error(f"Failed to send error email: {str(e)}")

    @staticmethod
    def get_logger(name: Optional[str] = None) -> logging.Logger:
        """Get a logger instance"""
        AppLogger()  # Ensure logging is configured
        return logging.getLogger(name)


def get_logger(name: Optional[str] = None) -> logging.Logger:
    return AppLogger.get_logger(name)


# Email notification helper function
def notify_error(subject: str, error_message: str):
    AppLogger().send_error_email(subject, error_message)
