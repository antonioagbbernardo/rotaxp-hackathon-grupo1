"""Carga adicional idempotente de dez personas de demonstração, sem apagar a base."""
import json
from datetime import timedelta

import click
from flask import current_app
from .clock import formatar_utc
from .db import get_db

PERSONAS = [
    ('Ana Souza', 'Moderado', 'aposentadoria com renda mensal', ['café', 'Palmeiras'], 'Estou muito satisfeita com nosso acompanhamento. Obrigada pela atenção!', 'positive'),
    ('Bruno Lima', 'Conservador', 'reserva para a família', ['Fórmula 1', 'uva'], 'Fiquei preocupado com a demora do retorno. Preciso de mais clareza sobre os vencimentos.', 'negative'),
    ('Carla Mendes', 'Arrojado', 'independência financeira em dez anos', ['corridas de rua', 'futebol'], 'Gostei bastante da nossa última conversa! Completei minha primeira meia maratona.', 'positive'),
    ('Diego Rocha', 'Moderado', 'compra de um apartamento', ['Corinthians', 'gastronomia'], 'Podemos revisar o planejamento na próxima reunião. Estou tranquilo com os próximos passos.', 'neutral'),
    ('Eva Martins', 'Conservador', 'educação dos filhos', ['café', 'viagens'], 'Não fiquei confortável com a última explicação. Quero entender melhor os riscos.', 'negative'),
    ('Felipe Costa', 'Arrojado', 'expansão da empresa', ['Fórmula 1', 'tecnologia'], 'Excelente acompanhamento! A empresa cresceu e quero rever o planejamento.', 'positive'),
    ('Gabriela Santos', 'Moderado', 'planejamento de intercâmbio', ['cinema', 'viagens'], 'Tudo certo por aqui. Vamos organizar os próximos aportes sem pressa.', 'neutral'),
    ('Henrique Oliveira', 'Conservador', 'preservação de patrimônio', ['Palmeiras', 'café'], 'Estou chateado porque minha dúvida ainda não foi resolvida. Podemos conversar?', 'negative'),
    ('Isabela Ribeiro', 'Arrojado', 'construção de patrimônio', ['futebol', 'fotografia'], 'Adorei a reunião e estou animada com meu planejamento de longo prazo!', 'positive'),
    ('João Ferreira', 'Moderado', 'aposentadoria e viagens', ['Fórmula 1', 'ciclismo'], 'Recebi o material, obrigado. Vou conferir com calma antes da nossa conversa.', 'neutral'),
]


