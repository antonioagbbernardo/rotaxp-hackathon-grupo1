"""Associação humana, coletas compartilhadas, orçamento e feedback persistente."""
import json
from datetime import datetime, time, timedelta

import click
from flask import current_app

from . import contexto
from .clock import TZ, formatar_utc, parse_instante
from .db import get_db
from .newsapi import NewsAPI
from .noticias_rules import CATALOGO, ErroNoticias, interesse_elegivel, validar_artigos, versao_consulta, assuntos_do_interesse
from .seed import ASSESSOR_ID


def _limite():
    valor = current_app.config['NEWSAPI_LIMITE_DIARIO']
    try:
        if isinstance(valor, bool) or not isinstance(valor, (int, str)):
            raise ValueError()
        limite = int(valor)
        if not 1 <= limite <= 100:
            raise ValueError()
    except ValueError:
        raise ErroNoticias('NEWSAPI_LIMITE_DIARIO deve ser um inteiro de 1 a 100.', status=503, codigo='configuracao_invalida') from None
    return limite


def _configurado():
    return bool(current_app.config.get('COLETOR_NOTICIAS') or current_app.config.get('NEWSAPI_API_KEY'))


def _interesses(cid, itens=None):
    itens = contexto.consultar(cid)['itens'] if itens is None else itens
    return {i['id']: i for i in itens if interesse_elegivel(i)}


def _fontes(item):
    return [f"documento #{e['documento_id']} · {e['origem']} · {e['registro_id']} v{e['versao']}" for e in item['evidencias']]


def _valor(item):
    return item['valor_revisado'] or item['valor_original']


def _vinculos(cid, interesses):
    rows = get_db().execute('SELECT * FROM vinculo_noticia WHERE cliente_id=? AND id IN '
                            '(SELECT MAX(id) FROM vinculo_noticia WHERE cliente_id=? GROUP BY item_id) ORDER BY id', (cid, cid))
    return [{'id': r['id'], 'item_id': r['item_id'], 'revisao': r['revisao'], 'assunto': r['assunto'],
             'interesse': _valor(interesses[r['item_id']]), 'fontes': _fontes(interesses[r['item_id']])}
            for r in rows if r['item_id'] in interesses and r['revisao'] == interesses[r['item_id']]['revisao'] and r['assunto'] in CATALOGO]


def _assuntos_automaticos(cid, itens=None):
    itens = contexto.consultar(cid)['itens'] if itens is None else itens
    legados = _vinculos(cid, _interesses(cid, itens))
    ids_legados = {v['item_id'] for v in legados}
    # Ler notícias não é contatar o cliente: a cadência não impede a preparação.
    # Propostas com evidência literal podem sugerir notícias, sem confirmar o contexto.
    encontrados = legados + [{'id': f"automatico-{i['id']}-{assunto}", 'item_id': i['id'], 'revisao': i['revisao'],
             'assunto': assunto, 'interesse': _valor(i), 'fontes': _fontes(i), 'automatico': True}
            for i in itens if i['id'] not in ids_legados and i['categoria'] == 'interesse' and i['tipo'] == 'fato' and i['sujeito'] == 'cliente'
            and i['estado'] in ('pendente', 'confirmado', 'corrigido') and i['evidencia_atual']
            and not i['conflitos'] and not i['bloqueado']
            for assunto in assuntos_do_interesse(_valor(i))]
    return encontrados or [{'id': 'automatico-mercado', 'item_id': None, 'revisao': 0,
        'assunto': 'mercado', 'interesse': 'Notícias gerais do mercado financeiro', 'fontes': [],
        'automatico': True, 'geral': True}]


