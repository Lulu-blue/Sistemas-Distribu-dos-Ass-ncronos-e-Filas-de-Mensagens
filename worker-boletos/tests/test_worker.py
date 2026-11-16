"""Testes de contrato sem serviços externos nem dependências instaladas."""
import importlib.util
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import MagicMock, patch


class DatabaseError(Exception):
    pass


# Isola o módulo: os testes verificam o fluxo, não os drivers de terceiros.
spec = importlib.util.spec_from_file_location("worker", Path(__file__).parents[1] / "main.py")
worker = importlib.util.module_from_spec(spec)
with patch.dict(sys.modules, {
    "pika": types.SimpleNamespace(),
    "psycopg2": types.SimpleNamespace(InterfaceError=DatabaseError, OperationalError=DatabaseError),
    "dotenv": types.SimpleNamespace(load_dotenv=lambda *args, **kwargs: None),
}):
    spec.loader.exec_module(worker)


class WorkerTests(unittest.TestCase):
    def test_commit_antes_do_ack(self):
        banco, canal = MagicMock(), MagicMock()
        cursor = banco.cursor.return_value.__enter__.return_value
        cursor.fetchone.side_effect = [("CRIADO",), None]
        eventos = []
        banco.__exit__.side_effect = lambda *args: eventos.append("commit") or False
        canal.basic_ack.side_effect = lambda **kwargs: eventos.append("ack")
        with patch.object(worker.time, "sleep"):
            worker.criar_callback(banco, 1, 3)(canal, types.SimpleNamespace(delivery_tag=9), None,
                                               b'{"pedido_id": 1}')
        self.assertEqual(eventos, ["commit", "ack"])
        self.assertEqual(cursor.execute.call_count, 4)
        canal.basic_nack.assert_not_called()

    def test_falha_commit_devolve_mensagem(self):
        banco, canal = MagicMock(), MagicMock()
        banco.cursor.return_value.__enter__.return_value.fetchone.side_effect = [("CRIADO",), None]
        banco.__exit__.side_effect = DatabaseError("commit falhou")
        with patch.object(worker.time, "sleep"), self.assertRaises(DatabaseError):
            worker.criar_callback(banco, 1, 3)(canal, types.SimpleNamespace(delivery_tag=9), None,
                                               b'{"pedido_id": 1}')
        canal.basic_ack.assert_not_called()
        canal.basic_nack.assert_called_once_with(delivery_tag=9, requeue=True)

    def test_reentrega_nao_insere_nem_regride_status(self):
        banco = MagicMock()
        cursor = banco.cursor.return_value.__enter__.return_value
        cursor.fetchone.side_effect = [("PAGO",), (10,)]
        worker.gerar_boleto(banco, 1, 1, 3)
        self.assertEqual(cursor.execute.call_count, 2)

    def test_pedido_cancelado_sem_boleto_nao_e_reaberto(self):
        banco = MagicMock()
        cursor = banco.cursor.return_value.__enter__.return_value
        cursor.fetchone.side_effect = [("CANCELADO",), None]
        worker.gerar_boleto(banco, 1, 1, 3)
        self.assertEqual(cursor.execute.call_count, 2)

    def test_json_invalido_recebe_nack(self):
        banco, canal = MagicMock(), MagicMock()
        worker.criar_callback(banco, 1, 3)(canal, types.SimpleNamespace(delivery_tag=9), None, b'{}')
        canal.basic_nack.assert_called_once_with(delivery_tag=9, requeue=True)
        canal.basic_ack.assert_not_called()
        banco.cursor.assert_not_called()

    def test_falha_ack_nao_tenta_nack(self):
        canal = MagicMock()
        canal.basic_ack.side_effect = RuntimeError("canal caiu")
        with patch.object(worker, "gerar_boleto", return_value="ok"), self.assertRaises(RuntimeError):
            worker.criar_callback(MagicMock(), 1, 3)(canal, types.SimpleNamespace(delivery_tag=9), None,
                                                     b'{"pedido_id": 1}')
        canal.basic_nack.assert_not_called()


if __name__ == "__main__":
    unittest.main()
