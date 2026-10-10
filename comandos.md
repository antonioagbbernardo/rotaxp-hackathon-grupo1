# Comandos rápidos — Git e terminal

Os exemplos são para o terminal do macOS/zsh. Substitua nomes como
`minha-tarefa`, `arquivo.py` e `URL_DO_REPOSITORIO` pelos valores reais.
Execute os comandos de Git dentro da pasta do repositório.

## Consultar o estado antes de mexer

```bash
git status                 # Branch atual, arquivos alterados e conflitos
git diff                   # Alterações ainda não preparadas para commit
git diff --staged          # Alterações preparadas para o próximo commit
git log --oneline -10      # Últimos 10 commits
git branch                # Branches locais; * indica a atual
git branch -a             # Branches locais e referências remotas conhecidas
git remote -v             # Endereços dos repositórios remotos
```

## Começar: escolha uma das opções

### Baixar um projeto existente

```bash
git clone URL_DO_REPOSITORIO
cd NOME_DA_PASTA_CRIADA
```

### Iniciar Git em uma pasta local

Use quando não houver repositório fornecido. Antes de adicionar arquivos,
prepare um `.gitignore` adequado para excluir `.env`, ambientes virtuais,
dependências e outros arquivos locais que não devem ser versionados.

```bash
git init -b main
git status
git add README.md          # Exemplo: adicione apenas arquivos existentes e revisados
git diff --staged
git commit -m "docs: adiciona instruções iniciais"
git remote add origin URL_DO_REPOSITORIO
git push -u origin main
```

Esse exemplo de primeiro push pressupõe um remoto vazio já criado no serviço
da equipe. Se ele já tiver arquivos/commits, prefira cloná-lo primeiro.

### Identidade dos commits, se o Git solicitar

```bash
git config user.name "Seu Nome"
git config user.email "seu-email@example.com"
```

Essas configurações valem para o repositório atual e não fazem login no serviço.

## Branches: separar o trabalho

```bash
git switch -c minha-tarefa       # Cria uma branch a partir do ponto atual e entra nela
git switch main                 # Troca para uma branch local existente
git switch minha-tarefa
git fetch origin                # Atualiza referências remotas, sem integrar no seu código
git switch --track origin/tarefa-do-colega  # Cria branch local para acompanhar a remota
```

Antes de trocar, confira `git status` e faça commit ou guarde as alterações
com `stash`. Alterações sem commit podem acompanhar a troca de branch.
O nome da branch principal pode ser diferente de `main`.

## Salvar e enviar alterações

```bash
git status
git diff
git add arquivo.py docs/spec.md  # Prepara arquivos específicos
git diff --staged               # Revise o conteúdo exato que será salvo
git commit -m "feat: implementa cadastro"
git push -u origin minha-tarefa # Primeiro envio e configuração do acompanhamento
git push                       # Próximos envios dessa branch
```

- `add`: prepara o conteúdo para o próximo commit.
- `commit`: salva um ponto no histórico local.
- `push`: envia commits ao remoto; não envia alterações sem commit.
- `git add .`: prepara alterações da pasta atual e abaixo; revise para não incluir segredos ou arquivos indevidos.

## Receber e integrar trabalho

```bash
git fetch origin       # Consulta as novidades do remoto
git pull --ff-only     # Atualiza a branch atual pelo remoto que ela acompanha
```

`pull --ff-only` recusa a atualização se os históricos divergirem, permitindo
avaliar antes de criar uma integração. Ele depende de um remoto de acompanhamento
configurado, como no primeiro `push -u`.

Para trazer a branch principal para sua tarefa, com o trabalho salvo:

```bash
git switch minha-tarefa
git fetch origin
git merge origin/main
# Execute as verificações do projeto após integrar.
git push
```

Se o push for rejeitado porque a mesma branch recebeu commits de outra pessoa:

```bash
git fetch origin
git merge origin/minha-tarefa
# Resolva conflitos, se houver, e verifique o resultado antes de enviar.
git push
```

Combine o fluxo com a equipe. No GitHub, um Pull Request (PR) propõe integrar
sua branch à principal para revisão. Não use push forçado para contornar rejeições.

## Resolver conflitos

1. Rode `git status` para identificar os arquivos em conflito.
2. Abra os arquivos e resolva os trechos entre `<<<<<<<`, `=======` e `>>>>>>>`.
3. Preserve o comportamento combinado; não escolha um lado sem ler.
4. Remova os marcadores, salve e execute as verificações relevantes.
5. Conclua o merge:

```bash
git add ARQUIVO_RESOLVIDO
git merge --continue
```

