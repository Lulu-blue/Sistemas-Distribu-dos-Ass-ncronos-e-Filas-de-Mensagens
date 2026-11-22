"""Testes de contrato do worker-envios sem serviços externos."""
import importlib.util
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import MagicMock, patch


class DatabaseError(Exception):
    pass


spec = importlib.util.spec_from_file_location("worker_envios", Path(__file__).parents[1] / "main.py")
worker_envios = importlib.util.module_from_spec(spec)
with patch.dict(
    sys.modules,
    {
        "pika": types.SimpleNamespace(),
        "psycopg2": types.SimpleNamespace(InterfaceError=DatabaseError, OperationalError=DatabaseError),
        "dotenv": types.SimpleNamespace(load_dotenv=lambda *args, **kwargs: None),
    },
):
    spec.loader.exec_module(worker_envios)

# os testes simulam erros de propósito; sem isso os tracebacks do log poluem a saída
worker_envios.log.disabled = True


class WorkerEnviosTests(unittest.TestCase):
    def test_commit_antes_do_ack_quando_pago(self):
        banco, canal = MagicMock(), MagicMock()
        cursor = banco.cursor.return_value.__enter__.return_value
        cursor.fetchone.return_value = ("PAGO", None)
        eventos = []
        banco.__exit__.side_effect = lambda *args: eventos.append("commit") or False
        canal.basic_ack.side_effect = lambda **kwargs: eventos.append("ack")
        with patch.object(worker_envios.time, "sleep"):
            worker_envios.criar_callback(banco, 1, 5)(
                canal, types.SimpleNamespace(delivery_tag=7), None, b'{"pedido_id": 42}'
            )
        self.assertEqual(eventos, ["commit", "ack"])
        self.assertEqual(cursor.execute.call_count, 2)
        canal.basic_nack.assert_not_called()

    def test_falha_commit_devolve_mensagem(self):
        banco, canal = MagicMock(), MagicMock()
        banco.cursor.return_value.__enter__.return_value.fetchone.return_value = ("PAGO", None)
        banco.__exit__.side_effect = DatabaseError("commit falhou")
        with patch.object(worker_envios.time, "sleep"), self.assertRaises(DatabaseError):
            worker_envios.criar_callback(banco, 1, 5)(
                canal, types.SimpleNamespace(delivery_tag=7), None, b'{"pedido_id": 42}'
            )
        canal.basic_ack.assert_not_called()
        canal.basic_nack.assert_called_once_with(delivery_tag=7, requeue=True)

    def test_reentrega_envio_ja_agendado_e_ignorada(self):
        banco = MagicMock()
        cursor = banco.cursor.return_value.__enter__.return_value
        cursor.fetchone.return_value = ("ENVIO_AGENDADO", "2026-11-15T12:00:00Z")
        resultado = worker_envios.agendar_envio(banco, 42, 1, 5)
        self.assertIn("reentrega ignorada", resultado)
        self.assertEqual(cursor.execute.call_count, 1)

    def test_pedido_nao_pago_nao_agenda_envio(self):
        banco = MagicMock()
        cursor = banco.cursor.return_value.__enter__.return_value
        cursor.fetchone.return_value = ("CANCELADO", None)
        resultado = worker_envios.agendar_envio(banco, 42, 1, 5)
        self.assertIn("CANCELADO", resultado)
        self.assertEqual(cursor.execute.call_count, 1)

    def test_calcula_previsao_envio_e_atualiza_para_envio_agendado(self):
        banco = MagicMock()
        cursor = banco.cursor.return_value.__enter__.return_value
        cursor.fetchone.return_value = ("PAGO", None)
        with patch.object(worker_envios.time, "sleep") as mock_sleep:
            resultado = worker_envios.agendar_envio(banco, 99, 1, 5)
        mock_sleep.assert_called_once_with(1)
        self.assertIn("envio agendado para", resultado)
        sql_update, params = cursor.execute.call_args_list[1][0]
        self.assertIn("SET status = 'ENVIO_AGENDADO'", sql_update)
        self.assertIn("previsao_envio = %s", sql_update)
        self.assertIsNotNone(params[0])
        self.assertEqual(params[1], 99)

    def test_json_invalido_recebe_nack(self):
        banco, canal = MagicMock(), MagicMock()
        worker_envios.criar_callback(banco, 1, 5)(
            canal, types.SimpleNamespace(delivery_tag=3), None, b'{"pedido_id": "invalido"}'
        )
        canal.basic_ack.assert_not_called()
        canal.basic_nack.assert_called_once_with(delivery_tag=3, requeue=True)


if __name__ == "__main__":
    unittest.main()

