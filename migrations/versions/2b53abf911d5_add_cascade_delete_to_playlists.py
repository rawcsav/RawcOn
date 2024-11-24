"""Add cascade delete to playlists

Revision ID: 2b53abf911d5
Revises: 52e8cca91ea4
Create Date: 2024-11-24 04:05:13.456011

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2b53abf911d5'
down_revision = '52e8cca91ea4'
branch_labels = None
depends_on = None


def upgrade():
    # Drop the existing foreign key using its actual name
    op.drop_constraint('playlist_data_ibfk_1', 'playlist_data', type_='foreignkey')

    # Recreate the foreign key with ON DELETE CASCADE
    op.create_foreign_key(
        'playlist_data_ibfk_1',  # Use the same name as the existing foreign key
        'playlist_data',  # Child table
        'user_data',  # Parent table
        ['user_id'],  # Column in child table
        ['spotify_user_id'],  # Column in parent table
        ondelete='CASCADE'
    )

def downgrade():
    # Drop the foreign key with ON DELETE CASCADE
    op.drop_constraint('playlist_data_ibfk_1', 'playlist_data', type_='foreignkey')

    # Recreate the original foreign key without ON DELETE CASCADE
    op.create_foreign_key(
        'playlist_data_ibfk_1',  # Use the same name as the existing foreign key
        'playlist_data',  # Child table
        'user_data',  # Parent table
        ['user_id'],  # Column in child table
        ['spotify_user_id']  # Column in parent table
    )
