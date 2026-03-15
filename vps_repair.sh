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
if [ -f "apps/cgrf/base_cgrf.db" ]; then
    sudo mv -f apps/cgrf/base_cgrf.db apps/cgrf/database/
    echo "✓ base_cgrf.db movido para apps/cgrf/database/"
fi

# PawSteps
if [ -f "apps/pawsteps/pawsteps.db" ]; then
    sudo mv -f apps/pawsteps/pawsteps.db apps/pawsteps/database/
    echo "✓ pawsteps.db movido para apps/pawsteps/database/"
fi
if [ -f "apps/pawsteps/database.db" ]; then
    sudo mv -f apps/pawsteps/database.db apps/pawsteps/database/pawsteps.db
    echo "✓ database.db (antigo) movido e renomeado para apps/pawsteps/database/pawsteps.db"
fi

# Shop
if [ -f "apps/shop/shop.db" ]; then
    sudo mv -f apps/shop/shop.db apps/shop/database/
    echo "✓ shop.db movido para apps/shop/database/"
fi

# 3. Permissões Progressivas (Crucial para o 502)
echo "🔐 Ajustando permissões de acesso..."
sudo chmod -R 777 apps/*/database
sudo chown -R $USER:$USER apps/*/database

# 4. Reiniciar e Reconstruir Docker (Limpeza total de cache)
echo "🐳 Reiniciando containers e limpando cache..."
sudo docker compose down
sudo docker compose build --no-cache admin-dash cgrf
sudo docker compose up -d

echo "✅ Reparo concluído! Aguarde 10 segundos e verifique https://arwolf.com.br"
