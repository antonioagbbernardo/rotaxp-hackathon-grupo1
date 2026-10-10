import type { Client } from '@/types/client'

export const clients: Client[] = [
  {
    id: 'carolina-souza',
    name: 'Carolina Souza',
    pronoun: 'ela',
    status: 'opportunity',
    interests: ['Renda fixa', 'Sustentabilidade'],
    tags: [{ label: 'Moderada' }, { label: 'ESG', highlighted: true }, { label: 'Renda fixa' }],
    sentiment: 'positive',
    headline: 'Nova oportunidade',
    updatedMinutesAgo: 12,
    clientSince: '2023-09',
    lastContactDays: 8,
    whatsapp: '(11) 99999-0142',
    email: 'carolina@exemplo.com',
    perception: [
      { month: '2023-09', sentiment: 'neutral' },
      { month: '2025-05', sentiment: 'negative' },
      { month: '2026-07', sentiment: 'neutral' },
      { month: '2026-10', sentiment: 'positive' },
    ],
    portfolio: {
      total: 480_000,
      goal: 'patrimônio com estabilidade e impacto ESG',
      allocation: [
        { asset: 'fixedIncome', percent: 55 },
        { asset: 'funds', percent: 25 },
        { asset: 'stocks', percent: 20 },
      ],
    },
    news: [
      {
        id: 'green-bonds',
        sentiment: 'positive',
        title: 'Novas emissões verdes ampliam opções de renda fixa',
        whyItMatters: 'Conecta o interesse em sustentabilidade à preferência por renda fixa.',
        relevance: 'Relevância alta · Interesse ESG + renda fixa',
        scenario: 'Cenário simulado 01',
        updatedMinutesAgo: 12,
      },
      {
        id: 'reit-volatility',
        sentiment: 'negative',
        title: 'Volatilidade pressiona fundos imobiliários',
        whyItMatters: 'A parcela em fundos pode gerar preocupação com estabilidade da carteira.',
        relevance: 'Ponto de atenção · Estabilidade + fundos',
        scenario: 'Cenário simulado 02',
        updatedMinutesAgo: 25,
      },
    ],
    assistant: {
      question: 'O que mudou para Carolina e como posso iniciar uma conversa?',
      summary: 'Encontrei uma oportunidade alinhada ao perfil dela e um ponto de atenção.',
      insights: [
        {
          kind: 'opportunity',
          title: 'Uma boa razão para se aproximar',
          body: 'As emissões verdes conectam dois interesses: sustentabilidade e renda fixa.',
        },
        {
          kind: 'concern',
          title: 'Acolha uma possível preocupação',
          body: 'Explique a volatilidade dos fundos sem presumir como ela está se sentindo.',
        },
      ],
      openings: [
        {
          tone: 'Próximo',
          text: 'Oi, Carolina! Lembrei do seu interesse em sustentabilidade ao ver novas opções de renda fixa verde. Quer que eu te explique como elas funcionam e quais riscos vale avaliar? Também podemos conversar sobre a parte de fundos da sua carteira.',
        },
        {
          tone: 'Formal',
          text: 'Olá, Carolina. Surgiram novas emissões de renda fixa com foco sustentável que dialogam com os seus objetivos. Posso apresentar as características e os riscos de cada uma? Aproveito para revisarmos juntos a parcela em fundos.',
        },
        {
          tone: 'Direto',
          text: 'Carolina, saíram títulos verdes de renda fixa que combinam com o seu perfil. Topa 15 minutos esta semana para olharmos isso e a parte de fundos?',
        },
      ],
    },
  },
  {
    id: 'rafael-almeida',
    name: 'Rafael Almeida',
    pronoun: 'ele',
    status: 'attention',
    interests: ['FIIs', 'Renda mensal'],
    tags: [{ label: 'Moderado' }, { label: 'FIIs', highlighted: true }, { label: 'Renda mensal' }],
    sentiment: 'negative',
    headline: 'Revisar exposição',
    updatedMinutesAgo: 25,
    clientSince: '2021-03',
    lastContactDays: 21,
    whatsapp: '(21) 98888-0371',
    email: 'rafael@exemplo.com',
    perception: [
      { month: '2021-03', sentiment: 'positive' },
      { month: '2024-02', sentiment: 'positive' },
      { month: '2025-11', sentiment: 'neutral' },
      { month: '2026-09', sentiment: 'negative' },
    ],
    portfolio: {
      total: 920_000,
      goal: 'renda mensal previsível para complementar a aposentadoria',
      allocation: [
        { asset: 'fixedIncome', percent: 30 },
        { asset: 'funds', percent: 60 },
        { asset: 'stocks', percent: 10 },
      ],
    },
    news: [
      {
        id: 'reit-dividends',
        sentiment: 'negative',
        title: 'Fundos de tijolo revisam distribuição de rendimentos',
        whyItMatters: 'Boa parte da renda mensal dele vem de FIIs de tijolo.',
        relevance: 'Ponto de atenção · Renda mensal + FIIs',
        scenario: 'Cenário simulado 03',
        updatedMinutesAgo: 25,
      },
    ],
    assistant: {
      question: 'O que mudou para Rafael e como posso iniciar uma conversa?',
      summary: 'A renda mensal dele pode cair nos próximos meses. Vale antecipar o contato.',
      insights: [
        {
          kind: 'concern',
          title: 'Antecipe a conversa sobre rendimentos',
          body: 'Mostre o impacto estimado na renda antes que ele perceba no extrato.',
        },
        {
          kind: 'opportunity',
          title: 'Diversificar a fonte de renda',
          body: 'Títulos com pagamento de cupom podem equilibrar a dependência de FIIs.',
        },
      ],
      openings: [
        {
          tone: 'Próximo',
          text: 'Oi, Rafael! Alguns fundos de tijolo anunciaram revisão nos rendimentos. Fiz uma conta rápida do efeito na sua renda mensal e queria te mostrar, junto com algumas alternativas.',
        },
        {
          tone: 'Formal',
          text: 'Olá, Rafael. Houve revisões na distribuição de alguns FIIs presentes na sua carteira. Gostaria de agendar uma conversa para avaliarmos o impacto e possíveis ajustes.',
        },
      ],
    },
  },
  {
    id: 'beatriz-costa',
    name: 'Beatriz Costa',
    pronoun: 'ela',
    status: 'opportunity',
    interests: ['Tecnologia', 'Longo prazo'],
    tags: [{ label: 'Arrojada' }, { label: 'Tecnologia', highlighted: true }, { label: 'Longo prazo' }],
    sentiment: 'positive',
    headline: 'Setor em destaque',
    updatedMinutesAgo: 42,
    clientSince: '2022-06',
    lastContactDays: 14,
    whatsapp: '(31) 97777-0458',
    email: 'beatriz@exemplo.com',
    perception: [
      { month: '2022-06', sentiment: 'positive' },
      { month: '2023-10', sentiment: 'neutral' },
      { month: '2025-04', sentiment: 'positive' },
      { month: '2026-09', sentiment: 'positive' },
    ],
    portfolio: {
      total: 610_000,
      goal: 'crescimento de patrimônio no longo prazo',
      allocation: [
        { asset: 'fixedIncome', percent: 20 },
        { asset: 'funds', percent: 25 },
        { asset: 'stocks', percent: 55 },
      ],
    },
    news: [
      {
        id: 'tech-earnings',
        sentiment: 'positive',
        title: 'Empresas de tecnologia superam projeções do trimestre',
        whyItMatters: 'Mais da metade da carteira dela está em ações, com peso relevante em tecnologia.',
        relevance: 'Relevância alta · Tecnologia + longo prazo',
        scenario: 'Cenário simulado 04',
        updatedMinutesAgo: 42,
      },
    ],
    assistant: {
      question: 'O que mudou para Beatriz e como posso iniciar uma conversa?',
      summary: 'O setor que ela acompanha teve um bom trimestre. É um bom momento para revisar a estratégia.',
      insights: [
        {
          kind: 'opportunity',
          title: 'Converse sobre rebalanceamento',
          body: 'Com a alta recente, a fatia em ações pode ter passado do alvo definido.',
        },
      ],
      openings: [
        {
          tone: 'Próximo',
          text: 'Oi, Beatriz! As empresas de tecnologia que você acompanha tiveram um trimestre forte. Que tal olharmos se a carteira ainda está na proporção que você quer?',
        },
      ],
    },
  },
  {
    id: 'pedro-lima',
    name: 'Pedro Lima',
    pronoun: 'ele',
    status: 'stable',
    interests: ['Conservador', 'Liquidez'],
    tags: [{ label: 'Conservador' }, { label: 'Liquidez', highlighted: true }],
    sentiment: 'neutral',
    headline: 'Sem urgência',
    updatedMinutesAgo: 60,
    clientSince: '2020-01',
    lastContactDays: 30,
    whatsapp: '(41) 96666-0219',
    email: 'pedro@exemplo.com',
    perception: [
      { month: '2020-01', sentiment: 'neutral' },
      { month: '2023-05', sentiment: 'positive' },
      { month: '2025-08', sentiment: 'neutral' },
      { month: '2026-08', sentiment: 'neutral' },
    ],
    portfolio: {
      total: 350_000,
      goal: 'reserva com liquidez diária',
      allocation: [
        { asset: 'fixedIncome', percent: 85 },
        { asset: 'funds', percent: 15 },
        { asset: 'stocks', percent: 0 },
      ],
    },
    news: [
      {
        id: 'selic-hold',
        sentiment: 'neutral',
        title: 'Copom mantém a taxa básica de juros',
        whyItMatters: 'A rentabilidade da reserva dele segue no mesmo patamar.',
        relevance: 'Impacto neutro · Liquidez',
        scenario: 'Cenário simulado 05',
        updatedMinutesAgo: 60,
      },
    ],
    assistant: {
      question: 'O que mudou para Pedro e como posso iniciar uma conversa?',
      summary: 'Nada exige ação imediata. Um contato de rotina mantém o relacionamento próximo.',
      insights: [
        {
          kind: 'opportunity',
          title: 'Contato de manutenção',
          body: 'Faz 30 dias desde a última conversa. Uma atualização breve já é suficiente.',
        },
      ],
      openings: [
        {
          tone: 'Próximo',
          text: 'Oi, Pedro! Passando para contar que a taxa de juros foi mantida, então sua reserva segue rendendo no mesmo ritmo. Se quiser revisar algo, é só me chamar.',
        },
      ],
    },
  },
  {
    id: 'juliana-oliveira',
    name: 'Juliana Oliveira',
    pronoun: 'ela',
    status: 'attention',
    interests: ['Ações', 'Mercado global'],
    tags: [{ label: 'Arrojada' }, { label: 'Global', highlighted: true }, { label: 'Ações' }],
    sentiment: 'negative',
    headline: 'Volatilidade',
    updatedMinutesAgo: 120,
    clientSince: '2024-02',
    lastContactDays: 5,
    whatsapp: '(11) 95555-0987',
    email: 'juliana@exemplo.com',
    perception: [
      { month: '2024-02', sentiment: 'positive' },
      { month: '2025-01', sentiment: 'positive' },
      { month: '2026-03', sentiment: 'neutral' },
      { month: '2026-10', sentiment: 'negative' },
    ],
    portfolio: {
      total: 1_240_000,
      goal: 'exposição internacional com horizonte de dez anos',
      allocation: [
        { asset: 'fixedIncome', percent: 15 },
        { asset: 'funds', percent: 20 },
        { asset: 'stocks', percent: 65 },
      ],
    },
    news: [
      {
        id: 'global-selloff',
        sentiment: 'negative',
        title: 'Bolsas internacionais recuam com tensão comercial',
        whyItMatters: 'A maior parte da carteira dela está em ações globais.',
        relevance: 'Ponto de atenção · Mercado global + ações',
        scenario: 'Cenário simulado 06',
        updatedMinutesAgo: 120,
      },
    ],
    assistant: {
      question: 'O que mudou para Juliana e como posso iniciar uma conversa?',
      summary: 'A queda recente afeta a maior parte da carteira dela. Vale reforçar o horizonte de longo prazo.',
      insights: [
        {
          kind: 'concern',
          title: 'Retome o horizonte combinado',
          body: 'Lembre o objetivo de dez anos antes de discutir qualquer movimentação.',
        },
      ],
      openings: [
        {
          tone: 'Próximo',
          text: 'Oi, Juliana! Vi que as bolsas lá fora tiveram dias difíceis. Quero te mostrar como isso se encaixa no plano de dez anos que montamos. Tem um tempinho esta semana?',
        },
      ],
    },
  },
]
