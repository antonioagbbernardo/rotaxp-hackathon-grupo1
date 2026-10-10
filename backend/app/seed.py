"""Dados fictícios com vencimentos relativos à data de execução (−2, 0, 5, 7, 8, 30, 31 dias)."""
from datetime import date, datetime, timedelta

import click
from flask import Flask

from .clock import formatar_utc
from .db import drop_all, get_db, init_db

AVISO = "Dados fictícios para demonstração"
ASSESSOR_ID = 1


def seed_db(hoje: date, agora: datetime) -> bool:
    """Popula somente base vazia. Devolve False (sem alterar nada) se já houver dados."""
    db = get_db()
    if db.execute("SELECT 1 FROM cliente LIMIT 1").fetchone() or db.execute("SELECT 1 FROM assessor LIMIT 1").fetchone():
        return False
    d = lambda dias: (hoje + timedelta(days=dias)).isoformat()  # noqa: E731
    em = lambda dias: formatar_utc(agora - timedelta(days=dias))  # noqa: E731
    aniv = lambda dias: hoje + timedelta(days=dias)  # noqa: E731

    db.execute("INSERT INTO assessor (id, nome) VALUES (?, ?)", (ASSESSOR_ID, "Assessor Fictício"))
    clientes = [  # id, nome, perfil, canal, intervalo, permite
        (1, "Ana Souza (fictício)", "Moderado; objetivo: aposentadoria", "telefone", 7, 1),
        (2, "Bruno Lima (fictício)", "Conservador", "email", 14, 0),
        (3, "Carla Mendes (fictício)", "Arrojado", "whatsapp", 14, 1),
        (4, "Diego Rocha (fictício)", "Moderado", None, 7, 0),
        (5, "Eva Martins (fictício)", "", None, 30, 1),
    ]
    for c in clientes:
        db.execute(
            "INSERT INTO cliente (id, nome, perfil, canal_preferido, intervalo_minimo_dias, permite_assuntos_pessoais)"
            " VALUES (?,?,?,?,?,?)", c)
    posicoes = [  # cliente, ativo, valor, Δ
        (1, "CDB Banco Exemplo", "50000.00", 5),
        (1, "LCI Banco Exemplo", "30000.00", 31),
        (2, "Debênture Exemplo", "20000.00", -2),
        (2, "Tesouro Exemplo", "10000.00", 0),
        (3, "CRA Exemplo", "80000.00", 7),
        (3, "LCA Exemplo", "15000.00", 8),
        (4, "CDB Exemplo 2", "25000.00", 30),
    ]
    for cid, ativo, valor, delta in posicoes:
        db.execute("INSERT INTO posicao (cliente_id, ativo, valor, vencimento, fonte) VALUES (?,?,?,?,?)",
                   (cid, ativo, valor, d(delta), AVISO))
    datas = [(1, "familiar", "filha", aniv(3)), (2, "cliente", "próprio", aniv(3)), (3, "familiar", "esposa", aniv(5))]
    for cid, vinculo, desc, quando in datas:
        db.execute(
            "INSERT INTO data_importante (cliente_id, tipo, vinculo, descricao, dia, mes) VALUES (?,?,?,?,?,?)",
            (cid, "aniversario", vinculo, desc, quando.day, quando.month))
    interacoes = [  # cliente, canal, texto, dias atrás, próximos passos
        # Cliente 1 - Ana Souza (intervalo mínimo: 7 dias)
        (1, "telefone",
         "[Transcrição de Áudio — XP Voice · Duração: 03:45]\nAssessor: 'Olá, Ana! Tudo bem? Estou te ligando para alinharmos o vencimento do seu CDB de R$ 50.000, previsto para daqui a alguns dias.'\nAna: 'Oi! Tudo ótimo por aqui. Que bom que me ligou, na correria eu nem lembrava da data exata. O que você recomenda para reaplicar esse valor?'\nAssessor: 'Pelo seu perfil moderado e com foco na aposentadoria, selecionei duas alternativas: um CDB indexado ao IPCA e uma LCI isenta de Imposto de Renda. Posso te enviar as simulações detalhadas?'\nAna: 'Com certeza! Pode mandar sim. E a propósito, minha filha faz aniversário mês que vem, então quero manter uma pequena reserva caso façamos uma viagem.'\nAssessor: 'Excelente lembrança, Ana! Já vou reservar essa liquidez no nosso planejamento. Te envio as opções hoje mesmo.'\nAna: 'Combinado, muito obrigada pela atenção!'",
         8, "Enviar lâmina comparativa de LCI isenta e CDB IPCA+."),
        (1, "whatsapp",
         "Ana: 'Oi! Vi o resumo que você mandou sobre a LCI IPCA+. A taxa de 6,8% me pareceu excelente para o vencimento do meu CDB!'\nAssessor: 'Olá, Ana! Que bom que gostou. Como o seu objetivo é a aposentadoria, essa taxa garante ganho real protegido da inflação. Quer que eu faça a alocação hoje?'\nAna: 'Pode alocar sim, por favor!'",
         10, "Confirmar aplicação de R$ 50.000 em LCI IPCA+ 6,8%."),
        (1, "email",
         "De: Ana Souza <ana.souza@exemplo.com>\nPara: assessor@xp.com.br\nAssunto: Extrato e planejamento mensal\n\n'Olá! Poderia me encaminhar o extrato consolidado com a posição atualizada da minha carteira? Gostaria de analisar a rentabilidade deste trimestre antes de decidirmos os próximos aportes. Um abraço, Ana.'",
         15, "Extrato trimestral consolidado enviado por e-mail."),
        # Cliente 2 - Bruno Lima
        (2, "email",
         "De: Bruno Lima <bruno.lima@exemplo.com>\nPara: assessor@xp.com.br\nAssunto: Re: Posição de renda fixa e vencimentos de outubro\n\n'Prezado assessor, recebi a notificação sobre a debênture vencida e o Tesouro com vencimento hoje. Solicito o envio formal por e-mail de 3 alternativas estritamente conservadoras (CDB 100%+ CDI com FGC ou Tesouro Selic) para reaplicação do capital. Por favor, mantenha nosso contato exclusivamente por e-mail com dados técnicos.'",
         1, "Apresentar comparativo de 3 opções conservadoras com garantia do FGC via e-mail."),
        (2, "telefone",
         "[Transcrição de Áudio — XP Voice · Duração: 01:52]\nAssessor: 'Sr. Bruno, bom dia. Sou seu assessor da XP, entrando em contato a respeito da debênture de R$ 20.000 com vencimento recente.'\nBruno: 'Bom dia. Como informei no meu cadastro, prefiro que assuntos de carteira sejam tratados por e-mail com relatórios anexos, para que eu possa avaliar com calma os números.'\nAssessor: 'Compreendo perfeitamente, Sr. Bruno. Respeitamos seu canal de preferência. Vou compilar as taxas e enviar diretamente para sua caixa de entrada.'\nBruno: 'Agradeço a atenção. Fico no aguardo do material por e-mail.'",
         3, "Enviar relatório técnico formal por e-mail."),
        (2, "email",
         "De: Bruno Lima <bruno.lima@exemplo.com>\nPara: assessor@xp.com.br\nAssunto: Solicitação de revisão conservadora\n\n'Gostaria de uma revisão periódica das posições de renda fixa antes dos vencimentos de outubro. Favor atentar para o perfil conservador sem exposição a risco de crédito privado.'",
         4, None),
        # Cliente 3 - Carla Mendes (intervalo mínimo: 14 dias)
        (3, "telefone",
         "[Transcrição de Áudio — XP Voice · Duração: 04:15]\nCarla: 'Fala! Tudo bem? Te ligando rapidinho entre um treino de corrida e o trabalho.'\nAssessor: 'Tudo ótimo, Carla! Vi que seu CRA de R$ 80.000 vence na semana que vem. Já pensou onde quer alocar o resgate?'\nCarla: 'Quero algo arrojado dessa vez! Talvez um fundo de ações internacional ou debênture incentivada com yield bem alto. Minha esposa também faz aniversário daqui a pouco, mas quero o dinheiro trabalhando forte.'\nAssessor: 'Perfeito! Posso montar uma cesta com debêntures incentivadas de infraestrutura e uma fatia em renda variável global.'\nCarla: 'Excelente! Manda no WhatsApp assim que tiver pronto que eu dou o ok.'",
         15, "Estruturar cesta agressiva com debêntures de infraestrutura e BDRs."),
        (3, "whatsapp",
         "Carla: 'E aí! Vi que saiu o prospecto do novo IPO de tecnologia. Tem cota disponível pra mim?'\nAssessor: 'Oi Carla! Tem sim, a procura está alta mas consigo garantir sua reserva. Como seu perfil é arrojado, se encaixa muito bem na estratégia.'\nCarla: 'Top! Pode reservar R$ 20.000 para a minha conta!'",
         20, "Executar reserva de IPO no sistema XP."),
        (3, "whatsapp",
         "Carla: 'Você viu a matéria sobre a maratona no Rio? Mês que vem tô confirmada! Depois me manda como ficaram os fundos multimercado.'\nAssessor: 'Parabéns pela maratona, Carla! Vou atualizar a lâmina dos multimercados e te envio logo mais.'",
         25, None),
        # Cliente 4 - Diego Rocha
        (4, "telefone",
         "[Transcrição de Áudio — XP Voice · Duração: 02:30]\nAssessor: 'Olá Diego, tudo bem? Estou fazendo nosso alinhamento de rotina da carteira.'\nDiego: 'Tudo bem por aqui! Como estão as projeções para os CDBs?'\nAssessor: 'Temos um CDB de R$ 25.000 vencendo daqui a 30 dias. Estou ligando com antecedência para monitorarmos as melhores taxas do mercado.'\nDiego: 'Bacana! Muito bom você antecipar isso. Quando faltarem uns 10 dias me dá um toque com as taxas atualizadas.'\nAssessor: 'Combinado, Diego! Agendarei nosso próximo contato para essa data.'",
         2, "Retomar contato a 10 dias do vencimento com grade de taxas."),
        (4, "whatsapp",
         "Diego: 'Bom dia! Recebi o relatório semanal de mercado da XP. Muito bom o resumo sobre a curva de juros!'\nAssessor: 'Que ótimo que acompanhou, Diego! Qualquer dúvida sobre o impacto nos seus títulos, estou à disposição.'",
         6, None),
    ]
    for cid, canal, texto, dias, passos in interacoes:
        db.execute(
            "INSERT INTO interacao (cliente_id, canal, texto, ocorrida_em, registrada_em, proximos_passos, assessor_id)"
            " VALUES (?,?,?,?,?,?,?)", (cid, canal, texto, em(dias), em(dias), passos, ASSESSOR_ID))
    db.execute(
        "INSERT INTO avaliacao_relacionamento (cliente_id, estado, justificativa, assessor_id, avaliada_em)"
        " VALUES (2, 'atencao', 'Pediu revisão da carteira e há vencimentos pendentes.', ?, ?)",
        (ASSESSOR_ID, em(4)))
    db.commit()
    return True


def init_app(app: Flask) -> None:
    from . import demo_pulse
    demo_pulse.init_app(app)
    @app.cli.command("seed")
    def seed_command():
        """Popula dados fictícios somente se a base estiver vazia."""
        init_db()
        clock = app.config["CLOCK"]
        if seed_db(clock.hoje(), clock.agora()):
            click.echo("Banco populado com dados fictícios.")
        else:
            click.echo("Base já possui dados; nada foi alterado (use reset-demo para reconstruir).")

    @app.cli.command("reset-demo")
    def reset_command():
        """Apaga tudo e reconstrói os dados fictícios da demonstração."""
        drop_all()
        init_db()
        clock = app.config["CLOCK"]
        seed_db(clock.hoje(), clock.agora())
        click.echo("Demonstração reconstruída.")
