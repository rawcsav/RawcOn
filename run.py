import os
from dotenv import load_dotenv


dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

from app import create_app, csrf
from flask import jsonify

app = create_app()

from app.util.celery_util import make_celery

celery = make_celery(app)

if os.getenv("FLASK_ENV") == "development":

    @app.route("/trigger/update-stale-user-data", methods=["POST"])
    @csrf.exempt
    def trigger_update_stale_user_data():
        celery.send_task("tasks.update_stale_user_data")
        return jsonify({"message": "Task update_stale_user_data triggered successfully"}), 202

    @app.route("/trigger/delete-inactive-users", methods=["POST"])
    @csrf.exempt
    def trigger_delete_inactive_users():
        celery.send_task("tasks.delete_inactive_users")
        return jsonify({"message": "Task delete_inactive_users triggered successfully"}), 202


if __name__ == "__main__":
    app.run(port=8081, host="127.0.0.1")
