# Serviço de Inferência Distribuído — C1.A2

Projeto desenvolvido para a disciplina de **Sistemas Distribuídos e Computação em Nuvem — FAESA 2026/2**.

O sistema recebe textos, executa uma inferência de IA utilizando o modelo disponibilizado no kit da atividade e disponibiliza o serviço através de **REST e gRPC**, utilizando **Redis como fila de processamento assíncrono**.

## Integrantes

- Ian Rodrigues

## Tecnologias utilizadas

- Python 3.12
- FastAPI
- gRPC
- Protocol Buffers
- Redis
- Docker / Docker Compose
- Scikit-learn

---

# Arquitetura

O sistema foi dividido em componentes independentes para separar a entrada das requisições, o processamento da inferência e o armazenamento dos resultados.

```text
                    ┌─────────────────┐
                    │     Cliente     │
                    └────────┬────────┘
                             │
                ┌────────────┴────────────┐
                │                         │
                ▼                         ▼
        ┌───────────────┐         ┌───────────────┐
        │    REST       │         │     gRPC      │
        │   FastAPI     │         │   :50051      │
        └───────┬───────┘         └───────┬───────┘
                │                         │
                ▼                         ▼
        ┌───────────────┐         ┌───────────────┐
        │     Redis     │         │    Modelo     │
        │     Fila      │         │   Inferência  │
        └───────┬───────┘         └───────────────┘
                │
                ▼
        ┌───────────────┐
        │    Worker     │
        │  processamento│
        └───────┬───────┘
                │
                ▼
        ┌───────────────┐
        │     Redis     │
        │   Resultados  │
        └───────────────┘
Processamento assíncrono

O endpoint POST /predict não executa a inferência diretamente.

A requisição é colocada em uma fila Redis e o cliente recebe imediatamente um identificador da tarefa.

O worker consome a fila, executa a inferência e salva o resultado no Redis.

O cliente pode consultar o resultado posteriormente através de:

GET /resultado/{id}
Estrutura do projeto
.
├── app/
│   ├── api_rest.py
│   ├── fila.py
│   ├── modelo.py
│   ├── servidor_grpc.py
│   └── worker.py
│
├── proto/
│   └── inferencia.proto
│
├── exemplos/
│   └── cliente_rest.py
│
├── scripts/
│   └── gerar_stubs
│
├── docker-compose.yml
├── requirements.txt
├── TAREFAS.md
└── README.md
Principais componentes

app/api_rest.py

Implementa a API REST utilizando FastAPI.

Responsável por receber as requisições, validar os dados, inserir tarefas na fila e consultar resultados.

app/worker.py

Processa as tarefas retiradas da fila Redis e executa a inferência utilizando o modelo.

Também possui tratamento de falhas, retentativas e encaminhamento para a fila de descarte.

app/fila.py

Centraliza a comunicação com o Redis, incluindo:

inclusão de tarefas;
consumo da fila;
armazenamento de resultados;
consulta de resultados;
fila de dead-letter.

app/servidor_grpc.py

Implementa o serviço gRPC definido pelo arquivo .proto.

Possui os métodos:

Prever
PreverLote

app/modelo.py

Responsável pelo carregamento e utilização do modelo de inferência disponibilizado no projeto.

Requisitos

Para executar o projeto é necessário ter instalado:

Python 3.12
Docker Desktop
Git
Execução
1. Clonar o repositório
git clone https://github.com/lanmatsukase/sd-2026-2-kit-c1a2.git
cd sd-2026-2-kit-c1a2
2. Criar o ambiente virtual
Windows
py -3.12 -m venv .venv

Ative o ambiente:

.venv\Scripts\activate
Linux/macOS
python3.12 -m venv .venv
source .venv/bin/activate
3. Instalar as dependências
python -m pip install -r requirements.txt
4. Iniciar o Redis

Com o Docker Desktop em execução:

docker compose up -d

Para verificar:

docker compose ps
API REST
5. Iniciar a API

Em um terminal:

uvicorn app.api_rest:app --reload --port 8000

A API ficará disponível em:

http://localhost:8000

A documentação interativa pode ser acessada em:

http://localhost:8000/docs
Worker
6. Iniciar o worker

Em outro terminal:

python -m app.worker

O worker carrega o modelo uma vez e permanece aguardando novas tarefas.

Testando o processamento assíncrono

Com a API REST e o worker executando, envie uma requisição:

Windows PowerShell
$body = '{"texto":"o atendimento foi excelente"}'

$resposta = Invoke-RestMethod `
    -Uri "http://localhost:8000/predict" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body

