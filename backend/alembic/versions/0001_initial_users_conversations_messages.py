"""
Initial tables: users, conversations, messages (safe if-exists checks)
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

# revision identifiers, used by Alembic.
revision = '0001_initial'
down_revision = None
branch_labels = None
depends_on = None


def table_exists(conn, name: str) -> bool:
    insp = Inspector.from_engine(conn)
    return name in insp.get_table_names()


def upgrade() -> None:
    bind = op.get_bind()
    conn = bind.engine.connect()

    if not table_exists(conn, 'users'):
        op.create_table(
            'users',
            sa.Column('id', sa.String(), primary_key=True),
            sa.Column('email', sa.String(), nullable=False, unique=True, index=True),
            sa.Column('username', sa.String(), nullable=False),
            sa.Column('role', sa.String(), nullable=False, server_default='user'),
            sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('last_login', sa.DateTime(), nullable=True),
            sa.Column('subscription_tier', sa.String(), nullable=False, server_default='free'),
            sa.Column('usage_count', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('monthly_limit', sa.Integer(), nullable=False, server_default='100'),
            sa.Column('password_hash', sa.String(), nullable=False),
        )

    if not table_exists(conn, 'conversations'):
        op.create_table(
            'conversations',
            sa.Column('id', sa.String(), primary_key=True),
            sa.Column('user_id', sa.String(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
            sa.Column('title', sa.String(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
        )
        op.create_index('ix_conversations_user_updated', 'conversations', ['user_id', 'updated_at'])

    if not table_exists(conn, 'messages'):
        op.create_table(
            'messages',
            sa.Column('id', sa.String(), primary_key=True),
            sa.Column('conversation_id', sa.String(), sa.ForeignKey('conversations.id', ondelete='CASCADE'), nullable=False),
            sa.Column('user_id', sa.String(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
            sa.Column('role', sa.String(), nullable=False),
            sa.Column('content', sa.Text(), nullable=False),
            sa.Column('timestamp', sa.DateTime(), nullable=False),
        )
        op.create_index('ix_messages_conv_time', 'messages', ['conversation_id', 'timestamp'])


def downgrade() -> None:
    bind = op.get_bind()
    conn = bind.engine.connect()
    # Drop child tables first
    if table_exists(conn, 'messages'):
        op.drop_index('ix_messages_conv_time', table_name='messages')
        op.drop_table('messages')
    if table_exists(conn, 'conversations'):
        op.drop_index('ix_conversations_user_updated', table_name='conversations')
        op.drop_table('conversations')
    if table_exists(conn, 'users'):
        op.drop_table('users')

