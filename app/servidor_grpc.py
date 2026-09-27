"""
Interface gRPC do servico de inferencia.

PRE-REQUISITO: gerar os stubs antes de rodar (veja scripts/gerar_stubs).

O QUE JA ESTA PRONTO: o metodo Prever.
O QUE VOCE PRECISA FAZER (TAREFAS.md, item 4): o metodo PreverLote.

Rodar:  python -m app.servidor_grpc
"""
from concurrent import futures
import time
import uuid

import grpc

from app.modelo import carregar_modelo

try:
    import inferencia_pb2
    import inferencia_pb2_grpc
except ImportError:  # pragma: no cover
    raise SystemExit(
        "Stubs nao encontrados. Rode antes:\n"
        "  python -m grpc_tools.protoc -I proto --python_out=. "
        "--grpc_python_out=. proto/inferencia.proto"
    )


class ServicoInferencia(inferencia_pb2_grpc.InferenciaServicer):

    def __init__(self):
        print("[grpc] carregando modelo...")
        self.modelo = carregar_modelo()
        print("[grpc] modelo pronto")

    def Prever(self, request, context):
        inicio = time.time()
        requisicao_id = str(uuid.uuid4())

        tamanho = len(request.texto.encode("utf-8"))

        r = self.modelo.prever(request.texto)

        tempo_ms = round((time.time() - inicio) * 1000, 2)

        print(
            f"[grpc] id={requisicao_id} "
            f"entrada={tamanho}B "
            f"tempo_ms={tempo_ms}"
        )

        return inferencia_pb2.RespostaPrever(
            texto=r["texto"],
            sentimento=r["sentimento"],
            confianca=r["confianca"]
        )

    def PreverLote(self, request, context):
        inicio = time.time()
        requisicao_id = str(uuid.uuid4())

        tamanho = sum(
            len(texto.encode("utf-8"))
            for texto in request.textos
        )

        resultados = []

        for texto in request.textos:
            r = self.modelo.prever(texto)

            resultados.append(
                inferencia_pb2.RespostaPrever(
                    texto=r["texto"],
                    sentimento=r["sentimento"],
                    confianca=r["confianca"]
                )
            )

        tempo_ms = round((time.time() - inicio) * 1000, 2)

        print(
            f"[grpc] id={requisicao_id} "
            f"entrada={tamanho}B "
            f"tempo_ms={tempo_ms}"
        )

        return inferencia_pb2.RespostaLote(resultados=resultados)


def servir(porta: int = 50051):
    servidor = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    inferencia_pb2_grpc.add_InferenciaServicer_to_server(
        ServicoInferencia(), servidor)
    servidor.add_insecure_port(f"[::]:{porta}")
    servidor.start()
    print(f"[grpc] escutando na porta {porta}")
    servidor.wait_for_termination()


if __name__ == "__main__":
    servir()
