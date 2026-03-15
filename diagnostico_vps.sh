#!/bin/bash
# FurryCore Network - Script de Diagnóstico de Erros (502 Fix)
echo "🔍 Iniciando diagnóstico de containers..."

echo "--- [ STATUS DOS CONTAINERS ] ---"
sudo docker compose ps

echo -e "\n--- [ LOGS DO PAWSTEPS (REDESOCIAL) ] ---"
sudo docker compose logs pawsteps --tail 50

echo -e "\n--- [ LOGS DA LOJA (SHOP) ] ---"
sudo docker compose logs shop --tail 50

echo -e "\n--- [ LOGS DO NGINX ] ---"
sudo docker compose logs nginx --tail 20

echo -e "\n--- [ PERMISSÕES DE BANCO ] ---"
ls -la apps/*/database/*.db
