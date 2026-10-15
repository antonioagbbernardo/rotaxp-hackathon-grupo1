"""Cartões paginados com consultas em lote; detalhes somente ao selecionar."""
from collections import defaultdict
import json

from flask import current_app

from . import alertas, humor
from .clock import TZ, formatar_utc, parse_instante
from .db import get_db


def listar(pagina=1, limite=25):
    db,clock=get_db(),current_app.config['CLOCK']
    clientes=db.execute('SELECT * FROM cliente').fetchall()
    def agrupar(sql):
        grupos=defaultdict(list)
        for row in db.execute(sql):
            grupos[row['cliente_id']].append(dict(row))
        return grupos
    posicoes=agrupar('SELECT * FROM posicao ORDER BY vencimento,id')
    datas=agrupar('SELECT * FROM data_importante ORDER BY mes,dia,id')
    tratadas=agrupar('SELECT cliente_id,chave_ocorrencia FROM tratamento_alerta')
    interacoes=agrupar('SELECT * FROM (SELECT id,cliente_id,canal,texto,ocorrida_em, ROW_NUMBER() OVER (PARTITION BY cliente_id ORDER BY ocorrida_em DESC,id DESC) AS n FROM interacao) WHERE n<=12 ORDER BY ocorrida_em DESC,id DESC')
    inferencias={r['cliente_id']:r for r in db.execute('SELECT * FROM humor_inferido')}
    interesses=agrupar("SELECT * FROM item_contexto WHERE categoria='interesse' AND tipo='fato' AND sujeito='cliente' AND estado!='descartado'")
    bloqueios={(r['cliente_id'],r['assunto']) for r in db.execute('SELECT * FROM preferencia_assunto WHERE bloqueado=1')}
    fontes={r['id'] for r in db.execute('SELECT f.id FROM documento_fonte f WHERE f.versao=(SELECT MAX(v.versao) FROM documento_fonte v WHERE v.origem=f.origem AND v.registro_id=f.registro_id)')}
    cards=[]
    for c in clientes:
        cid=c['id']
        conversas=interacoes[cid]
        ultimo=parse_instante(conversas[0]['ocorrida_em']).astimezone(TZ).date() if conversas else None
        pendencias=alertas.calcular_alertas(posicoes[cid],datas[cid],{r['chave_ocorrencia'] for r in tratadas[cid]},clock.hoje(),bool(c['permite_assuntos_pessoais']),c['intervalo_minimo_dias'],ultimo)
        mood=humor.consultar(cid,humor.entrada_dados(conversas,c['nome']),inferencias.get(cid))
        valores=defaultdict(set)
        atuais=[]
        for i in interesses[cid]:
            if not all(e['documento_id'] in fontes for e in json.loads(i['evidencias'])):
                continue
            valor=i['valor_revisado'] or i['valor_original']
            valores[i['assunto']].add(' '.join(valor.casefold().split()))
            atuais.append((i,valor))
        cards.append({'id':str(cid),'name':c['nome'],'photoUrl':f'/assets/avatars/{cid}.jpg' if 1<=cid<=10 else None,
            'priority':alertas.prioridade_do_cliente(pendencias),'nextDue':alertas.proxima_pendencia(pendencias),
            'sentiment':mood['sentiment'],'mood':mood,
            'interests':list(dict.fromkeys(valor for i,valor in atuais if i['estado'] in ('confirmado','corrigido')
                and len(valores[i['assunto']])==1 and (cid,i['assunto']) not in bloqueios))})
    cards.sort(key=lambda c: (('alta','media','baixa').index(c['priority']),c['nextDue'] or '9999',c['name'].casefold()))
    assessor=db.execute('SELECT nome,cargo FROM assessor WHERE id=1').fetchone()
    return {'advisor':{'name':assessor['nome'] if assessor else 'Assessor','role':assessor['cargo'] if assessor else 'Assessor de investimentos'},
        'generatedAt':formatar_utc(clock.agora()),'clients':cards[(pagina-1)*limite:pagina*limite],
        'pagination':{'page':pagina,'limit':limite,'total':len(cards),'pages':max(1,(len(cards)+limite-1)//limite)}}
