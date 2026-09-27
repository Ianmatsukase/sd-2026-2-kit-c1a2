
import time
import uuid

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from app.modelo import carregar_modelo
from app import fila

app = FastAPI(title="Servico de Inferencia - C1.A2", version="0.1.0")

modelo = None


class Entrada(BaseModel):
    texto: str


@app.on_event("startup")
def _subir():
    """Carrega o modelo UMA vez. Este e o ponto-chave da Aula 6."""
    global modelo
    inicio = time.time()
    modelo = carregar_modelo()
    print(f"[startup] modelo carregado em {time.time() - inicio:.3f}s")


@app.get("/saude")
def saude():
    return {"status": "ok", "modelo_carregado": modelo is not None}


@app.post("/predict-sync")
def predict_sync(entrada: Entrada):
    """Inferencia SINCRONA: o cliente espera a resposta. Lab da Aula 6."""
    if not entrada.texto.strip():
        raise HTTPException(status_code=400, detail="texto vazio")
    inicio = time.time()
    resultado = modelo.prever(entrada.texto)
    resultado["tempo_ms"] = round((time.time() - inicio) * 1000, 2)
    return resultado



@app.post("/predict", status_code=202)
def predict(entrada: Entrada):
    """Enfileira a tarefa e devolve o id sem esperar."""
    inicio = time.time()
    requisicao_id = str(uuid.uuid4())

    if not entrada.texto.strip():
        print(
            f"[rest] id={requisicao_id} "
            f"entrada=0B "
            f"tempo_ms={round((time.time() - inicio) * 1000, 2)}"
        )
        raise HTTPException(status_code=400, detail="texto vazio")

    tamanho = len(entrada.texto.encode("utf-8"))
    tarefa_id = fila.enfileirar(entrada.texto)
    tempo_ms = round((time.time() - inicio) * 1000, 2)

    print(
        f"[rest] id={requisicao_id} "
        f"entrada={tamanho}B "
        f"tempo_ms={tempo_ms}"
    )

    return {"id": tarefa_id}
#     """Deve enfileirar a tarefa e devolver {"id": ...} SEM esperar."""
#     # DICA: use app.fila.enfileirar(entrada.texto)
#     raise NotImplementedError("implemente a submissao assincrona")


# ------------------------------------------------------------------
@app.get("/resultado/{tarefa_id}")
def resultado(tarefa_id: str):
    """Devolve o resultado da tarefa; 404 se o id não existir."""
    inicio = time.time()
    requisicao_id = str(uuid.uuid4())

    resultado = fila.buscar_resultado(tarefa_id)
    tempo_ms = round((time.time() - inicio) * 1000, 2)

    if resultado is None:
        print(
            f"[rest] id={requisicao_id} "
            f"entrada=0B "
            f"tempo_ms={tempo_ms}"
        )
        raise HTTPException(status_code=404, detail="tarefa não encontrada")

    print(
        f"[rest] id={requisicao_id} "
        f"entrada=0B "
        f"tempo_ms={tempo_ms}"
    )

    return resultado