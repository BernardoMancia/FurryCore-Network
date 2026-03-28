# Política de Privacidade — Ecossistema FurryCore Network

**Última atualização:** Março de 2026

## 1. Controlador dos Dados
A **FurryCore Network** é a controladora dos dados pessoais tratados neste ecossistema, conforme definido pela Lei Geral de Proteção de Dados (Lei nº 13.709/2018 — LGPD).

## 2. Dados Coletados e Finalidade

| Dado | Finalidade | Base Legal (LGPD) |
|------|-----------|-------------------|
| Nome / Nome de exibição | Identificação no registro CGRF e rede social | Execução de contrato (Art. 7, V) |
| E-mail | Comunicação, login, envio de credenciais | Execução de contrato (Art. 7, V) |
| Espécie / Região / Cidade / País | Personalização do perfil CGRF | Consentimento (Art. 7, I) |
| Foto (base64) | Exibição na identidade digital CGRF | Consentimento (Art. 7, I) |
| Senha (hash) | Autenticação segura | Execução de contrato (Art. 7, V) |
| Username / Bio / Avatar | Perfil social no PawSteps | Execução de contrato (Art. 7, V) |
| Localização aproximada (±100m) | Mapa de Amigos (opcional, opt-in) | Consentimento explícito (Art. 7, I) |
| Endereço de entrega | Cálculo de frete e entrega (Shop) | Execução de contrato (Art. 7, V) |
| Idade / Data de nascimento | Controle de acesso a conteúdo NSFW | Obrigação legal (Art. 7, II) |
| IP e User-Agent | Logs de segurança e prevenção de fraudes | Interesse legítimo (Art. 7, IX) |

## 3. Compartilhamento de Dados
Seus dados **não são compartilhados** com terceiros, exceto:
- **Provedores de e-mail** (SMTP) para envio de comunicações transacionais.
- **Transportadoras/Correios** para entregas de produtos adquiridos na loja.
- **Autoridades judiciais**, quando exigido por lei.

## 4. Tempo de Retenção
- **Dados de perfil ativo**: enquanto a conta estiver ativa.
- **Dados após exclusão**: anonimizados (hash irreversível) e mantidos por 5 anos para fins de auditoria forense, conforme LGPD Art. 16.
- **Logs de acesso**: 6 meses.

## 5. Seus Direitos (LGPD Art. 18)
Você tem direito a:
1. **Acesso** — Solicitar cópia de todos os seus dados pessoais (exportação em JSON).
2. **Correção** — Solicitar correção de dados incompletos ou incorretos.
3. **Anonimização/Exclusão** — Solicitar a exclusão ou anonimização dos dados pessoais.
4. **Portabilidade** — Receber seus dados em formato estruturado (JSON).
5. **Revogação de consentimento** — Retirar o consentimento a qualquer momento.
6. **Oposição** — Opor-se ao tratamento com base em interesse legítimo.

Para exercer seus direitos, utilize:
- A funcionalidade **"Solicitar Privacidade"** no Portal CGRF.
- A rota de **exportação de dados** no portal.
- Ou entre em contato via e-mail com o Encarregado de Dados.

## 6. Segurança dos Dados
Implementamos medidas técnicas e organizacionais, incluindo:
- Criptografia de senhas (Werkzeug/PBKDF2)
- Autenticação de dois fatores (TOTP)
- Proteção CSRF em todos os formulários
- Rate limiting contra ataques de força bruta
- Sanitização de inputs contra XSS/injeção
- Soft Delete para preservação forense
- Ofuscação de localização (ruído de ±100m)

## 7. Cookies
Utilizamos cookies de sessão estritamente necessários para autenticação e preferência de idioma. Não utilizamos cookies de rastreamento ou publicidade.

## 8. Alterações nesta Política
Reservamo-nos o direito de atualizar esta política. Alterações significativas serão comunicadas por e-mail.
