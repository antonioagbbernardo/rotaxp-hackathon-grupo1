"""Processo local explícito: notícias compartilhadas e reuniões próximas."""
import json
from threading import Event

import click
from flask import current_app

from . import noticias, reunioes
from .agenda_rules import ErroAgenda, proxima
from .db import get_db


def executar_ciclo():
    resultado = {'noticias': noticias.coletar_diario(), 'reunioes': []}
    rows = get_db().execute("SELECT id,inicio_em FROM reuniao WHERE estado='agendada' ORDER BY inicio_em").fetchall()
    for row in rows:
        if not proxima(row['inicio_em'], current_app.config['CLOCK'].agora()):
            continue
        try:
            preparada = reunioes.preparar(row['id'])
            resultado['reunioes'].append({'id': row['id'], 'pauta_id': preparada['pauta']['id']})
        except ErroAgenda as exc:
            resultado['reunioes'].append({'id': row['id'], 'erro': exc.mensagem})
    return resultado


def init_app(app):
    @app.cli.command('acompanhar-agenda')
    @click.option('--uma-vez', is_flag=True, help='Executa um ciclo e termina.')
    @click.option('--intervalo', default=60, type=click.IntRange(15, 3600), show_default=True)
    def acompanhar(uma_vez, intervalo):
        """Mantém atualizações enquanto este processo local estiver em execução."""
        try:
            while True:
                try:
                    click.echo(json.dumps(executar_ciclo(), ensure_ascii=False))
                except Exception:
                    if uma_vez:
                        raise click.ClickException('Falha no ciclo de atualização; confira a configuração local.') from None
                    click.echo('{"erro":"Falha no ciclo de atualização; próxima tentativa no intervalo configurado."}')
                if uma_vez:
                    break
                Event().wait(intervalo)
        except KeyboardInterrupt:
            click.echo('Acompanhamento encerrado.')
