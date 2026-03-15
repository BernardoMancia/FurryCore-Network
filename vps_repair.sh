#!/bin/bash

# FurryCore Network - VPS Repair Script
# Este script organiza os bancos de dados e reinicia os containers

echo "🐾 Iniciando reparo de infraestrutura..."

# 1. Garantir que as pastas database existam (usando sudo)
sudo mkdir -p apps/cgrf/database
sudo mkdir -p apps/pawsteps/database
sudo mkdir -p apps/shop/database
sudo mkdir -p apps/admin-dash/database

# 2. Mover arquivos .db se estiverem nos locais antigos
echo "📁 Organizando arquivos de banco de dados..."

# CGRF
if [ -f "apps/cgrf/base_cgrf.db" ] && [ ! -f "apps/cgrf/database/base_cgrf.db" ]; then
    sudo mv -f apps/cgrf/base_cgrf.db apps/cgrf/database/
    echo "✓ base_cgrf.db movido para apps/cgrf/database/"
elif [ -f "apps/cgrf/base_cgrf.db" ]; then
    echo "⚠️  base_cgrf.db já existe no destino. Removendo duplicata órfã..."
    sudo rm apps/cgrf/base_cgrf.db
fi

# PawSteps
if [ -f "apps/pawsteps/pawsteps.db" ] && [ ! -f "apps/pawsteps/database/pawsteps.db" ]; then
    sudo mv -f apps/pawsteps/pawsteps.db apps/pawsteps/database/
    echo "✓ pawsteps.db movido para apps/pawsteps/database/"
fi

# 3. Rodar Migrações de Banco (Garantir que as colunas novas existam)
echo "🗄️ Verificando integridade das tabelas..."
python3 tmp_migrate_db_v3.py || echo "⚠️ Alerta: Falha na migração v3."
python3 tmp_migrate_db_v4.py || echo "⚠️ Alerta: Falha na migração v4."

# 4. Permissões Progressivas
echo "🔐 Ajustando permissões de acesso..."
sudo chmod -R 777 apps/*/database
sudo chown -R $USER:$USER apps/*/database

# 5. Reiniciar e Reconstruir Docker
echo "🐳 Reiniciando containers..."
sudo docker compose down
sudo docker compose build cgrf admin-dash
sudo docker compose up -d

echo "⏳ Aguardando startup (15s)..."
sleep 15
sudo docker ps
sudo docker logs furry_cgrf --tail 20

echo "✅ Reparo concluído! Verifique https://arwolf.com.br e https://cgrf.com.br"
