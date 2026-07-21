import uuid
from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    BigInteger,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

PAPEL_ADMIN = "admin"
PAPEL_FUNCIONARIO = "funcionario"
PAPEL_CLIENTE = "cliente"

PACOTE_BASICO = "basico"
PACOTE_COMPLETA = "completa"
PACOTE_DETALHADA = "detalhada"
ORDEM_PACOTES = (PACOTE_BASICO, PACOTE_COMPLETA, PACOTE_DETALHADA)


class Pessoa(Base):
    """Cache local dos dados de CPF consultados no provedor externo.

    Enquanto nenhuma API real de dados é configurada (ver `cpf_provider` em
    Settings), este cache é preenchido pelo `MockCPFProvider` com dados de
    demonstração — nunca dados reais de terceiros.
    """

    __tablename__ = "pessoas"

    cpf: Mapped[str] = mapped_column(String(11), primary_key=True)
    nome_completo: Mapped[str | None] = mapped_column(String(255))
    data_nascimento: Mapped[str | None] = mapped_column(String(10))
    idade: Mapped[int | None] = mapped_column(BigInteger)
    sexo: Mapped[str | None] = mapped_column(String(20))
    nome_mae: Mapped[str | None] = mapped_column(String(255))
    situacao_cadastral: Mapped[str | None] = mapped_column(String(50))

    telefones: Mapped[list | None] = mapped_column(JSON)
    emails: Mapped[list | None] = mapped_column(JSON)

    endereco_logradouro: Mapped[str | None] = mapped_column(String(255))
    endereco_numero: Mapped[str | None] = mapped_column(String(20))
    endereco_complemento: Mapped[str | None] = mapped_column(String(255))
    endereco_bairro: Mapped[str | None] = mapped_column(String(120))
    endereco_cep: Mapped[str | None] = mapped_column(String(9))
    endereco_municipio: Mapped[str | None] = mapped_column(String(120))
    endereco_uf: Mapped[str | None] = mapped_column(String(2))

    # Pacote "completa"
    estado_civil: Mapped[str | None] = mapped_column(String(30))
    rg: Mapped[str | None] = mapped_column(String(20))
    profissao: Mapped[str | None] = mapped_column(String(120))
    salario_estimado: Mapped[float | None] = mapped_column(Numeric(10, 2))
    exposta_politicamente: Mapped[bool | None] = mapped_column(Boolean)

    # Pacote "detalhada"
    obito: Mapped[bool | None] = mapped_column(Boolean)
    aposentado: Mapped[bool | None] = mapped_column(Boolean)
    locais_trabalho: Mapped[list | None] = mapped_column(JSON)
    empresas_envolvidas: Mapped[list | None] = mapped_column(JSON)
    veiculos: Mapped[list | None] = mapped_column(JSON)
    parentes: Mapped[list | None] = mapped_column(JSON)
    beneficios: Mapped[list | None] = mapped_column(JSON)

    raw_json: Mapped[dict | None] = mapped_column(JSON)
    fonte: Mapped[str] = mapped_column(String(50), default="mock")

    criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    __table_args__ = (
        Index("ix_pessoas_uf", "endereco_uf"),
        Index("ix_pessoas_municipio", "endereco_municipio"),
        Index("ix_pessoas_situacao_cadastral", "situacao_cadastral"),
    )


class Consulta(Base):
    """Log simples de consultas, para métricas e limitação de uso."""

    __tablename__ = "consultas"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    cpf: Mapped[str] = mapped_column(String(11), index=True)
    ip: Mapped[str | None] = mapped_column(String(64))
    user_agent: Mapped[str | None] = mapped_column(String(255))
    usuario_id: Mapped[int | None] = mapped_column(
        ForeignKey("usuarios.id"), nullable=True, index=True
    )
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Pedido(Base):
    """Cobrança Pix (Woovi) para desbloqueio do resultado completo de um CPF."""

    __tablename__ = "pedidos"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    correlation_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    cpf: Mapped[str] = mapped_column(String(11), index=True)
    buyer_token: Mapped[str] = mapped_column(String(64), index=True)
    usuario_id: Mapped[int | None] = mapped_column(
        ForeignKey("usuarios.id"), nullable=True, index=True
    )

    valor_centavos: Mapped[int] = mapped_column(BigInteger)
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending|paid|expired|failed
    pacote: Mapped[str] = mapped_column(String(20), default=PACOTE_BASICO)  # basico|completa|detalhada

    qrcode_image: Mapped[str | None] = mapped_column(Text)
    brcode: Mapped[str | None] = mapped_column(Text)

    criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    pago_em: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    __table_args__ = (Index("ix_pedidos_buyer_cpf", "buyer_token", "cpf"),)


class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    senha_hash: Mapped[str] = mapped_column(String(255))
    telefone: Mapped[str | None] = mapped_column(String(30))
    papel: Mapped[str] = mapped_column(String(20), default=PAPEL_CLIENTE)  # admin|funcionario|cliente
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)

    criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    sessoes: Mapped[list["Sessao"]] = relationship(
        back_populates="usuario", cascade="all, delete-orphan"
    )

    @property
    def is_admin(self) -> bool:
        return self.papel == PAPEL_ADMIN

    @property
    def is_funcionario(self) -> bool:
        return self.papel == PAPEL_FUNCIONARIO

    @property
    def is_staff(self) -> bool:
        return self.papel in (PAPEL_ADMIN, PAPEL_FUNCIONARIO)


class Sessao(Base):
    """Sessão de login (token opaco), análoga à tabela `sessions` do Consultar Motorista."""

    __tablename__ = "sessoes"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), index=True)
    token: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    manter_conectado: Mapped[bool] = mapped_column(Boolean, default=True)
    expira_em: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    usuario: Mapped["Usuario"] = relationship(back_populates="sessoes")


class MensagemContato(Base):
    """Mensagens enviadas pelo formulário de e-mail da página /contato."""

    __tablename__ = "mensagens_contato"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    motivo: Mapped[str] = mapped_column(String(30))
    nome: Mapped[str] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(255))
    telefone: Mapped[str] = mapped_column(String(20))
    mensagem: Mapped[str] = mapped_column(Text)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Configuracao(Base):
    """Configurações da área administrativa (Alertas, Marketing, Financeiro), chave/valor."""

    __tablename__ = "configuracoes"

    chave: Mapped[str] = mapped_column(String(100), primary_key=True)
    valor: Mapped[str | None] = mapped_column(Text)
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
