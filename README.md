# FurryCore Network - Multi-App Furry Identity & Social Network

## 🇧🇷 Português

### Visão Geral
A FurryCore Network evoluiu para um ecossistema completo composto por três aplicações independentes, integradas para oferecer segurança, socialização e e-commerce para a comunidade furry, tendo como base o Registro CGRF.

### Componentes
1.  **Portal CGRF (`apps/cgrf`)**: Sistema central de governança. Emissão de Identidades Digitais (CNF/RGF), painel administrativo e gestão de privacidade LGPD.
2.  **PawSteps (`apps/pawsteps`)**: Rede social estilo microblogging. Inclui timeline, stories, central de eventos e Mapa de Amigos com ofuscação de privacidade.
3.  **FurryCore Shop (`apps/shop`)**: Loja virtual para aquisição de carteiras físicas e produtos oficiais, com sistema de carrinho e cálculo de frete.

### Infraestrutura
- **Proxy Reverso**: Configurado via Nginx (`infra/nginx`) para gerenciar domínios e SSL.
- **Segurança**: Cabeçalhos HSTS, CSP, Proteção contra XSS e Rate Limiting globais.
- **Bancos de Dados**: SQLite3 independentes para cada aplicação, garantindo isolamento de dados.

### Como Executar (Localmente)
Cada aplicação roda em seu próprio processo Flask:
- **CGRF**: `cd apps/cgrf && python app.py` (Porta 6969)
- **PawSteps**: `cd apps/pawsteps && python app.py` (Porta 7070)
- **Shop**: `cd apps/shop && python app.py` (Porta 8080)

### Como Executar (Produção - Docker)
Este projeto está pronto para ser implantado usando Docker Compose V2:
```bash
# Instalar dependências (Debian/Ubuntu)
sudo apt update && sudo apt install docker.io docker-compose-v2 -y

# Subir ecossistema completo
sudo docker compose up -d --build
```

---

## 🇺🇸 English

...

### How to Run (Production - Docker)
This project is ready to be deployed using Docker Compose V2:
```bash
# Install dependencies (Debian/Ubuntu)
sudo apt update && sudo apt install docker.io docker-compose-v2 -y

# Start full ecosystem
sudo docker compose up -d --build
```


---

## 🇺🇸 English

### Overview
FurryCore Network has evolved into a full ecosystem consisting of three independent applications, integrated to provide security, socialization, and e-commerce for the furry community, based on the CGRF Registry.

### Components
1.  **Portal CGRF (`apps/cgrf`)**: Central governance system. Issuance of Digital Identities (CNF/RGF), admin panel, and LGPD privacy management.
2.  **PawSteps (`apps/pawsteps`)**: Microblogging-style social network. Includes timeline, stories, event center, and Friend Map with privacy obfuscation.
3.  **FurryCore Shop (`apps/shop`)**: Virtual store for physical wallets and official products, featuring a cart system and shipping calculation.

### Infrastructure
- **Reverse Proxy**: Configured via Nginx (`infra/nginx`) to manage domains and SSL.
- **Security**: Global HSTS, CSP, XSS Protection, and Rate Limiting headers.
- **Databases**: Independent SQLite3 databases for each application, ensuring data isolation.

### How to Run (Locally)
Each application runs in its own Flask process:
- **CGRF**: `cd apps/cgrf && python app.py` (Port 6969)
- **PawSteps**: `cd apps/pawsteps && python app.py` (Port 7070)
- **Shop**: `cd apps/shop && python app.py` (Port 8080)
