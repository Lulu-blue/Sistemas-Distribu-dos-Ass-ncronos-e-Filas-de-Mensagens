-- docker compose exec -T postgres psql -U delivery -d delivery < banco/consultas.sql

-- pedidos por status
SELECT status, COUNT(*) AS quantidade
FROM pedidos
GROUP BY status
ORDER BY quantidade DESC;

-- boletos por minuto
SELECT date_trunc('minute', gerado_em) AS minuto,
       COUNT(*)                        AS boletos
FROM boletos
GROUP BY minuto
ORDER BY minuto;

-- total de boletos
SELECT COUNT(*) AS total_boletos FROM boletos;

-- boletos por worker
SELECT gerado_por, COUNT(*) AS boletos
FROM boletos
GROUP BY gerado_por
ORDER BY boletos DESC;

-- boletos/s no último minuto
SELECT ROUND(COUNT(*) / 60.0, 2) AS boletos_por_segundo
FROM boletos
WHERE gerado_em > now() - INTERVAL '60 seconds';

-- vencidos ainda não pagos
SELECT p.id, p.cliente, b.vencimento
FROM pedidos p
JOIN boletos b ON b.pedido_id = p.id
WHERE p.status = 'AGUARDANDO_PAGAMENTO'
  AND b.vencimento < now();

-- últimos boletos
SELECT b.id, b.pedido_id, p.cliente, p.valor, b.linha_digitavel, b.vencimento, b.gerado_por
FROM boletos b
JOIN pedidos p ON p.id = b.pedido_id
ORDER BY b.gerado_em DESC
LIMIT 10;
