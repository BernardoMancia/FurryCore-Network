#!/bin/bash

# FurryCore Network - VPS Repair Script
# Este script organiza os bancos de dados e reinicia os containers

echo "🐾 Iniciando reparo de infraestrutura..."

# 1. Garantir que as pastas database existam
mkdir -p apps/cgrf/database
mkdir -p apps/pawsteps/database
mkdir -p apps/shop/database
mkdir -p apps/admin-dash/database

# 2. Mover arquivos .db se estiverem nos locais antigos
echo "📁 Organizando arquivos de banco de dados..."

# CGRF
if [ -f "apps/cgrf/base_cgrf.db" ]; then
    mv apps/cgrf/base_cgrf.db apps/cgrf/database/
    echo "✓ base_cgrf.db movido para apps/cgrf/database/"
fi

# PawSteps
if [ -f "apps/pawsteps/pawsteps.db" ]; then
    mv apps/pawsteps/pawsteps.db apps/pawsteps/database/
    echo "✓ pawsteps.db movido para apps/pawsteps/database/"
fi
if [ -f "apps/pawsteps/database.db" ]; then
    mv apps/pawsteps/database.db apps/pawsteps/database/pawsteps.db
    echo "✓ database.db (antigo) movido e renomeado para apps/pawsteps/database/pawsteps.db"
fi

# Shop
if [ -f "apps/shop/shop.db" ]; then
    mv apps/shop/shop.db apps/shop/database/
    echo "✓ shop.db movido para apps/shop/database/"
fi

# 3. Permissões
chmod -R 777 apps/*/database

# 4. Reiniciar Docker
echo "🐳 Reiniciando containers para aplicar novos volumes..."
sudo docker compose down
sudo docker compose up -d

echo "✅ Reparo concluído! Verifique https://arwolf.com.br"
