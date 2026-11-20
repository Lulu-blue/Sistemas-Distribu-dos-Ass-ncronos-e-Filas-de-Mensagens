import json
import logging
import os
import random
import time
from decimal import Decimal

import pika
import psycopg
from faker import Faker
from fastapi import BackgroundTasks, FastAPI, HTTPException, Query, status
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

logging.basicConfig(level=logging.INFO, format="%(asctime)s [api] %(message)s")
log = logging.getLogger("api")

# tudo vem do .env (via docker-compose)
POSTGRES_HOST = os.environ["POSTGRES_HOST"]
POSTGRES_PORT = int(os.environ["POSTGRES_PORT"])
POSTGRES_DB = os.environ["POSTGRES_DB"]
POSTGRES_USER = os.environ["POSTGRES_USER"]
POSTGRES_PASSWORD = os.environ["POSTGRES_PASSWORD"]

RABBITMQ_HOST = os.environ["RABBITMQ_HOST"]
RABBITMQ_PORT = int(os.environ["RABBITMQ_PORT"])
RABBITMQ_USER = os.environ["RABBITMQ_USER"]
RABBITMQ_PASSWORD = os.environ["RABBITMQ_PASSWORD"]

FILA_BOLETOS = os.environ["FILA_BOLETOS"]
FILA_ENVIOS = os.environ["FILA_ENVIOS"]
QTD_PEDIDOS_PICO = int(os.environ["QTD_PEDIDOS_PICO"])

TENTATIVAS_CONEXAO = 10
ESPERA_ENTRE_TENTATIVAS = 3  # segundos

app = FastAPI(title="Delivery - API e painel administrativo")

STATUS_PEDIDO = (
    "CRIADO",
    "AGUARDANDO_PAGAMENTO",
    "PAGO",
    "ENVIO_AGENDADO",
    "ENVIADO",
    "CANCELADO",
)


@app.get("/", include_in_schema=False)
def inicio():
    """Abre o painel diretamente na raiz para facilitar a demonstração."""
    return FileResponse("/app/admin.html")


@app.get("/admin", include_in_schema=False)
def painel_admin():
    return FileResponse("/app/admin.html")


@app.get("/api/admin/resumo")
def resumo_pedidos():
    """Retorna todos os status, inclusive os que ainda estão com zero pedidos."""
    with conectar_banco() as conn:
        linhas = conn.execute(
            "SELECT status, COUNT(*) FROM pedidos GROUP BY status"
        ).fetchall()
    quantidades = {linha[0]: linha[1] for linha in linhas}
    return {
        "total": sum(quantidades.values()),
        "por_status": {
            situacao: quantidades.get(situacao, 0) for situacao in STATUS_PEDIDO
        },
    }


@app.get("/api/admin/pedidos")
def listar_pedidos(
    filtro_status: str | None = Query(default=None, alias="status"),
    limite: int = Query(default=100, ge=1, le=500),
):
    """Lista pedidos recentes e dados do boleto, quando já tiver sido gerado."""
    if filtro_status and filtro_status not in STATUS_PEDIDO:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "status inválido")

    consulta = """
        SELECT p.id, p.cliente, p.valor, p.status, p.criado_em,
               p.atualizado_em, p.previsao_envio,
               b.linha_digitavel, b.vencimento, b.gerado_por
        FROM pedidos AS p
        LEFT JOIN boletos AS b ON b.pedido_id = p.id
    """
    parametros = []
    if filtro_status:
        consulta += " WHERE p.status = %s"
        parametros.append(filtro_status)
    consulta += " ORDER BY p.criado_em DESC, p.id DESC LIMIT %s"
    parametros.append(limite)

    with conectar_banco() as conn:
        linhas = conn.execute(consulta, parametros).fetchall()

    colunas = (
        "id", "cliente", "valor", "status", "criado_em", "atualizado_em",
        "previsao_envio", "linha_digitavel", "vencimento", "gerado_por",
    )
    return [dict(zip(colunas, linha)) for linha in linhas]




