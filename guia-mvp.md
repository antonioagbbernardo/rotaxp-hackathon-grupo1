# Guia rápido — construir e dividir um MVP

## 1. Entender antes de programar

- Quem é o usuário e qual problema precisa resolver?
- Quais são as regras, restrições, prazo e formato de entrega?
- Existe código inicial? Leia as instruções e tente executar o que já existe.
- Separe requisitos confirmados, hipóteses e dúvidas que mudam a solução.

## 2. Escolher a menor entrega útil

Complete com a equipe:

> Para [usuário], vamos permitir [ação principal], respeitando [regras].
> Demonstraremos isso por [cenário verificável]. Ficará de fora [escopo adiado].

- Escolha um fluxo completo: entrada → processamento → resultado visível.
- Liste poucos critérios de aceite, cobrindo sucesso e erros importantes.
- Identifique o que não pode falhar: integridade, acesso ou outras regras essenciais.
- Escolha a stack conforme as regras e a familiaridade da equipe.

## 3. Dividir o trabalho

Divida por resultados demonstráveis, com tarefas pequenas. Evite deixar
interface, backend e dados isolados até o final.

| Etapa | Entrega esperada |
| --- | --- |
| Base executável | Projeto roda nas máquinas da equipe; entrega/deploy conferido cedo, se exigido |
| Primeiro fluxo completo | Uma ação principal funciona da entrada ao resultado |
| Regras e erros essenciais | Validações e garantias necessárias estão implementadas e verificadas |
| Entrega | Fluxo revisado, instruções de execução e demonstração prontas |

Para cada tarefa, registre:

> **Resultado:** … · **Responsável:** … · **Depende de:** …
> **Critério de aceite:** … · **Como verificar:** … · **Quando integrar:** …

Para trabalhar em paralelo:

- Combinem antes os dados de entrada, saída e erros entre as partes.
- Distribuam arquivos ou áreas para reduzir conflitos.
- Combinem pontos de integração frequentes e avisem bloqueios cedo.
- Ajustem a divisão ao tamanho da equipe; cada pessoa verifica sua entrega.

## 4. Implementar e validar em ciclos curtos

1. Escolher uma tarefa e revisar seu comportamento esperado.
2. Escrever testes relevantes para as regras; revisar os resultados esperados.
3. Implementar a menor mudança que atende à tarefa.
4. Executar as verificações, revisar o diff e experimentar o fluxo real.
5. Integrar e registrar um ponto de recuperação no Git.

**IA:** use para estruturar requisitos, propor tarefas, escrever testes,
implementar e revisar. Informe objetivo, arquivos relevantes, restrições e
como verificar. Confira regras e resultados; não aceite “funciona” sem evidência.

## 5. Preparar a entrega

- Compare o resultado com os critérios de aceite.
- Teste o fluxo principal e as falhas que comprometem o resultado.
- Registre comandos reais de execução e testes, além das limitações.
- Ensaie: problema → demonstração → decisões → limitações.
- Reserve tempo para integração e apresentação. Se apertar, corte escopo opcional.

**Prioridade perto do prazo:** completar e validar o fluxo principal.
Refatore apenas quando necessário para resolver um impedimento da entrega.