Para cancelar um merge em andamento: `git merge --abort`.
Inicie integrações com o trabalho salvo para facilitar a recuperação.

## Guardar trabalho temporariamente

```bash
git stash push -u -m "trabalho em andamento" # Inclui arquivos novos não ignorados
git stash list
git stash apply                            # Reaplica o último stash, mantendo a cópia
# Confira os arquivos antes de remover a cópia guardada:
git stash drop
```

O stash é local, não é enviado pelo push e sua reaplicação pode gerar conflitos.

## Corrigir enganos

```bash
git restore --staged arquivo.py # Retira do próximo commit, preservando a edição
git revert HASH_DO_COMMIT       # Cria um novo commit que desfaz outro commit
git branch -d tarefa-concluida  # Exclui uma branch local já integrada; saia dela antes
```

**Descarta alterações locais:** `git restore arquivo.py` substitui as edições
não preparadas desse arquivo pelo conteúdo do índice. Confira `git diff` antes.

Evite `git reset --hard`, `git clean -fd` e `git push --force` durante o trabalho
em equipe sem entender exatamente o que será perdido ou sobrescrito.

## Rotina curta em equipe

1. Começo: `git status` → atualizar a principal → criar uma branch de tarefa.
2. Durante: mudanças pequenas → verificar → revisar diff → commit → push.
3. Integração: combinar interfaces, atualizar a tarefa com a principal e abrir PR.
4. Depois de integrar: atualizar a principal local e criar a próxima branch a partir dela.

## Terminal: navegação e arquivos

```bash
pwd                         # Mostra a pasta atual
ls                          # Lista arquivos
ls -la                      # Inclui arquivos ocultos e detalhes
cd caminho/da/pasta          # Entra em uma pasta
cd ..                       # Sobe uma pasta
cd "pasta com espaços"      # Use aspas quando houver espaços
mkdir -p docs               # Cria uma pasta, se necessário
touch notas.md              # Cria arquivo vazio se ele não existir
cat notas.md                # Mostra o conteúdo de um arquivo
less arquivo.log            # Lê por páginas; q sai
cp origem.txt copia.txt     # Copia; pode sobrescrever o destino
mv antigo.txt novo.txt      # Move/renomeia; pode sobrescrever o destino
open .                      # Abre a pasta no Finder (macOS)
```

Atalhos: **Tab** completa nomes; **↑** recupera comandos anteriores;
**Ctrl+C** interrompe o processo atual. Evite `rm -rf` para limpeza apressada.

## Encontrar arquivos, texto e processos

```bash
rg --files                  # Lista arquivos; exige ripgrep instalado
rg "texto" .                # Busca texto no projeto
find . -name '*.py'          # Alternativa para localizar arquivos Python
grep -n "texto" arquivo.py  # Alternativa para buscar dentro de um arquivo
lsof -nP -iTCP:8000 -sTCP:LISTEN # Identifica quem está escutando na porta 8000
curl -i http://localhost:8000/   # Consulta uma rota HTTP e mostra cabeçalhos
```

Se a porta estiver ocupada, prefira encerrar o servidor pelo terminal onde
ele foi iniciado com **Ctrl+C**. Para outro processo, confirme sua identidade
antes de usar `kill PID`.

## Python/Django — apenas se essa for a stack escolhida

Verifique a versão exigida pelo projeto antes de instalar dependências.

```bash
python3 --version
python3 -m venv .venv            # Cria ambiente isolado
source .venv/bin/activate        # Ativa no macOS/zsh
python -m pip --version
python -m pip install -r requirements.txt # Apenas se esse arquivo existir
deactivate                      # Sai do ambiente virtual
```

Com o ambiente ativado, na pasta que contém `manage.py`:

```bash
python manage.py check           # Verificações de configuração do Django
python manage.py runserver       # Servidor local de desenvolvimento
python manage.py test            # Testes pelo executor do Django
python manage.py makemigrations  # Gera migrations após alterações nos models
python manage.py migrate         # Aplica migrations e altera o banco configurado
```

Confirme o banco configurado antes de executar migrations. Se o projeto usar
outro executor de testes, siga o README; esses comandos não foram validados
em uma aplicação desta pasta.

## Node/npm — apenas se o projeto usar

```bash
node --version
npm --version
npm run              # Lista scripts definidos pelo projeto
npm ci               # Instala conforme package-lock.json existente e compatível
```

`npm run dev`, `npm test` e `npm run build` só se aplicam se os respectivos
scripts existirem no `package.json`. Siga o gerenciador e os comandos do README.
