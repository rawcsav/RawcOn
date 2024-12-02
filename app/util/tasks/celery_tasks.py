from datetime import datetime, timedelta

from celery import shared_task
from sqlalchemy import or_

from app.models.user_models import UserData
from app.util.logging_util import get_logger, notify_error
from app.util.tasks.tasks_util import make_session, init_session_client_for_celery, update_user_data

logger = get_logger(__name__)


@shared_task(name="tasks.update_stale_user_data")
def update_stale_user_data_task():
    db_session = make_session()
    try:
        now = datetime.utcnow()
        activity_threshold = now - timedelta(days=4)
        update_threshold = now - timedelta(days=7)  # Only update users once a week

        stale_users = (
            db_session.query(UserData)
            .filter(
                or_(UserData.last_active < activity_threshold, UserData.last_stale_update == None),
                or_(UserData.last_stale_update == None, UserData.last_stale_update < update_threshold),
            )
            .all()
        )

        updated_count = 0
        for user in stale_users:
            sp, error = init_session_client_for_celery(user.spotify_user_id)
            if error:
                logger.error(f"Failed to initialize Spotify client for user {user.spotify_user_id}: {error}")
                continue

            try:
                update_user_data(user, sp, db_session)
                user.last_stale_update = now  # Update the last_stale_update field
                updated_count += 1
            except Exception as e:
                logger.error(f"Error updating data for user {user.spotify_user_id}: {str(e)}")

        db_session.commit()
        logger.info(f"Successfully updated {updated_count} stale users")
        return f"Successfully updated {updated_count} stale users"
    except Exception as e:
        db_session.rollback()
        logger.error(f"Error updating stale user data: {str(e)}")
        return f"Error updating stale user data: {str(e)}"
    finally:
        db_session.remove()


@shared_task(name="tasks.delete_inactive_users")
def delete_inactive_users_task():
    db_session = make_session()
    try:
        threshold_date = datetime.utcnow() - timedelta(days=30)
        inactive_users = db_session.query(UserData).filter(UserData.last_active < threshold_date).all()

        deleted_count = 0
        for user in inactive_users:
            db_session.delete(user)
            deleted_count += 1

        db_session.commit()
        logger.info(f"Successfully deleted {deleted_count} inactive users")
        return f"Successfully deleted {deleted_count} inactive users"
    except Exception as e:
        db_session.rollback()
        logger.error(f"Error deleting inactive users: {str(e)}")
        return f"Error deleting inactive users: {str(e)}"
    finally:
        db_session.remove()


@shared_task(name="tasks.test_logging")
def test_logging_task():
    logger.info("Celery logging test - info message")
    logger.error("Celery logging test - error message")
    notify_error("Celery Test", "This is a test error from Celery task")
    return "Logging test complete"
