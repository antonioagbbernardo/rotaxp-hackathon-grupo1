"""Geração explícita, cache persistente e proteção contra resposta obsoleta."""
import json
from uuid import uuid4

from flask import current_app

from .clock import formatar_utc, parse_instante
from .db import get_db
from .ia_openai import OpenAIResumo
from .resumo_ia_rules import ErroResumoIA, assinatura, montar_entrada, validar_saida


def _gerador():
    return current_app.config.get('GERADOR_RESUMO') or OpenAIResumo(
        current_app.config['OPENAI_API_KEY'], current_app.config['OPENAI_MODEL'])


def consultar(cliente):
    gerador = _gerador()
    entrada = montar_entrada(cliente, current_app.config['CLOCK'].hoje())
    sig = assinatura(entrada, gerador.modelo)
    registro = get_db().execute('SELECT * FROM resumo_ia WHERE cliente_id=?', (cliente['id'],)).fetchone()
    resumo = json.loads(registro['resposta']) if registro and registro['estado'] == 'concluido' and registro['assinatura'] == sig else None
    return {'configurado': bool(current_app.config.get('GERADOR_RESUMO') or current_app.config['OPENAI_API_KEY']),
            'modelo': gerador.modelo, 'assinatura': sig, 'resumo': resumo}


def gerar(cliente):
    from .pulse import montar_cliente
    db, clock, gerador = get_db(), current_app.config['CLOCK'], _gerador()
    entrada = montar_entrada(cliente, clock.hoje())
    if len(json.dumps(entrada, ensure_ascii=False)) > 20000:
        raise ErroResumoIA('Os registros excedem o limite de 20 mil caracteres para esta síntese.', 400, 'entrada_invalida')
    sig, tentativa, agora = assinatura(entrada, gerador.modelo), uuid4().hex, clock.agora()
    db.execute('BEGIN IMMEDIATE')
    registro = db.execute('SELECT * FROM resumo_ia WHERE cliente_id=?', (cliente['id'],)).fetchone()
    if registro and registro['estado'] == 'em_processamento' and (agora - parse_instante(registro['inicio_em'])).total_seconds() < 120:
        db.rollback()
        raise ErroResumoIA('Uma síntese já está em andamento para este cliente. Aguarde antes de tentar novamente.', 409, 'em_processamento')
    if registro and registro['estado'] == 'concluido' and registro['assinatura'] == sig:
        db.rollback()
        return {'reutilizado': True, 'resumo': json.loads(registro['resposta'])}
    db.execute("INSERT INTO resumo_ia (cliente_id,assinatura,tentativa,estado,inicio_em,resposta) VALUES (?,?,?,'em_processamento',?,NULL) "
               "ON CONFLICT(cliente_id) DO UPDATE SET assinatura=excluded.assinatura,tentativa=excluded.tentativa,"
               "estado=excluded.estado,inicio_em=excluded.inicio_em,resposta=NULL",
               (cliente['id'], sig, tentativa, formatar_utc(agora)))
    db.commit()  # Não manter lock durante a chamada externa.
    try:
        resposta = gerador.gerar(entrada)
        resumo = validar_saida(resposta['conteudo'], entrada)
        db.execute('BEGIN IMMEDIATE')
        c = db.execute('SELECT * FROM cliente WHERE id=?', (cliente['id'],)).fetchone()
        atual = montar_entrada(montar_cliente(c, incluir_resumo_ia=False), clock.hoje())
        if assinatura(atual, _gerador().modelo) != sig:
            raise ErroResumoIA('Os dados do cliente mudaram. Gere uma nova síntese para usar as informações atuais.', 409, 'dados_alterados')
        resumo.update(modelo=gerador.modelo, gerado_em=formatar_utc(clock.agora()), assinatura=sig, uso=resposta.get('uso', {}))
        alterada = db.execute("UPDATE resumo_ia SET estado='concluido',resposta=? WHERE cliente_id=? AND tentativa=? AND estado='em_processamento'",
                             (json.dumps(resumo, ensure_ascii=False), cliente['id'], tentativa)).rowcount
        if not alterada:
            raise ErroResumoIA('Esta tentativa foi substituída por uma geração mais recente.', 409, 'tentativa_substituida')
        db.commit()
    except Exception:
        db.rollback()
        db.execute("UPDATE resumo_ia SET estado='falhou',resposta=NULL WHERE cliente_id=? AND tentativa=? AND estado='em_processamento'",
                   (cliente['id'], tentativa))
        db.commit()
        raise
    return {'reutilizado': False, 'resumo': resumo}
