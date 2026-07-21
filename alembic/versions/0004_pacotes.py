"""campos extras de pessoas (pacotes completa/detalhada) + pedidos.pacote

Revision ID: 0004
Revises: 0003
Create Date: 2026-07-20

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("pessoas", sa.Column("estado_civil", sa.String(30)))
    op.add_column("pessoas", sa.Column("rg", sa.String(20)))
    op.add_column("pessoas", sa.Column("profissao", sa.String(120)))
    op.add_column("pessoas", sa.Column("salario_estimado", sa.Numeric(10, 2)))
    op.add_column("pessoas", sa.Column("exposta_politicamente", sa.Boolean))
    op.add_column("pessoas", sa.Column("obito", sa.Boolean))
    op.add_column("pessoas", sa.Column("aposentado", sa.Boolean))
    op.add_column("pessoas", sa.Column("locais_trabalho", sa.JSON))
    op.add_column("pessoas", sa.Column("empresas_envolvidas", sa.JSON))
    op.add_column("pessoas", sa.Column("veiculos", sa.JSON))
    op.add_column("pessoas", sa.Column("parentes", sa.JSON))
    op.add_column("pessoas", sa.Column("beneficios", sa.JSON))

    op.add_column(
        "pedidos",
        sa.Column("pacote", sa.String(20), nullable=False, server_default="basico"),
    )


def downgrade() -> None:
    op.drop_column("pedidos", "pacote")

    op.drop_column("pessoas", "beneficios")
    op.drop_column("pessoas", "parentes")
    op.drop_column("pessoas", "veiculos")
    op.drop_column("pessoas", "empresas_envolvidas")
    op.drop_column("pessoas", "locais_trabalho")
    op.drop_column("pessoas", "aposentado")
    op.drop_column("pessoas", "obito")
    op.drop_column("pessoas", "exposta_politicamente")
    op.drop_column("pessoas", "salario_estimado")
    op.drop_column("pessoas", "profissao")
    op.drop_column("pessoas", "rg")
    op.drop_column("pessoas", "estado_civil")
