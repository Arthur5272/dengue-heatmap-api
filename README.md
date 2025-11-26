# 🦟 API de Monitoramento e Inteligência de Dengue

> **Data Lake e Dashboard de visualização de dados epidemiológicos em tempo real.**

Este projeto é uma API Backend robusta desenvolvida em **Python (FastAPI)** que coleta, processa e armazena dados epidemiológicos da Dengue no Brasil. Ele atua como uma camada de inteligência (Data Lake), consumindo dados da API oficial do **InfoDengue (Fiocruz/FGV)** e disponibilizando-os através de uma API performática e um Dashboard interativo de mapas de calor.

---

## 🚀 Funcionalidades Principais

* **ETL Automatizado:** Sincronização automática de dados epidemiológicos (Casos, Nível de Alerta, Rt) para todos os **5.570 municípios brasileiros**.
* **Alta Performance:** Utiliza **processamento assíncrono** e inserção em lotes (*Batch Upsert*) para lidar com milhões de registros históricos sem travar o banco.
* **Banco de Dados Temporal:** Histórico completo semanal (Semana Epidemiológica) persistido em PostgreSQL.
* **Dashboard Interativo:**
    * **Nível Nacional:** Mapa coroplético dos estados brasileiros.
    * **Nível Municipal (Drill-down):** Visualização granular por cidade (Demo implementada para **Pernambuco**).
* **API RESTful:** Endpoints flexíveis para consulta e filtragem de dados.

---

## 🛠️ Stack Tecnológica

* **Linguagem:** Python 3.10+
* **Framework Web:** FastAPI (ASGI)
* **Banco de Dados:** PostgreSQL 15 (via Docker)
* **ORM:** SQLAlchemy (Asyncio) + Alembic (Migrações)
* **Cliente HTTP:** HTTPX (Requisições assíncronas paralelas)
* **Agendamento:** APScheduler (Cron jobs)
* **Visualização:** Folium (Leaflet.js) + Pandas
* **Gerenciamento de Dependências:** Poetry

---

## ⚙️ Pré-requisitos

* Docker e Docker Compose
* Python 3.10 ou superior
* Poetry (Gerenciador de pacotes)

---

## 📦 Instalação e Configuração

### 1. Clone o repositório
```bash
git clone [https://github.com/seu-usuario/dengue-api.git](https://github.com/seu-usuario/dengue-api.git)
cd dengue-api
```

### 2. Configure as Variáveis de Ambiente

Copie o arquivo de exemplo e, se necessário, ajuste as credenciais do banco no arquivo `.env` gerado.

```bash
cp .env.example .env
```

### 3. Inicie o Banco de Dados

Suba o container do PostgreSQL via Docker.

```bash
docker-compose up -d
```

### 4. Instale as Dependências

```bash
poetry install
```

### 5. Execute as Migrações do Banco

Crie as tabelas no banco de dados.

```bash
poetry run alembic upgrade head
```

### 🌱 Carga de Dados (Seed & Backfill)

Antes de usar o dashboard, é necessário popular o banco de dados. Execute os scripts na ordem abaixo:

#### Passo 1: Popular Municípios (Territórios)

Baixa a lista oficial do IBGE e popula a tabela `territories`.

```bash
poetry run python src/app/scripts/seed_territories.py
```

#### Passo 2: Carga Histórica (Backfill)

Baixa os dados de dengue semanais dos últimos anos (2023 até o presente) para todas as cidades.

⚠️ **Atenção:** Este processo dispara milhares de requisições HTTP e pode levar alguns minutos.

```bash
poetry run python src/app/scripts/backfill_infodengue.py
```

---

## ▶️ Como Rodar

Inicie o servidor de desenvolvimento:

```bash
poetry run uvicorn src.app.main:app --reload
```

O servidor estará rodando em `http://127.0.0.1:8000`.

---

## 📊 Acessando o Projeto

### 🗺️ Dashboard Visual

Acesse o mapa interativo para visualizar a evolução da doença: 👉 `http://127.0.0.1:8000/api/v1/map/dashboard`

**Como usar:**

*   Selecione a **Semana Epidemiológica** desejada no canto superior direito.
*   Alterne entre a visão **Brasil (Estados)** e **Pernambuco (Cidades)** usando os botões no topo.

### 📑 Documentação da API (Swagger UI)

Explore e teste os endpoints disponíveis (JSON): 👉 `http://127.0.0.1:8000/docs`

---

## 📂 Estrutura do Projeto

```plaintext
dengue-api/
├── migrations/          # Scripts de migração do banco (Alembic)
├── src/
│   ├── app/
│   │   ├── api/         # Endpoints (Routes) da API
│   │   ├── core/        # Configurações e Scheduler
│   │   ├── db/          # Configuração do Banco de Dados
│   │   ├── models/      # Modelos ORM (SQLAlchemy)
│   │   ├── schemas/     # Schemas Pydantic (Validação)
│   │   ├── scripts/     # Scripts de carga de dados (Seed/Backfill)
│   │   └── services/    # Lógica de negócio (InfoDengue Sync, Map Generation)
│   └── static/
│       └── geo/         # Arquivos GeoJSON (Mapas)
├── docker-compose.yml   # Infraestrutura
└── pyproject.toml       # Dependências
```

---

## 🔮 Contexto de IoT (Internet das Coisas)

Este projeto serve como a camada de **Processamento e Data Lake** em uma arquitetura de IoT para **Cidades Inteligentes**. A infraestrutura foi projetada para suportar expansões futuras, tais as:

*   **Ingestão de Sensores:** Receber dados de estações meteorológicas (temperatura/umidade) via API.
*   **Correlação de Dados:** Cruzar dados climáticos locais com o risco epidemiológico.
*   **Dispositivos de Borda:** Servir como backend para painéis de alerta físicos baseados em ESP32/Arduino.
