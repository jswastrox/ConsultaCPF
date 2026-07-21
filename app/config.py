from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_FILE = Path(__file__).resolve().parent.parent / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILE, extra="ignore")

    database_url: str = "postgresql+psycopg://user:password@localhost/consultacpf"

    # Provedor de dados de CPF (adapter plugável). "mock" gera dados de
    # demonstração localmente — não há API real configurada ainda.
    cpf_provider: str = "mock"
    cpf_provider_base_url: str = ""
    cpf_provider_api_key: str = ""
    cpf_cache_ttl_dias: int = 30

    woovi_app_id: str = ""
    woovi_base_url: str = "https://api.woovi.com"
    woovi_webhook_secret: str = ""

    secret_key: str = "troque-esta-chave-em-producao"
    site_name: str = "ConsultaCPF"
    site_url: str = "http://localhost:8000"
    report_price_cents: int = 2990
    report_price_completa_cents: int = 4990
    report_price_detalhada_cents: int = 7990
    environment: str = "development"

    admin_email: str = ""
    """E-mail que é automaticamente promovido a role=admin ao logar/cadastrar."""

    contact_email: str = "atende@consultasagora.com.br"
    contact_whatsapp: str = "5532999764443"
    contact_phone_display: str = "(32) 99976-4443"

    rate_limit_consultas_por_janela: int = 20
    rate_limit_janela_minutos: int = 10


@lru_cache
def get_settings() -> Settings:
    return Settings()