def conectar_banco() -> psycopg.Connection:
    for tentativa in range(1, TENTATIVAS_CONEXAO + 1):
        try:
            return psycopg.connect(
                host=POSTGRES_HOST,
                port=POSTGRES_PORT,
                dbname=POSTGRES_DB,
                user=POSTGRES_USER,
                password=POSTGRES_PASSWORD,
            )
        except psycopg.OperationalError as erro:
            log.warning("postgres indisponível (tentativa %d): %s", tentativa, erro)
            time.sleep(ESPERA_ENTRE_TENTATIVAS)
    raise RuntimeError("não foi possível conectar ao postgres")


def conectar_rabbitmq() -> pika.BlockingConnection:
    parametros = pika.ConnectionParameters(
        host=RABBITMQ_HOST,
        port=RABBITMQ_PORT,
        credentials=pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD),
    )
    for tentativa in range(1, TENTATIVAS_CONEXAO + 1):
        try:
            return pika.BlockingConnection(parametros)
        except pika.exceptions.AMQPConnectionError as erro:
            log.warning("rabbitmq indisponível (tentativa %d): %s", tentativa, erro)
            time.sleep(ESPERA_ENTRE_TENTATIVAS)
    raise RuntimeError("não foi possível conectar ao rabbitmq")


def abrir_canal(conexao: pika.BlockingConnection):
    canal = conexao.channel()
    # durable: a fila sobrevive a um restart do rabbitmq (volume dados_rabbitmq).
    # os workers precisam declarar as filas com durable=True também.
    canal.queue_declare(queue=FILA_BOLETOS, durable=True)
    canal.queue_declare(queue=FILA_ENVIOS, durable=True)
    return canal




def montar_mensagem(pedido_id, cliente, valor, criado_em) -> bytes:
    """Contrato combinado com os workers."""
    return json.dumps(
        {
            "pedido_id": pedido_id,
            "cliente": cliente,
            "valor": float(valor),
            "criado_em": criado_em.replace(tzinfo=None).isoformat(timespec="seconds"),
        },
        ensure_ascii=False,
    ).encode("utf-8")


def publicar(canal, fila: str, corpo: bytes) -> None:
    canal.basic_publish(
        exchange="",
        routing_key=fila,
        body=corpo,
        # delivery_mode=2: mensagem persistente, não some se o rabbitmq reiniciar
        properties=pika.BasicProperties(delivery_mode=2, content_type="application/json"),
    )


def publicar_uma(fila: str, corpo: bytes) -> None:
    conexao = conectar_rabbitmq()
    try:
        publicar(abrir_canal(conexao), fila, corpo)
    finally:
        conexao.close()




class NovoPedido(BaseModel):
    cliente: str = Field(min_length=1, max_length=150, examples=["Ana Souza"])
    valor: Decimal = Field(gt=0, max_digits=10, decimal_places=2, examples=[59.90])


@app.post("/pedidos", status_code=status.HTTP_201_CREATED)
def criar_pedido(pedido: NovoPedido):
    # 1) anota no banco como CRIADO (commit antes de publicar, senão o worker
    #    pode pegar a mensagem antes do pedido existir no banco)
    with conectar_banco() as conn:
        pedido_id, criado_em = conn.execute(
            "INSERT INTO pedidos (cliente, valor) VALUES (%s, %s) RETURNING id, criado_em",
            (pedido.cliente, pedido.valor),
        ).fetchone()

    # 2) pendura na fila; o boleto é gerado pelo worker-boletos
    try:
        publicar_uma(FILA_BOLETOS, montar_mensagem(pedido_id, pedido.cliente, pedido.valor, criado_em))
    except Exception as erro:
        log.error("pedido %d gravado mas não publicado: %s", pedido_id, erro)
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "fila indisponível")

    return {"pedido_id": pedido_id, "status": "CRIADO"}