def vincular(cid, corpo):
    if not isinstance(corpo, dict) or set(corpo) != {'item_id', 'assunto'}:
        raise ErroNoticias('Informe apenas item_id e assunto do catálogo.', 'item_id')
    iid, assunto = corpo['item_id'], corpo['assunto']
    if type(iid) is not int or not 1 <= iid <= 2**63 - 1:
        raise ErroNoticias('item_id deve ser inteiro positivo.', 'item_id')
    if not isinstance(assunto, str) or assunto not in CATALOGO:
        raise ErroNoticias('Escolha um assunto do catálogo.', 'assunto')
    db = get_db()
    db.execute('BEGIN IMMEDIATE')
    try:
        if not db.execute('SELECT 1 FROM item_contexto WHERE id=? AND cliente_id=?', (iid, cid)).fetchone():
            raise ErroNoticias('Interesse inexistente para este cliente.', 'item_id', 404)
        interesses = _interesses(cid)
        if iid not in interesses:
            raise ErroNoticias('Revisar o interesse e conferir fonte, bloqueio e preferências antes de associar.', 'item_id')
        i = interesses[iid]
        ultimo = db.execute('SELECT * FROM vinculo_noticia WHERE cliente_id=? AND item_id=? ORDER BY id DESC LIMIT 1', (cid, iid)).fetchone()
        if ultimo and ultimo['assunto'] == assunto and ultimo['revisao'] == i['revisao']:
            db.commit()
            return {'vinculo_id': ultimo['id']}, 200
        cur = db.execute('INSERT INTO vinculo_noticia (cliente_id,item_id,revisao,assunto,assessor_id,criada_em) VALUES (?,?,?,?,?,?)',
                         (cid, iid, i['revisao'], assunto, ASSESSOR_ID, formatar_utc(current_app.config['CLOCK'].agora())))
        db.commit()
        return {'vinculo_id': cur.lastrowid}, 201
    except Exception:
        db.rollback()
        raise


def _coletas(assunto):
    return [dict(r) for r in get_db().execute('SELECT * FROM coleta_noticia WHERE assunto=? AND consulta_versao=? ORDER BY id DESC',
                                            (assunto, versao_consulta(assunto)))]


def _chamadas_hoje():
    clock = current_app.config['CLOCK']
    inicio = formatar_utc(datetime.combine(clock.hoje(), time.min, TZ))
    fim = formatar_utc(datetime.combine(clock.hoje() + timedelta(days=1), time.min, TZ))
    return get_db().execute('SELECT COUNT(*) FROM coleta_noticia WHERE inicio_em>=? AND inicio_em<?', (inicio, fim)).fetchone()[0]


