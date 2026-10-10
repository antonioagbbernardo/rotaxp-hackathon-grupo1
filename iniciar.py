"""Inicializador portátil. Execute: uv run --locked --project backend iniciar.py."""
import argparse
from pathlib import Path
import shutil
import subprocess

raiz = Path(__file__).resolve().parent
parser = argparse.ArgumentParser()
parser.add_argument('--porta', type=int, default=5001)
parser.add_argument('--sem-build', action='store_true')
args = parser.parse_args()

uv, npm = shutil.which('uv'), shutil.which('npm')
if not uv or not npm:
    raise SystemExit('Instale uv e Node.js 22.18+ (ou 24+) antes de executar.')
if not 1 <= args.porta <= 65535:
    raise SystemExit('Porta inválida.')

def executar(command, cwd):
    subprocess.run(command, cwd=cwd, check=True)

try:
    if not args.sem_build:
        executar([npm, 'ci'], raiz / 'frontend')
        executar([npm, 'run', 'build'], raiz / 'frontend')
    elif not (raiz / 'frontend/dist/index.html').is_file():
        raise SystemExit('Build ausente. Execute novamente sem --sem-build.')
    backend = raiz / 'backend'
    flask = [uv, 'run', '--locked', 'flask', '--app', 'app']
    executar([*flask, 'seed'], backend)
    executar([*flask, 'importar-fontes', 'dados/fonte-demo.json'], backend)
    if not (backend / '.env').is_file():
        shutil.copyfile(backend / '.env.example', backend / '.env')
        (backend / '.env').chmod(0o600)
        print('Configure OPENAI_API_KEY e NEWSAPI_API_KEY em backend/.env para usar as integrações.', flush=True)
    print(f'XP Pulse: http://127.0.0.1:{args.porta}/login · acesso admin/admin', flush=True)
    worker = subprocess.Popen([*flask, 'acompanhar-agenda'], cwd=backend)
    try:
        executar([*flask, 'run', '--host', '127.0.0.1', '--port', str(args.porta)], backend)
    finally:
        worker.terminate()
        worker.wait(timeout=10)
except subprocess.CalledProcessError:
    raise SystemExit('Não foi possível iniciar. Confira o erro mostrado acima.') from None
except KeyboardInterrupt:
    print('Aplicação encerrada.')