def gerar_pico(quantidade: int) -> None:
    inicio = time.perf_counter()
    fake = Faker("pt_BR")
    clientes = [fake.name() for _ in range(quantidade)]
    valores = [Decimal(random.randint(1500, 25000)) / 100 for _ in range(quantidade)]  # R$ 15,00 a 250,00

    try:
        # um INSERT só para os N pedidos (bem mais rápido que N INSERTs)
        with conectar_banco() as conn:
            pedidos = conn.execute(
                """
                INSERT INTO pedidos (cliente, valor)
                SELECT * FROM unnest(%s::varchar[], %s::numeric[])
                RETURNING id, cliente, valor, criado_em
                """,
                (clientes, valores),
            ).fetchall()
        log.info("pico: %d pedidos gravados em %.2fs", len(pedidos), time.perf_counter() - inicio)

        # uma conexão e um canal para publicar todas as mensagens
        conexao = conectar_rabbitmq()
        try:
            canal = abrir_canal(conexao)
            for pedido_id, cliente, valor, criado_em in pedidos:
                publicar(canal, FILA_BOLETOS, montar_mensagem(pedido_id, cliente, valor, criado_em))
        finally:
            conexao.close()
        log.info("pico: %d pedidos publicados em %.2fs", len(pedidos), time.perf_counter() - inicio)
    except Exception:
        log.exception("pico: falhou")


@app.post("/pedidos/simular-pico", status_code=status.HTTP_202_ACCEPTED)
def simular_pico(tarefas: BackgroundTasks):
    # responde na hora; os pedidos são gerados e publicados em segundo plano
    tarefas.add_task(gerar_pico, QTD_PEDIDOS_PICO)
    return {"mensagem": "pico iniciado", "quantidade": QTD_PEDIDOS_PICO}


@app.post("/pedidos/{pedido_id}/aprovar")
def aprovar_pagamento(pedido_id: int):
    with conectar_banco() as conn:
        linha = conn.execute(
            """
            UPDATE pedidos SET status = 'PAGO'
            WHERE id = %s AND status = 'AGUARDANDO_PAGAMENTO'
            RETURNING id, cliente, valor, criado_em
            """,
            (pedido_id,),
        ).fetchone()

        if linha is None:
            atual = conn.execute("SELECT status FROM pedidos WHERE id = %s", (pedido_id,)).fetchone()
            if atual is None:
                raise HTTPException(status.HTTP_404_NOT_FOUND, "pedido não encontrado")
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                f"só dá para aprovar pedido AGUARDANDO_PAGAMENTO (status atual: {atual[0]})",
            )

    try:
        publicar_uma(FILA_ENVIOS, montar_mensagem(*linha))
    except Exception as erro:
        # sem a mensagem o envio nunca seria agendado: desfaz a aprovação
        log.error("pedido %d aprovado mas não publicado, revertendo: %s", pedido_id, erro)
        with conectar_banco() as conn:
            conn.execute(
                "UPDATE pedidos SET status = 'AGUARDANDO_PAGAMENTO' WHERE id = %s AND status = 'PAGO'",
                (pedido_id,),
            )
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "fila indisponível")

    return {"pedido_id": pedido_id, "status": "PAGO"}


@app.post("/pedidos/{pedido_id}/cancelar")
def cancelar_pedido(pedido_id: int):
    """Cancela pedidos que ainda não foram pagos ou enviados."""
    with conectar_banco() as conn:
        linha = conn.execute(
            """
            UPDATE pedidos SET status = 'CANCELADO'
            WHERE id = %s AND status IN ('CRIADO', 'AGUARDANDO_PAGAMENTO')
            RETURNING id
            """,
            (pedido_id,),
        ).fetchone()

        if linha is None:
            atual = conn.execute(
                "SELECT status FROM pedidos WHERE id = %s", (pedido_id,)
            ).fetchone()
            if atual is None:
                raise HTTPException(status.HTTP_404_NOT_FOUND, "pedido não encontrado")
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                "só é possível cancelar pedidos nos status CRIADO ou AGUARDANDO_PAGAMENTO",
            )

    return {"pedido_id": linha[0], "status": "CANCELADO"}
