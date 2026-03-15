#!/bin/bash
# FurryCore Network - Script de Reset Total de Bancos de Dados
# 🚨 CUIDADO: Isso apagará TODOS os dados (CGRF, Social, Loja e Admin)

echo "🐾 Iniciando Reset Total dos Bancos de Dados FurryCore..."

# Parar containers para evitar File Lock
echo "🛑 Parando containers..."
sudo docker compose stop

# Caminhos dos bancos
DB_DIR_CGRF="./apps/cgrf/database"
DB_DIR_SOCIAL="./apps/pawsteps/database"
DB_DIR_SHOP="./apps/shop/database"
DB_DIR_ADMIN="./apps/admin-dash/database"

# Função para resetar banco via SQL
reset_db() {
    local dir=$1
    local db_name=$2
    local schema=$3
    
    if [ -f "$dir/$db_name" ]; then
        echo "🗑️ Removendo $db_name..."
        rm "$dir/$db_name"
    fi
    
    if [ -f "$dir/$schema" ]; then
        echo "🏗️ Recriando $db_name usando $schema..."
        sqlite3 "$dir/$db_name" < "$dir/$schema"
    else
        echo "⚠️ Schema $schema não encontrado em $dir. O banco será criado vazio pela aplicação."
    fi
}

# Executar resets
reset_db "$DB_DIR_CGRF" "base_cgrf.db" "schema.sql"
reset_db "$DB_DIR_SOCIAL" "pawsteps.db" "schema.sql"
reset_db "$DB_DIR_SHOP" "shop.db" "schema_shop.sql"
reset_db "$DB_DIR_ADMIN" "admin_panel.db" "" # Admin não tem schema SQL fixo, app cria via SQLAlchemy/Hash

# Garantir permissões
echo "🔑 Ajustando permissões..."
sudo chmod -R 777 ./apps/*/database

# Subir containers
echo "🚀 Reiniciando serviços..."
sudo docker compose up -d

echo "✅ Reset concluído! O sistema está limpo e pronto para novos registros."