def consultar(cid, itens=None):
    db, clock = get_db(), current_app.config['CLOCK']
    interesses = _interesses(cid, itens)
    vinculos = _assuntos_automaticos(cid, itens)
    assuntos, artigos = [], {}
    descartadas = {r[0] for r in db.execute('SELECT artigo_id FROM descarte_noticia WHERE cliente_id=?', (cid,))}
    for assunto in sorted({v['assunto'] for v in vinculos}):
        coletas = _coletas(assunto)
        ultima = coletas[0] if coletas else None
        sucesso = next((r for r in coletas if r['estado'] == 'concluido'), None)
        estado, erro = 'nunca', None
        if sucesso:
            estado = 'atualizado' if parse_instante(sucesso['fim_em']).astimezone(TZ).date() == clock.hoje() else 'desatualizado'
        if ultima and ultima['estado'] == 'em_processamento' and parse_instante(ultima['inicio_em']) > clock.agora() - timedelta(minutes=2):
            estado = 'processando'
        elif ultima and ultima['estado'] == 'falhou':
            estado, erro = 'falhou', {'codigo': ultima['erro_codigo'], 'mensagem': ultima['erro_mensagem']}
        assuntos.append({'id': assunto, 'nome': CATALOGO[assunto]['nome'], 'estado': estado,
                         'ultima_coleta': sucesso['fim_em'] if sucesso else None,
                         'ultima_tentativa': ultima['inicio_em'] if ultima else None, 'erro': erro})
        if not sucesso:
            continue
        vinculo = next(v for v in vinculos if v['assunto'] == assunto)
        for row in db.execute('SELECT dados FROM coleta_artigo_noticia WHERE coleta_id=?', (sucesso['id'],)):
            a = json.loads(row['dados'])
            if a['url'] in descartadas or parse_instante(a['publishedAt']) < clock.agora() - timedelta(days=7):
                continue
            artigos.setdefault(a['url'], {**a, 'id': a['url'], 'sentiment': 'unknown', 'scenario': 'NewsAPI',
                'whyItMatters': ('Notícia geral do mercado financeiro para preparação do assessor; não representa um interesse pessoal inferido.'
                    if vinculo.get('geral') else f"Sugestão automática pelo interesse identificado: {vinculo['interesse']} · " + '; '.join(vinculo['fontes'])),
                'relevance': 'Sugestão de assunto para o assessor revisar.', 'topic': CATALOGO[assunto]['nome'],
                'collectedAt': sucesso['fim_em'],
                'updatedMinutesAgo': max(0, int((clock.agora() - parse_instante(sucesso['fim_em'])).total_seconds() // 60))})
    recentes = sorted(artigos.values(), key=lambda a: (a['publishedAt'], a['url']), reverse=True)
    saida, temas = [], set()
    for a in recentes:
        if a['topic'] not in temas:
            saida.append(a); temas.add(a['topic'])
        if len(saida) == 3:
            break
    for a in recentes:
        if len(saida) == 3:
            break
        if a['id'] not in {r['id'] for r in saida}:
            saida.append(a)
    # GET permanece útil mesmo quando um valor de configuração requer correção.
    try:
        limite = _limite()
    except ErroNoticias:
        limite = None
    return {'configurado': _configurado(), 'catalogo': [{'id': k, 'nome': v['nome']} for k, v in CATALOGO.items()],
            'interesses': [{'id': i['id'], 'revisao': i['revisao'], 'valor': _valor(i), 'fontes': _fontes(i)} for i in interesses.values()],
            'vinculos': vinculos, 'assuntos': assuntos, 'artigos': saida, 'limite_diario': limite, 'chamadas_hoje': _chamadas_hoje()}


def _coletar(assunto, max_idade=None):
    if not _configurado():
        raise ErroNoticias('Configure NEWSAPI_API_KEY no backend e reinicie o servidor.', status=503, codigo='noticias_nao_configuradas')
    limite = _limite()
    db, clock = get_db(), current_app.config['CLOCK']
    agora = clock.agora()
    db.execute('BEGIN IMMEDIATE')
    try:
        coletas = _coletas(assunto)
        ativos = db.execute("SELECT inicio_em FROM coleta_noticia WHERE assunto=? AND estado='em_processamento'", (assunto,))
        if any(parse_instante(r['inicio_em']) > agora - timedelta(minutes=2) for r in ativos):
            raise ErroNoticias('Já existe coleta em andamento para este assunto.', status=409, codigo='coleta_em_andamento')
        sucesso = next((r for r in coletas if r['estado'] == 'concluido'), None)
        if sucesso and parse_instante(sucesso['fim_em']).astimezone(TZ).date() == clock.hoje() and (max_idade is None or parse_instante(sucesso['fim_em']) > agora - max_idade):
            db.commit()
            return {'assunto': assunto, 'estado': 'reutilizado'}
        for r in db.execute("SELECT erro_codigo,fim_em FROM coleta_noticia WHERE estado='falhou' AND erro_codigo IN ('cota_externa','limite_provedor') ORDER BY id DESC"):
            fim = parse_instante(r['fim_em'])
            if r['erro_codigo'] == 'cota_externa' and fim.astimezone(TZ).date() == clock.hoje():
                raise ErroNoticias('Cota externa esgotada; aguarde o próximo dia local.', status=503, codigo='cota_externa')
            if r['erro_codigo'] == 'limite_provedor' and fim > agora - timedelta(minutes=30):
                raise ErroNoticias('NewsAPI limitou as consultas. Aguarde 30 minutos.', status=503, codigo='limite_provedor')
        if coletas and coletas[0]['estado'] == 'falhou':
            intervalo = timedelta(seconds=30) if coletas[0]['erro_codigo'] == 'saida_noticias_invalida' else timedelta(minutes=15)
            if parse_instante(coletas[0]['fim_em']) > agora - intervalo:
                mensagem = 'Aguarde 30 segundos para tentar novamente.' if intervalo == timedelta(seconds=30) else 'Aguarde 15 minutos entre tentativas após uma falha.'
                raise ErroNoticias(mensagem, status=409, codigo='intervalo_coleta')
        if _chamadas_hoje() >= limite:
            raise ErroNoticias('Limite diário local atingido. O cache foi preservado.', status=503, codigo='cota_local')
        db.execute("UPDATE coleta_noticia SET estado='falhou',fim_em=?,erro_codigo='coleta_abandonada',erro_mensagem='Coleta antiga substituída.' WHERE assunto=? AND estado='em_processamento'",
                   (formatar_utc(agora), assunto))
        cur = db.execute("INSERT INTO coleta_noticia (assunto,consulta_versao,estado,inicio_em) VALUES (?,?,'em_processamento',?)",
                         (assunto, versao_consulta(assunto), formatar_utc(agora)))
        pid = cur.lastrowid
        db.commit()
    except Exception:
        db.rollback()
        raise
    try:
        coletor = current_app.config.get('COLETOR_NOTICIAS') or NewsAPI(current_app.config['NEWSAPI_API_KEY'])
        artigos = validar_artigos(coletor.buscar({'q': CATALOGO[assunto]['q']}, agora), agora)
        db.execute('BEGIN IMMEDIATE')
        tentativa = db.execute('SELECT estado FROM coleta_noticia WHERE id=?', (pid,)).fetchone()
        if not tentativa or tentativa['estado'] != 'em_processamento':
            raise ErroNoticias('Coleta substituída por outra tentativa. Recarregue.', status=409, codigo='coleta_substituida')
        for a in artigos:
            db.execute('INSERT OR IGNORE INTO artigo_noticia (url) VALUES (?)', (a['url'],))
            db.execute('INSERT INTO coleta_artigo_noticia (coleta_id,artigo_id,dados) VALUES (?,?,?)',
                       (pid, a['url'], json.dumps(a, ensure_ascii=False)))
        db.execute("UPDATE coleta_noticia SET estado='concluido',fim_em=? WHERE id=?", (formatar_utc(clock.agora()), pid))
        db.commit()
    except Exception as e:
        db.rollback()
        codigo = e.codigo if isinstance(e, ErroNoticias) else 'coleta_interrompida'
        mensagem = e.mensagem if isinstance(e, ErroNoticias) else 'A coleta foi interrompida.'
        db.execute("UPDATE coleta_noticia SET estado='falhou',fim_em=?,erro_codigo=?,erro_mensagem=? WHERE id=? AND estado='em_processamento'",
                   (formatar_utc(clock.agora()), codigo, mensagem, pid))
        db.commit()
        raise
    return {'assunto': assunto, 'estado': 'atualizado'}


def _atualizar_assuntos(assuntos, max_idade=None):
    resultados = []
    for assunto in sorted(set(assuntos)):
        try:
            resultados.append(_coletar(assunto, max_idade))
        except ErroNoticias as e:
            resultados.append({'assunto': assunto, 'estado': 'erro', 'erro': e.resposta()})
    return {'resultados': resultados}


def atualizar(cid, max_idade=None):
    assuntos = {v['assunto'] for v in _assuntos_automaticos(cid)}
    if not assuntos:
        raise ErroNoticias('Nenhum interesse identificado corresponde aos assuntos de notícias disponíveis.', 'interesses')
    return _atualizar_assuntos(assuntos, max_idade)


def descartar(cid, corpo):
    if not isinstance(corpo, dict) or set(corpo) != {'artigo_id', 'motivo'}:
        raise ErroNoticias('Informe artigo_id e motivo.', 'motivo')
    url, motivo = corpo['artigo_id'], corpo['motivo']
    if not isinstance(url, str) or len(url) > 3000:
        raise ErroNoticias('artigo_id deve ser a URL da notícia exibida.', 'artigo_id')
    if not isinstance(motivo, str) or not motivo.strip() or len(motivo) > 1000:
        raise ErroNoticias('Motivo obrigatório, com até mil caracteres.', 'motivo')
    db = get_db()
    db.execute('BEGIN IMMEDIATE')
    try:
        if db.execute('SELECT 1 FROM descarte_noticia WHERE cliente_id=? AND artigo_id=?', (cid, url)).fetchone():
            db.commit()
            return {'descartado': True}
        if url not in {a['id'] for a in consultar(cid)['artigos']}:
            raise ErroNoticias('Notícia não disponível para este cliente.', 'artigo_id', 404)
        db.execute('INSERT INTO descarte_noticia (cliente_id,artigo_id,motivo,assessor_id,descartada_em) VALUES (?,?,?,?,?)',
                   (cid, url, motivo.strip(), ASSESSOR_ID, formatar_utc(current_app.config['CLOCK'].agora())))
        db.commit()
    except Exception:
        db.rollback()
        raise
    return {'descartado': True}


def coletar_diario():
    assuntos = set()
    for r in get_db().execute('SELECT id FROM cliente').fetchall():
        assuntos.update(v['assunto'] for v in _assuntos_automaticos(r['id']))
    return _atualizar_assuntos(assuntos)


def init_app(app):
    @app.cli.command('coletar-noticias')
    def coletar_noticias_command():
        """Coleta assuntos vinculados/elegíveis; reutiliza sucesso do mesmo dia."""
        resultado = coletar_diario()
        click.echo(json.dumps(resultado, ensure_ascii=False))
        if any(r['estado'] == 'erro' for r in resultado['resultados']):
            raise click.ClickException('Uma ou mais coletas falharam; cache anterior preservado.')
