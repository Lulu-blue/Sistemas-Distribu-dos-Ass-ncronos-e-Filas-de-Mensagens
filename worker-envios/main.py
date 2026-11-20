"""Consumidor de envios: calcula a previsão de envio e atualiza o pedido para ENVIO_AGENDADO antes do ACK."""

import json
import logging
import os
from pathlib import Path
import socket
import time
from datetime import datetime, timedelta, timezone

import pika
import psycopg2
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env", override=False)
log = logging.getLogger("worker-envios")
WORKER_ID = socket.gethostname()
ESPERA_RECONEXAO = 3


def configuracao():
    """Carrega e valida as variáveis de ambiente necessárias."""
    banco = {
        "host": os.environ["POSTGRES_HOST"],
        "port": int(os.environ.get("POSTGRES_PORT", "5432")),
        "dbname": os.environ["POSTGRES_DB"],
        "user": os.environ["POSTGRES_USER"],
        "password": os.environ["POSTGRES_PASSWORD"],
        "connect_timeout": 5,
        "options": "-c statement_timeout=15000 -c lock_timeout=10000",
    }
    rabbit = pika.ConnectionParameters(
        host=os.environ["RABBITMQ_HOST"],
        port=int(os.environ.get("RABBITMQ_PORT", "5672")),
        credentials=pika.PlainCredentials(
            os.environ["RABBITMQ_USER"], os.environ["RABBITMQ_PASSWORD"]
        ),
        heartbeat=60,
        socket_timeout=5,
        stack_timeout=10,
        blocked_connection_timeout=30,
    )
    tempo = float(os.environ.get("TEMPO_PROCESSAMENTO_SEGUNDOS", "1"))
    prazo_envio = float(os.environ.get("PRAZO_ENVIO_MINUTOS", "2880"))
    if not 0 <= tempo <= 10 or not 0 < prazo_envio <= 525600:
        raise ValueError("Tempo deve estar entre 0 e 10s; prazo de envio entre 0 e 525600min")
    fila = os.environ["FILA_ENVIOS"]
    if not fila.strip():
        raise ValueError("FILA_ENVIOS não pode ser vazia")
    return banco, rabbit, fila, tempo, prazo_envio


def conectar_com_retry(nome, abrir):
    tentativa = 0
    while True:
        tentativa += 1
        try:
            conexao = abrir()
            log.info("Conectado a %s", nome)
            return conexao
        except (psycopg2.Error, pika.exceptions.AMQPError, OSError):
            log.warning(
                "%s indisponível; tentativa %d. Nova tentativa em %ds",
                nome,
                tentativa,
                ESPERA_RECONEXAO,
            )
            time.sleep(ESPERA_RECONEXAO)


def ler_pedido_id(corpo):
    mensagem = json.loads(corpo)
    if not isinstance(mensagem, dict):
        raise ValueError("Mensagem deve ser um objeto JSON")
    pedido_id = mensagem.get("pedido_id")
    if type(pedido_id) is not int or not 0 < pedido_id <= 9223372036854775807:
        raise ValueError("pedido_id deve ser um inteiro positivo BIGINT")
    return pedido_id


def agendar_envio(banco, pedido_id, tempo, prazo_envio):
    """Agenda o envio de um pedido pago de forma transacional e idempotente."""
    with banco:
        with banco.cursor() as cursor:
            cursor.execute(
                "SELECT status, previsao_envio FROM pedidos WHERE id = %s FOR UPDATE",
                (pedido_id,),
            )
            pedido = cursor.fetchone()
            if pedido is None:
                raise ValueError(f"Pedido {pedido_id} não encontrado")

            status_atual, previsao_atual = pedido
            if status_atual in ("ENVIO_AGENDADO", "ENVIADO") and previsao_atual is not None:
                return f"envio já agendado ({status_atual}); reentrega ignorada"

            if status_atual != "PAGO":
                return f"pedido em {status_atual}; nenhuma alteração necessária"

            time.sleep(tempo)
            previsao_envio = datetime.now(timezone.utc) + timedelta(minutes=prazo_envio)
            cursor.execute(
                """
                UPDATE pedidos
                SET status = 'ENVIO_AGENDADO',
                    previsao_envio = %s
                WHERE id = %s
                """,
                (previsao_envio, pedido_id),
            )
    return f"envio agendado para {previsao_envio.isoformat(timespec='seconds')}"


def criar_callback(banco, tempo, prazo_envio):
    def receber(ch, method, properties, body):
        inicio = time.monotonic()
        pedido_id = None
        try:
            pedido_id = ler_pedido_id(body)
            resultado = agendar_envio(banco, pedido_id, tempo, prazo_envio)
        except Exception as erro:
            log.exception("Falha no agendamento do pedido %s; devolvendo mensagem à fila", pedido_id)
            if ch.is_open:
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
            if isinstance(erro, (psycopg2.InterfaceError, psycopg2.OperationalError)):
                raise
        else:
            ch.basic_ack(delivery_tag=method.delivery_tag)
            log.info(
                "pedido=%s | %s | %.2fs",
                pedido_id,
                resultado,
                time.monotonic() - inicio,
            )

    return receber


def fechar(conexao):
    if conexao is not None:
        try:
            conexao.close()
        except Exception:
            log.warning("Conexão já indisponível durante fechamento")


def main():
    logging.basicConfig(
        level=logging.INFO,
        format=f"%(asctime)s [{WORKER_ID}] %(levelname)s %(message)s",
    )
    config_banco, config_rabbit, fila, tempo, prazo_envio = configuracao()
    try:
        while True:
            banco = rabbit = None
            try:
                banco = conectar_com_retry("PostgreSQL", lambda: psycopg2.connect(**config_banco))
                rabbit = conectar_com_retry("RabbitMQ", lambda: pika.BlockingConnection(config_rabbit))
                canal = rabbit.channel()
                canal.queue_declare(queue=fila, durable=True)
                canal.basic_qos(prefetch_count=1)
                canal.basic_consume(
                    queue=fila,
                    on_message_callback=criar_callback(banco, tempo, prazo_envio),
                    auto_ack=False,
                )
                log.info(
                    "Consumindo %s | prefetch=1 | processamento=%ss | prazo_envio=%smin",
                    fila,
                    tempo,
                    prazo_envio,
                )
                canal.start_consuming()
            except (pika.exceptions.AMQPError, psycopg2.Error, OSError):
                log.warning("Conexão interrompida; reconectando em %ds", ESPERA_RECONEXAO)
            finally:
                fechar(rabbit)
                fechar(banco)
            time.sleep(ESPERA_RECONEXAO)
    except KeyboardInterrupt:
        log.info("Worker de envios encerrado")


if __name__ == "__main__":
    main()
