"""mensagens_contato (formulario da pagina /contato)

Revision ID: 0003
Revises: 0002
Create Date: 2026-07-20

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "mensagens_contato",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("motivo", sa.String(30), nullable=False),
        sa.Column("nome", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("telefone", sa.String(20), nullable=False),
        sa.Column("mensagem", sa.Text, nullable=False),
        sa.Column("criado_em", sa.DateTime, nullable=False),
    )


def downgrade() -> None:
    op.drop_table("mensagens_contato")
