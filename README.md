# CGRF 2.0 - Cadastro e Gestão de Registro Furry

## 🇧🇷 Português

### Visão Geral
O CGRF 2.0 é um Sistema de Governança de Identidades para a comunidade furry, focado em transparência, segurança e conformidade com a LGPD. O sistema emite documentos digitais (CNF e RGF), gerencia perfis através de QR Codes e possui um sistema robusto de controle de acesso (RBAC).

### Funcionalidades
- **Emissão de Identidade**: Geração de CNF e RGF com QR Code individual.
- **Portabilidade**: Perfil público acessível via QR Code com motor de censura de dados.
- **Governança**: Sistema de tickets para solicitações de privacidade e suporte.
- **Segurança**: Proteção contra SQLi, XSS, CSRF e autenticação MFA (TOTP).

### Requisitos
- Python 3.10+
- SQLite3

### Instalação
1. Clone o repositório.
2. Crie um ambiente virtual: `python -m venv venv`.
3. Ative o ambiente virtual.
4. Instale as dependências: `pip install -r requirements.txt`.
5. Configure o arquivo `.env` baseado no `.env.example`.
6. Execute a aplicação: `python app.py`.

---

## 🇺🇸 English

### Overview
CGRF 2.0 is an Identity Governance System for the furry community, focused on transparency, security, and LGPD compliance. The system issues digital documents (CNF and RGF), manages profiles via QR Codes, and features a robust Role-Based Access Control (RBAC) system.

### Features
- **Identity Issuance**: CNF and RGF generation with individual QR Codes.
- **Portability**: Public profile accessible via QR Code with a data masking engine.
- **Governance**: Ticket system for privacy requests and support.
- **Security**: Protection against SQLi, XSS, CSRF, and MFA (TOTP) authentication.

### Requirements
- Python 3.10+
- SQLite3

### Installation
1. Clone the repository.
2. Create a virtual environment: `python -m venv venv`.
3. Activate the virtual environment.
4. Install dependencies: `pip install -r requirements.txt`.
5. Setup the `.env` file based on `.env.example`.
6. Run the application: `python app.py`.
