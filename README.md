# ConsultaCPF

Plataforma de consulta de dados associados a um CPF, com prévia gratuita e
resultado completo liberado via Pix. Reconstrução moderna do funil de
"prévia → pagamento → resultado" (inspirado em sites como o Detetive
Online), com back-office de administrador/funcionário/usuário nos mesmos
moldes do Consultar Motorista.

## Stack

- Backend: **Python** (FastAPI) + SQLAlchemy 2.0 + Alembic
- Frontend: **HTML/CSS** server-renderizado via Jinja2, JS vanilla só no
  checkout Pix (sem framework de frontend)
- Banco de dados: **PostgreSQL** (Neon em produção)
- Pagamentos: **Pix via Woovi/OpenPix**

## Importante: modo demonstração

Ainda não há uma API real de dados de CPF configurada. Enquanto
`CPF_PROVIDER=mock` (padrão), toda consulta retorna uma **pessoa fictícia
determinística** gerada a partir do CPF informado (`app/services/cpf_provider.py`,
`MockCPFProvider`) — nunca dados reais de terceiros. A UI mostra um aviso de
"modo demonstração" enquanto isso.

Quando uma fonte de dados real for definida, implemente
`CPFProvider.buscar()` (veja `HttpCPFProvider` como esqueleto de adapter
HTTP genérico) e mude `CPF_PROVIDER=http` + `CPF_PROVIDER_BASE_URL` +
`CPF_PROVIDER_API_KEY` no `.env`. Nenhuma outra parte do app precisa mudar.

## Papéis e áreas

Mesmo modelo de autenticação e áreas do Consultar Motorista, adaptado para
um app renderizado no servidor: sessão por cookie httpOnly (não localStorage),
papéis `cliente` / `funcionario` / `admin` em `Usuario.papel`.

- **Área do usuário** (`/area-usuario`): histórico de consultas e pagamentos.
- **Área do funcionário** (`/area-funcionario`): busca de clientes; suas
  próprias consultas são liberadas sem custo.
- **Área do administrador** (`/area-admin`): abas Controle e Finanças,
  Operação, Alertas, Marketing, Configurações e Controle de Usuários
  (promover/rebaixar papel).

`ADMIN_EMAIL` no `.env` promove automaticamente a `admin` qualquer conta
que faça login/cadastro com aquele e-mail (sem precisar editar o banco
manualmente para criar o primeiro admin).

## Decisões de escopo (não redecidir sem confirmar com o usuário)

- **MVP = busca por CPF apenas.** O site de referência também busca por
  telefone/nome/e-mail/endereço/CNPJ, mas isso ficou fora do MVP (mesmo
  padrão adotado no projeto irmão ConsultaCNPJ).
- **Sem carteira de créditos.** Cada consulta é paga individualmente via
  Pix (como no ConsultaCNPJ), não via saldo pré-pago como no Consultar
  Motorista — só a estrutura de papéis/áreas foi replicada, não o modelo
  de monetização.
- **Páginas de resultado de CPF nunca são indexadas** (`noindex` +
  `Disallow: /cpf/` no robots.txt, fora do sitemap): diferente de CNPJ
  (entidade pública), CPF é dado pessoal de terceiro.

## Rodando localmente

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

O `.env` (não versionado) já aponta para o banco Neon deste projeto.
