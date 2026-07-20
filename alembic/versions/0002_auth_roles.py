"""usuarios, sessoes, configuracoes + usuario_id em pedidos/consultas

Revision ID: 0002
Revises: 0001
Create Date: 2026-07-20

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "usuarios",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("nome", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("senha_hash", sa.String(255), nullable=False),
        sa.Column("telefone", sa.String(30)),
        sa.Column("papel", sa.String(20), nullable=False, server_default="cliente"),
        sa.Column("ativo", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("criado_em", sa.DateTime, nullable=False),
    )
    op.create_unique_constraint("uq_usuarios_email", "usuarios", ["email"])
    op.create_index("ix_usuarios_email", "usuarios", ["email"])

    op.create_table(
        "sessoes",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("usuario_id", sa.BigInteger, sa.ForeignKey("usuarios.id"), nullable=False),
        sa.Column("token", sa.String(64), nullable=False),
        sa.Column("manter_conectado", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("expira_em", sa.DateTime, nullable=True),
        sa.Column("criado_em", sa.DateTime, nullable=False),
    )
    op.create_unique_constraint("uq_sessoes_token", "sessoes", ["token"])
    op.create_index("ix_sessoes_token", "sessoes", ["token"])
    op.create_index("ix_sessoes_usuario_id", "sessoes", ["usuario_id"])

    op.create_table(
        "configuracoes",
        sa.Column("chave", sa.String(100), primary_key=True),
        sa.Column("valor", sa.Text),
        sa.Column("atualizado_em", sa.DateTime, nullable=False),
    )

    op.add_column("consultas", sa.Column("usuario_id", sa.BigInteger, sa.ForeignKey("usuarios.id"), nullable=True))
    op.create_index("ix_consultas_usuario_id", "consultas", ["usuario_id"])

    op.add_column("pedidos", sa.Column("usuario_id", sa.BigInteger, sa.ForeignKey("usuarios.id"), nullable=True))
    op.create_index("ix_pedidos_usuario_id", "pedidos", ["usuario_id"])


def downgrade() -> None:
    op.drop_index("ix_pedidos_usuario_id", table_name="pedidos")
    op.drop_column("pedidos", "usuario_id")

    op.drop_index("ix_consultas_usuario_id", table_name="consultas")
    op.drop_column("consultas", "usuario_id")

    op.drop_table("configuracoes")

    op.drop_index("ix_sessoes_usuario_id", table_name="sessoes")
    op.drop_index("ix_sessoes_token", table_name="sessoes")
    op.drop_table("sessoes")

    op.drop_index("ix_usuarios_email", table_name="usuarios")
    op.drop_table("usuarios")