$resposta

A API retornará um identificador:

id
------------------------------------
xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx

Consulte o resultado utilizando o ID retornado:

Invoke-RestMethod "http://localhost:8000/resultado/COLOQUE_O_ID_AQUI"

Resultado esperado:

texto       : o atendimento foi excelente
sentimento  : positivo
confianca   : 0.53
status      : pronto
tempo_ms    : 10.5
Endpoints REST
POST /predict

Recebe um texto e cria uma tarefa de inferência.

A resposta utiliza HTTP 202 Accepted.

Exemplo:

{
  "texto": "o atendimento foi excelente"
}

Resposta:

{
  "id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
}
GET /resultado/{id}

Consulta o resultado de uma tarefa através do identificador recebido no /predict.

Exemplo:

GET /resultado/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx

Caso o identificador não exista:

404 Not Found
GET /saude

Verifica se o serviço está funcionando e se o modelo foi carregado.

Exemplo:

GET /saude

Resposta:

{
  "status": "ok",
  "modelo_carregado": true
}
gRPC

O serviço gRPC utiliza o contrato definido em:

proto/inferencia.proto

Antes de executar o servidor, gere os arquivos Python do Protocol Buffers:

python -m grpc_tools.protoc -I proto --python_out=. --grpc_python_out=. proto/inferencia.proto

Depois execute:

python -m app.servidor_grpc

O servidor ficará disponível na porta:

50051
Métodos gRPC
Prever

Recebe um texto e retorna a inferência:

Prever(PedidoPrever) -> RespostaPrever
PreverLote

Recebe vários textos em uma única chamada:

PreverLote(PedidoLote) -> RespostaLote

Exemplo de teste:

python -c "import grpc, inferencia_pb2, inferencia_pb2_grpc; canal=grpc.insecure_channel('localhost:50051'); stub=inferencia_pb2_grpc.InferenciaStub(canal); r=stub.PreverLote(inferencia_pb2.PedidoLote(textos=['o atendimento foi excelente','o atendimento foi pessimo'])); print(r)"

REST e gRPC utilizam o mesmo modelo de inferência.

Resiliência

O processamento das tarefas possui mecanismo de retentativa.

Quando ocorre uma falha durante a inferência, a tarefa pode ser processada novamente até três tentativas.

Após atingir o limite de tentativas, a tarefa é encaminhada para uma fila de descarte chamada:

tarefas_dead_letter

As filas utilizadas pelo sistema são:

tarefas
tarefas_dead_letter

Os resultados processados são armazenados no Redis e associados aos identificadores das tarefas.

Logs

As requisições e processamentos são registrados no terminal.

Exemplo de log REST:

[rest] id=... entrada=25B tempo_ms=...

Exemplo de log do worker:

[worker] id=... entrada=25B tempo_ms=...

Exemplo de log gRPC:

[grpc] id=... entrada=25B tempo_ms=...

Os logs permitem acompanhar:

identificador da requisição;
tamanho da entrada;
tempo de processamento;
erros durante o processamento;
tentativas de execução.
Execução completa

Para executar o sistema completo, utilize os seguintes processos:

Terminal 1 — Redis
docker compose up -d
Terminal 2 — API REST
uvicorn app.api_rest:app --reload --port 8000
Terminal 3 — Worker
python -m app.worker
Terminal 4 — gRPC
python -m app.servidor_grpc

Com os componentes em execução, o sistema pode receber requisições REST e gRPC e realizar o processamento das inferências.

Fluxo da aplicação

O fluxo principal do processamento REST é:

1. Cliente envia texto
        ↓
2. FastAPI recebe a requisição
        ↓
3. Tarefa recebe um ID
        ↓
4. Tarefa é adicionada ao Redis
        ↓
5. API retorna HTTP 202 + ID
        ↓
6. Worker consome a tarefa
        ↓
7. Modelo executa a inferência
        ↓
8. Resultado é armazenado no Redis
        ↓
9. Cliente consulta /resultado/{id}
        ↓
10. Resultado é retornado
Observações

O modelo de IA utilizado é o modelo disponibilizado no kit da atividade.

O foco do projeto está na implementação da arquitetura distribuída, comunicação entre componentes, processamento assíncrono, tratamento de falhas e execução reproduzível.

O modelo é carregado uma vez na inicialização de cada processo que realiza inferência, evitando o carregamento a cada requisição.