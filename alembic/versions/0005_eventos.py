"""tabela eventos_sistema (aba Operacao da area administrativa)

Revision ID: 0005
Revises: 0004
Create Date: 2026-07-21

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "eventos_sistema",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("tipo", sa.String(40), nullable=False),
        sa.Column("descricao", sa.String(255)),
        sa.Column("usuario_id", sa.BigInteger, sa.ForeignKey("usuarios.id"), nullable=True),
        sa.Column("ip", sa.String(64)),
        sa.Column("criado_em", sa.DateTime, nullable=False),
    )
    op.create_index("ix_eventos_sistema_tipo", "eventos_sistema", ["tipo"])
    op.create_index("ix_eventos_sistema_criado_em", "eventos_sistema", ["criado_em"])


def downgrade() -> None:
    op.drop_index("ix_eventos_sistema_criado_em", table_name="eventos_sistema")
    op.drop_index("ix_eventos_sistema_tipo", table_name="eventos_sistema")
    op.drop_table("eventos_sistema")
