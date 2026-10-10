# Incremento 10 — perfil do assessor

Pedido autorizado: abrir o perfil ao clicar no assessor do cabeçalho, editar e
salvar seus dados no design XP Pulse. RF32, sem gestão de outras contas.

- RN76: o perfil pertence ao assessor único da demonstração. Nome (1–120) e
  cargo (1–80) são obrigatórios; e-mail (até 254), telefone (até 30) e escritório
  (até 120) são opcionais. Campos textuais recebem trim. E-mail preenchido exige
  formato local@domínio com extensão; telefone aceita dígitos, espaços e +().-.
- RN77: salvar é atômico; campo ausente, extra, tipo ou formato inválido retorna
  erro com campo e não modifica o perfil. Não altera credenciais nem clientes.
- RN78: somente sessão autenticada consulta o perfil; escrita exige CSRF.

## Aceites

- CA99: clicar no nome/avatar (inclusive no celular) abre `#/perfil`, com dados
  atuais e campos rotulados. Voltar ao painel preserva o cliente selecionado.
- CA100: salvar dados válidos persiste após recarga/reinício e atualiza nome,
  iniciais e cargo do cabeçalho. Exibir confirmação e bloquear envio duplicado.
- CA101: cancelar restaura os dados salvos; falha mantém a edição e permite
  tentar novamente. Entrada inválida não persiste; API identifica campo.
- CA102: sessão/CSRF protegem o perfil; migração preserva assessor e vínculos.
  Desktop e celular sem rolagem horizontal, foco visível e navegação por teclado.

Sem upload de foto, alteração de senha, novas contas ou envio de mensagens.
