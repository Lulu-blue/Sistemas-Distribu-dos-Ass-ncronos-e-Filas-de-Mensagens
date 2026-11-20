"""Agendador periódico: verifica boletos vencidos e não pagos e altera o status do pedido para CANCELADO."""

import logging
import os
from pathlib import Path
import socket
import time

import psycopg2
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env", override=False)
log = logging.getLogger("agendador")
AGENDADOR_ID = socket.gethostname()
ESPERA_RECONEXAO = 3


def configuracao():
    """Carrega e valida as configurações do banco e do intervalo do agendador."""
    banco = {
        "host": os.environ["POSTGRES_HOST"],
        "port": int(os.environ.get("POSTGRES_PORT", "5432")),
        "dbname": os.environ["POSTGRES_DB"],
        "user": os.environ["POSTGRES_USER"],
        "password": os.environ["POSTGRES_PASSWORD"],
        "connect_timeout": 5,
        "options": "-c statement_timeout=15000 -c lock_timeout=10000",
    }
    intervalo = float(os.environ.get("INTERVALO_AGENDADOR_SEGUNDOS", "30"))
    if not 1 <= intervalo <= 86400:
        raise ValueError("INTERVALO_AGENDADOR_SEGUNDOS deve estar entre 1 e 86400s")
    return banco, intervalo


def conectar_com_retry(abrir):
    tentativa = 0
    while True:
        tentativa += 1
        try:
            conexao = abrir()
            log.info("Conectado ao PostgreSQL")
            return conexao
        except (psycopg2.Error, OSError):
            log.warning(
                "PostgreSQL indisponível; tentativa %d. Nova tentativa em %ds",
                tentativa,
                ESPERA_RECONEXAO,
            )
            time.sleep(ESPERA_RECONEXAO)


def cancelar_boletos_vencidos(banco):
    """Marca como CANCELADO todos os pedidos em AGUARDANDO_PAGAMENTO cujo boleto já venceu."""
    with banco:
        with banco.cursor() as cursor:
            cursor.execute(
                """
                UPDATE pedidos p
                SET status = 'CANCELADO'
                FROM boletos b
                WHERE b.pedido_id = p.id
                  AND p.status = 'AGUARDANDO_PAGAMENTO'
                  AND b.vencimento < now()
                RETURNING p.id, p.cliente, b.vencimento
                """
            )
            cancelados = cursor.fetchall()
    return cancelados


def fechar(conexao):
    if conexao is not None:
        try:
            conexao.close()
        except Exception:
            log.warning("Conexão já indisponível durante fechamento")


def main():
    logging.basicConfig(
        level=logging.INFO,
        format=f"%(asctime)s [{AGENDADOR_ID}] %(levelname)s %(message)s",
    )
    config_banco, intervalo = configuracao()
    log.info("Agendador iniciado | intervalo=%ss", intervalo)
    try:
        while True:
            banco = None
            try:
                banco = conectar_com_retry(lambda: psycopg2.connect(**config_banco))
                while True:
                    inicio = time.monotonic()
                    cancelados = cancelar_boletos_vencidos(banco)
                    duracao = time.monotonic() - inicio
                    if cancelados:
                        ids = [row[0] for row in cancelados[:10]]
                        sufixo = "..." if len(cancelados) > 10 else ""
                        log.info(
                            "Ciclo concluído em %.2fs | %d pedido(s) cancelado(s) por vencimento (ids=%s%s)",
                            duracao,
                            len(cancelados),
                            ids,
                            sufixo,
                        )
                    else:
                        log.info("Ciclo concluído em %.2fs | nenhum boleto vencido pendente", duracao)
                    time.sleep(intervalo)
            except (psycopg2.Error, OSError):
                log.warning("Conexão com PostgreSQL interrompida; reconectando em %ds", ESPERA_RECONEXAO)
            finally:
                fechar(banco)
            time.sleep(ESPERA_RECONEXAO)
    except KeyboardInterrupt:
        log.info("Agendador encerrado")


if __name__ == "__main__":
    main()
