import os
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

from app import create_app

app = create_app()

from app.util.database_util import initialize_genre_data

initialize_genre_data(app)

if __name__ == "__main__":
    app.run(port=8081, host="0.0.0.0")