def popular():
    db = get_db()
    if db.execute("SELECT 1 FROM documento_fonte WHERE origem='demo-pulse-v2' LIMIT 1").fetchone():
        _lembrancas(db)
        db.commit()
        return False
    clock = current_app.config['CLOCK']
    agora = clock.agora()
    em = lambda dias: formatar_utc(agora - timedelta(days=dias))
    db.execute('BEGIN IMMEDIATE')
    try:
        db.execute("UPDATE assessor SET nome='Lucas Almeida' WHERE id=1")
        for cid, (nome, perfil, objetivo, interesses, ultima, _) in enumerate(PERSONAS, 1):
            canal = ['whatsapp', 'email', 'telefone'][cid % 3]
            db.execute('INSERT OR IGNORE INTO cliente(id,nome,perfil,canal_preferido,intervalo_minimo_dias,permite_assuntos_pessoais) VALUES(?,?,?,?,14,1)', (cid, nome, perfil, canal))
            db.execute('UPDATE cliente SET nome=?,perfil=?,canal_preferido=?,permite_assuntos_pessoais=1 WHERE id=?', (nome, perfil, canal, cid))
            form = {'nome': nome, 'objetivo': objetivo, 'interesses': ', '.join(interesses),
                    'whatsapp': f'+55 11 0000-{cid:04d}', 'email': f'{nome.split()[0].lower()}@example.com',
                    'cliente_desde': f'{2020 + cid % 5}-03-15', 'aniversario': (clock.hoje() + timedelta(days=cid % 7)).isoformat(),
                    'preferencias': f'Prefere {canal}; reunião mensal e mensagens objetivas.'}
            did = db.execute('INSERT INTO documento_fonte(origem,registro_id,versao,cliente_referencia,cliente_id,tipo,conteudo,ocorrida_em,importada_em) VALUES(?,?,1,?,?,\'formulario\',?,?,?)',
                ('demo-pulse-v2', f'perfil-{cid}', cid, cid, json.dumps(form, ensure_ascii=False), em(0), em(0))).lastrowid
            pid = db.execute("INSERT INTO processamento_contexto(cliente_id,modelo,prompt_versao,assinatura,documentos,estado,inicio_em,fim_em) VALUES(?,'demo-estruturada','demo-v2',?,?,'concluido',?,?)", (cid, f'perfil-{cid}', json.dumps([did]), em(0), em(0))).lastrowid
            for categoria, assunto, campo, valor in [('objetivo', 'planejamento-patrimonial', 'objetivo', objetivo)] + [('interesse', {'Fórmula 1': 'formula-1', 'café': 'cafe'}.get(i, i.lower().replace(' ', '-')), 'interesses', i) for i in interesses]:
                prova = json.dumps([{'documento_id': did, 'campo': campo, 'trecho': valor}], ensure_ascii=False)
                db.execute("INSERT INTO item_contexto(cliente_id,processamento_id,categoria,assunto,sujeito,tipo,valor_original,evidencias,estado,revisao,gerado_em) VALUES(?,?,?,?,'cliente','fato',?,?,'confirmado',1,?)", (cid, pid, categoria, assunto, valor, prova, em(0)))
            mensagens = [
                (18, 'email', f'Olá! Meu objetivo é {objetivo}. Podemos definir juntos os próximos passos?', 'Preparar revisão dos objetivos.'),
                (12, 'telefone', f'Cliente relatou interesse em {interesses[0]} e {interesses[1]}. Prefere contato por {canal}.', 'Personalizar a próxima conversa.'),
                (6, 'whatsapp', 'Recebi o relatório da carteira. Gostaria de entender a distribuição entre as classes e os próximos vencimentos.', 'Explicar composição e prazos.'),
                (3, 'presencial', 'Reunião: alinhamos objetivos, necessidade de liquidez e horizonte. Combinamos revisar a carteira antes de qualquer decisão.', 'Preparar ata e pauta do próximo encontro.'),
                (cid % 3, canal, ultima, 'Retomar os pontos citados pelo cliente na próxima reunião.'),
            ]
            for indice, (dias, canal_msg, texto, passos) in enumerate(mensagens):
                iid = db.execute('INSERT INTO interacao(cliente_id,canal,texto,ocorrida_em,registrada_em,proximos_passos,assessor_id) VALUES(?,?,?,?,?,?,1)', (cid, canal_msg, texto, em(dias), em(dias), passos)).lastrowid
                db.execute("INSERT INTO documento_fonte(origem,registro_id,versao,cliente_referencia,cliente_id,tipo,canal,conteudo,ocorrida_em,importada_em,interacao_id) VALUES(?,?,1,?,?,'interacao',?,?,?,?,?)", ('demo-pulse-v2', f'conversa-{cid}-{indice}', cid, cid, canal_msg, json.dumps(texto, ensure_ascii=False), em(dias), em(0), iid))
            for ativo, valor, prazo in [('CDB Liquidez Diária', str(25000 * cid) + '.00', 35 + cid), ('Fundo Multimercado', str(18000 * cid) + '.00', 180), ('Ações Carteira Brasil', str(8000 * cid) + '.00', 365)]:
                if perfil == 'Conservador' and ativo.startswith('Ações'):
                    ativo = 'Tesouro IPCA+'
                db.execute('INSERT INTO posicao(cliente_id,ativo,valor,vencimento,fonte) VALUES(?,?,?,?,?)', (cid, ativo, valor, (clock.hoje() + timedelta(days=prazo)).isoformat(), 'Carteira de demonstração · posição cadastrada'))
            aniversario = clock.hoje() + timedelta(days=cid % 7)
            db.execute("INSERT INTO data_importante(cliente_id,tipo,vinculo,descricao,dia,mes,fonte) VALUES(?,'aniversario','cliente','Aniversário',?,?,'Formulário inicial · demo-pulse-v2')", (cid, aniversario.day, aniversario.month))
            estado = {'positive': 'positivo', 'negative': 'negativo', 'neutral': 'atencao'}[_]
            db.execute('INSERT INTO avaliacao_relacionamento(cliente_id,estado,justificativa,assessor_id,avaliada_em) VALUES(?,?,?,1,?)', (cid, estado, 'Retomar a percepção expressa no último contato e confirmar os próximos passos.', em(cid % 3)))
            db.execute('INSERT INTO reuniao(cliente_id,assessor_id,objetivo,inicio_em,criada_em,notas) VALUES(?,1,?,?,?,?)', (cid, f'Revisar planejamento: {objetivo}', formatar_utc(agora + timedelta(hours=cid * 2)), em(0), f'Iniciar retomando o último contato. Interesses: {", ".join(interesses)}. Conferir liquidez e objetivos.'))
        _lembrancas(db)
        db.commit()
    except Exception:
        db.rollback()
        raise
    return True


def _lembrancas(db):
    agora = formatar_utc(current_app.config['CLOCK'].agora())
    for f in db.execute("SELECT * FROM documento_fonte WHERE origem='demo-pulse-v2' AND tipo='formulario'").fetchall():
        cid = f['cliente_id']
        assunto = 'aniversario-demo-pulse'
        if db.execute('SELECT 1 FROM item_contexto WHERE cliente_id=? AND assunto=?', (cid, assunto)).fetchone():
            continue
        form = json.loads(f['conteudo'])
        pid = db.execute("SELECT id FROM processamento_contexto WHERE cliente_id=? AND modelo='demo-estruturada'", (cid,)).fetchone()['id']
        data = form['aniversario']
        prova = json.dumps([{'documento_id': f['id'], 'campo': 'aniversario', 'trecho': data}])
        iid = db.execute("INSERT INTO item_contexto(cliente_id,processamento_id,categoria,assunto,sujeito,tipo,valor_original,evidencias,estado,revisao,gerado_em) VALUES(?,?,'data_importante',?,'cliente','fato',?,?,'confirmado',1,?)", (cid, pid, assunto, f'Aniversário em {data}', prova, agora)).lastrowid
        db.execute("INSERT INTO lembranca_contexto(cliente_id,item_id,revisao,tipo,descricao,dia,mes,assessor_id,confirmada_em) VALUES(?,?,1,'aniversario',?,?,?,1,?)", (cid, iid, f"Aniversário de {form['nome']}", int(data[8:10]), int(data[5:7]), agora))


def init_app(app):
    @app.cli.command('popular-pulse')
    def comando():
        click.echo('Demonstração ampliada para dez clientes.' if popular() else 'Demonstração já carregada; registros preservados.')
