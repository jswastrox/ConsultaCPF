"""schema inicial: pessoas, consultas, pedidos

Revision ID: 0001
Revises:
Create Date: 2026-07-20

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "pessoas",
        sa.Column("cpf", sa.String(11), primary_key=True),
        sa.Column("nome_completo", sa.String(255)),
        sa.Column("data_nascimento", sa.String(10)),
        sa.Column("idade", sa.BigInteger),
        sa.Column("sexo", sa.String(20)),
        sa.Column("nome_mae", sa.String(255)),
        sa.Column("situacao_cadastral", sa.String(50)),
        sa.Column("telefones", sa.JSON),
        sa.Column("emails", sa.JSON),
        sa.Column("endereco_logradouro", sa.String(255)),
        sa.Column("endereco_numero", sa.String(20)),
        sa.Column("endereco_complemento", sa.String(255)),
        sa.Column("endereco_bairro", sa.String(120)),
        sa.Column("endereco_cep", sa.String(9)),
        sa.Column("endereco_municipio", sa.String(120)),
        sa.Column("endereco_uf", sa.String(2)),
        sa.Column("raw_json", sa.JSON),
        sa.Column("fonte", sa.String(50), nullable=False, server_default="mock"),
        sa.Column("criado_em", sa.DateTime, nullable=False),
        sa.Column("atualizado_em", sa.DateTime, nullable=False),
    )
    op.create_index("ix_pessoas_uf", "pessoas", ["endereco_uf"])
    op.create_index("ix_pessoas_municipio", "pessoas", ["endereco_municipio"])
    op.create_index("ix_pessoas_situacao_cadastral", "pessoas", ["situacao_cadastral"])

    op.create_table(
        "consultas",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("cpf", sa.String(11), nullable=False),
        sa.Column("ip", sa.String(64)),
        sa.Column("user_agent", sa.String(255)),
        sa.Column("criado_em", sa.DateTime, nullable=False),
    )
    op.create_index("ix_consultas_cpf", "consultas", ["cpf"])

    op.create_table(
        "pedidos",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("correlation_id", sa.String(64), nullable=False),
        sa.Column("cpf", sa.String(11), nullable=False),
        sa.Column("buyer_token", sa.String(64), nullable=False),
        sa.Column("valor_centavos", sa.BigInteger, nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("qrcode_image", sa.Text),
        sa.Column("brcode", sa.Text),
        sa.Column("criado_em", sa.DateTime, nullable=False),
        sa.Column("pago_em", sa.DateTime, nullable=True),
    )
    op.create_unique_constraint("uq_pedidos_correlation_id", "pedidos", ["correlation_id"])
    op.create_index("ix_pedidos_cpf", "pedidos", ["cpf"])
    op.create_index("ix_pedidos_buyer_token", "pedidos", ["buyer_token"])
    op.create_index("ix_pedidos_buyer_cpf", "pedidos", ["buyer_token", "cpf"])


def downgrade() -> None:
    op.drop_table("pedidos")
    op.drop_table("consultas")
    op.drop_table("pessoas")
