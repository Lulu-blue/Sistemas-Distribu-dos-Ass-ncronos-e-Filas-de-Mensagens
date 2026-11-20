"""Testes de contrato do agendador sem serviços externos."""
import importlib.util
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import MagicMock, patch


class DatabaseError(Exception):
    pass


spec = importlib.util.spec_from_file_location("agendador", Path(__file__).parents[1] / "main.py")
agendador = importlib.util.module_from_spec(spec)
with patch.dict(
    sys.modules,
    {
        "psycopg2": types.SimpleNamespace(Error=DatabaseError),
        "dotenv": types.SimpleNamespace(load_dotenv=lambda *args, **kwargs: None),
    },
):
    spec.loader.exec_module(agendador)


class AgendadorTests(unittest.TestCase):
    def test_cancelar_boletos_vencidos_retorna_linhas_afetadas(self):
        banco = MagicMock()
        cursor = banco.cursor.return_value.__enter__.return_value
        cursor.fetchall.return_value = [(10, "João", "2026-11-15T11:00:00Z")]
        cancelados = agendador.cancelar_boletos_vencidos(banco)
        self.assertEqual(len(cancelados), 1)
        self.assertEqual(cancelados[0][0], 10)
        cursor.execute.assert_called_once()
        sql_executado = cursor.execute.call_args[0][0]
        self.assertIn("SET status = 'CANCELADO'", sql_executado)
        self.assertIn("p.status = 'AGUARDANDO_PAGAMENTO'", sql_executado)
        self.assertIn("b.vencimento < now()", sql_executado)

    def test_configuracao_carrega_intervalo_do_env(self):
        env = {
            "POSTGRES_HOST": "postgres",
            "POSTGRES_DB": "delivery",
            "POSTGRES_USER": "delivery",
            "POSTGRES_PASSWORD": "secret",
            "INTERVALO_AGENDADOR_SEGUNDOS": "30",
        }
        with patch.dict(agendador.os.environ, env, clear=True):
            banco, intervalo = agendador.configuracao()
        self.assertEqual(banco["host"], "postgres")
        self.assertEqual(intervalo, 30.0)


if __name__ == "__main__":
    unittest.main()

