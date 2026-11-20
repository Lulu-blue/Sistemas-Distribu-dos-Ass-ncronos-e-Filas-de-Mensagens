"""Consumidor de boletos: transação no PostgreSQL antes do ACK no RabbitMQ."""

import json
import logging
import os
from pathlib import Path
import secrets
import socket
import time
from datetime import datetime, timedelta, timezone

import pika
import psycopg2
from dotenv import load_dotenv

# No Compose, as variáveis já são injetadas. Localmente, aceita o .env da raiz.
load_dotenv(Path(__file__).resolve().parent.parent / ".env", override=False)
log = logging.getLogger("worker-boletos")
WORKER_ID = socket.gethostname()
ESPERA_RECONEXAO = 3


def configuracao():
    """Falha cedo se faltar configuração; não registra senhas nos logs."""
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
    prazo = float(os.environ.get("PRAZO_PAGAMENTO_MINUTOS", "4320"))
    # Mantém o callback curto em relação ao heartbeat de 60 segundos.
    if not 0 <= tempo <= 10 or not 0 < prazo <= 525600:
        raise ValueError("Tempo deve estar entre 0 e 10s; prazo entre 0 e 525600min")
    fila = os.environ["FILA_BOLETOS"]
    if not fila.strip():
        raise ValueError("FILA_BOLETOS não pode ser vazia")
    return banco, rabbit, fila, tempo, prazo


def conectar_com_retry(nome, abrir):
    tentativa = 0
    while True:
        tentativa += 1
        try:
            conexao = abrir()
            log.info("Conectado a %s", nome)
            return conexao
        except (psycopg2.Error, pika.exceptions.AMQPError, OSError):
            log.warning("%s indisponível; tentativa %d. Nova tentativa em %ds",
                        nome, tentativa, ESPERA_RECONEXAO)
            time.sleep(ESPERA_RECONEXAO)


def ler_pedido_id(corpo):
    mensagem = json.loads(corpo)
    if not isinstance(mensagem, dict):
        raise ValueError("Mensagem deve ser um objeto JSON")
    pedido_id = mensagem.get("pedido_id")
    if type(pedido_id) is not int or not 0 < pedido_id <= 9223372036854775807:
        raise ValueError("pedido_id deve ser um inteiro positivo BIGINT")
    return pedido_id


def gerar_boleto(banco, pedido_id, tempo, prazo):
    """O contexto confirma a transação; qualquer exceção provoca rollback."""
    with banco:
        with banco.cursor() as cursor:
            # Serializa reentregas concorrentes do mesmo pedido, sem bloquear outros.
            cursor.execute("SELECT status FROM pedidos WHERE id = %s FOR UPDATE", (pedido_id,))
            pedido = cursor.fetchone()
            if pedido is None:
                raise ValueError(f"Pedido {pedido_id} não encontrado")
            cursor.execute("SELECT id FROM boletos WHERE pedido_id = %s", (pedido_id,))
            if cursor.fetchone() is not None:
                return "boleto já existente; reentrega ignorada"
            # Uma mensagem atrasada não deve reabrir um pedido cancelado ou pago.
            if pedido[0] != "CRIADO":
                return f"pedido em {pedido[0]}; nenhuma alteração necessária"

            time.sleep(tempo)  # Padrão: time.sleep(1), conforme a simulação acadêmica.
            linha_digitavel = "".join(str(secrets.randbelow(10)) for _ in range(47))
            vencimento = datetime.now(timezone.utc) + timedelta(minutes=prazo)
            cursor.execute(
                """INSERT INTO boletos (pedido_id, linha_digitavel, vencimento, gerado_por)
                   VALUES (%s, %s, %s, %s)""",
                (pedido_id, linha_digitavel, vencimento, WORKER_ID),
            )
            cursor.execute(
                "UPDATE pedidos SET status = 'AGUARDANDO_PAGAMENTO' WHERE id = %s",
                (pedido_id,),
            )
    return "boleto gerado e pedido aguardando pagamento"


def criar_callback(banco, tempo, prazo):
    def receber(ch, method, properties, body):
        inicio = time.monotonic()
        pedido_id = None
        try:
            pedido_id = ler_pedido_id(body)
            resultado = gerar_boleto(banco, pedido_id, tempo, prazo)
        except Exception as erro:
            log.exception("Falha no pedido %s; devolvendo mensagem à fila", pedido_id)
            # Se o canal caiu, fechar a conexão deixa a entrega sem ACK ser reentregue.
            if ch.is_open:
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
            if isinstance(erro, (psycopg2.InterfaceError, psycopg2.OperationalError)):
                raise  # O laço principal também reconecta o banco.
        else:
            # Fora do try: falha no ACK não deve tentar NACK após commit confirmado.
            ch.basic_ack(delivery_tag=method.delivery_tag)
            log.info("pedido=%s | %s | %.2fs", pedido_id, resultado,
                     time.monotonic() - inicio)
    return receber


def fechar(conexao):
    if conexao is not None:
        try:
            conexao.close()
        except Exception:
            log.warning("Conexão já indisponível durante fechamento")


def main():
    logging.basicConfig(level=logging.INFO,
                        format=f"%(asctime)s [{WORKER_ID}] %(levelname)s %(message)s")
    config_banco, config_rabbit, fila, tempo, prazo = configuracao()
    try:
        while True:
            banco = rabbit = None
            try:
                banco = conectar_com_retry("PostgreSQL", lambda: psycopg2.connect(**config_banco))
                rabbit = conectar_com_retry("RabbitMQ", lambda: pika.BlockingConnection(config_rabbit))
                canal = rabbit.channel()
                canal.queue_declare(queue=fila, durable=True)
                canal.basic_qos(prefetch_count=1)
                canal.basic_consume(queue=fila, on_message_callback=criar_callback(banco, tempo, prazo),
                                    auto_ack=False)
                log.info("Consumindo %s | prefetch=1 | processamento=%ss | prazo=%smin", fila, tempo, prazo)
                canal.start_consuming()
            except (pika.exceptions.AMQPError, psycopg2.Error, OSError):
                log.warning("Conexão interrompida; reconectando em %ds", ESPERA_RECONEXAO)
            finally:
                fechar(rabbit)
                fechar(banco)
            time.sleep(ESPERA_RECONEXAO)
    except KeyboardInterrupt:
        log.info("Worker encerrado")


if __name__ == "__main__":
    main()
