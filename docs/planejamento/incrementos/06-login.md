# Incremento SDD 06 — acesso ao XP Pulse

Decisão do usuário em 10/10/2026: acrescentar login `admin` / `admin`, com
logo centralizado e o design existente. RF31; RN53–RN58; CA79–CA84.
Este pedido substitui o recorte anterior sem autenticação. Continua sendo uma
demonstração local com um assessor e dados fictícios.

## Regras definidas antes do código

- RN53. Tela pública em `/login`, tema escuro, amarelo XP, logo centralizado,
  campos Usuário/Senha e botão Entrar. Sem cadastro ou recuperação de senha.
  Credenciais verificadas somente no backend: usuário `admin` (espaços externos
  removidos), senha `admin` exata. Campos obrigatórios, usuário até 80 caracteres,
  senha até 256; JSON inválido/campos extras recusados. Erro de credenciais genérico.
- RN54. `/`, `/legacy` e todas as APIs de dados exigem sessão. Página sem sessão
  redireciona para `/login`; API retorna JSON 401, sem dados nem chamada externa.
  `/login` autenticado redireciona para `/`. Assets e consulta de sessão são públicos.
- RN55. Cookie assinado HttpOnly/SameSite=Lax; chave aleatória persistida localmente
  fora do Git (ou `SECRET_KEY` no ambiente). Sessão opaca, com somente seu hash no
  SQLite, validade absoluta de oito horas pelo `Clock`. Senha não é armazenada na
  sessão/banco/navegador. Recarregar/reiniciar preserva sessão válida; cookie forjado
  ou sessão vencida não concede acesso. Sem opção de lembrar acesso.
- RN56. GET de sessão fornece token CSRF; login rotaciona sessão/token. Toda
  escrita da API, inclusive login/logout, exige `X-CSRF-Token` correspondente.
  Token ausente/errado retorna 403 sem gravação/chamada externa. Não habilitar CORS.
  Consultas autenticadas e HTML não podem ficar em cache HTTP.
- RN57. Botão Sair encerra a sessão no servidor, limpa cookie e dados do painel e
  retorna ao login. Cookie anterior não pode ser reutilizado. Sessão vencida no
  frontend retorna ao login sem repetição automática de gravações. Erro de rede
  é exibido e permite tentar novamente, sem simular autenticação.
- RN58. Interface responsiva, labels e foco visíveis, senha mascarada, Enter
  envia formulário, estado de envio evita duplicidade. Consultar sessão/entrar/sair
  não chama Gemini/OpenAI/NewsAPI e não altera dados de clientes. Multiassessor,
  recuperação de senha e publicação para dados reais continuam fora do recorte.

## Aceites / TDD

- CA79. `/login` público; `/` e `/legacy` redirecionam sem sessão. Todas as rotas
  de dados retornam 401 antes de executar o serviço, inclusive futuras rotas.
- CA80. `admin` / `admin` permite acesso; credenciais erradas/JSON/campos inválidos
  não criam sessão; erro não revela senha. Cookie válido persiste entre requisições.
- CA81. Token CSRF ausente/errado ou de outra sessão bloqueia escrita; token muda
  no login e não é necessário em leitura. Fluxos anteriores passam com login real.
- CA82. Validade de oito horas pelo relógio injetável, inclusive limite exato;
  adulteração e reuso após logout recusados. Reinício preserva sessão e dados.
- CA83. Frontend consulta sessão antes de buscar clientes, envia CSRF em escrita,
  reage a 401 de sessão sem exibir dados anteriores e oferece logout/erro de rede.
- CA84. Login desktop/celular sem rolagem horizontal, logo centralizado, senha
  mascarada, erro de credenciais e sucesso demonstráveis; nenhum “Esqueceu senha”.

## Implementação prevista

1. Blueprint de autenticação, guarda global e tabela aditiva `sessao_acesso`.
2. Testes HTTP com cliente anônimo; testes de domínio passam a entrar pela API.
3. Tela React de login, gate de sessão, painel existente e botão Sair.
4. Testes de comunicação, lint/build, navegador e registro para o pitch.

Configuração de cookie para HTTP local; `SESSION_COOKIE_SECURE=True` quando uma
implantação HTTPS for definida. Referência técnica: [sessões e CSRF no Flask](https://flask.palletsprojects.com/en/stable/web-security/).

## Entrega / evidências

Implementado: backend de sessão revogável/CSRF, React `/login`, acesso antes da
consulta de clientes e botão Sair. TDD: 23 falhas esperadas no backend e cinco
no frontend antes das implementações; após implementação, **352 backend +
11 frontend aprovados**, lint/build sem erro. Testes anteriores entram pela API;
os que avançam vários dias renovam explicitamente o acesso.

Desktop: logo centralizado e formulário conferidos; senha mascarada e erro de
credenciais observados. Painel autenticado com os cinco clientes e síntese anterior
preservados observado no navegador. Conferência adicional de logout/mobile
adiada a pedido do usuário; comportamento HTTP coberto nos testes. Nada de
chamadas externas novas para login. Branch local, sem push nesta etapa.
