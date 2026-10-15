"""Separação de interlocutores; nenhuma palavra-chave atribui sentimento."""
import re


def falas_investidor(texto, nome=''):
    nomes = ['investidor', 'cliente', 'assessor', 'assistente']
    if nome:
        nomes.extend([nome, nome.split()[0]])
    padrao = r'\b(' + '|'.join(re.escape(n) for n in nomes) + r')\s*:\s*'
    marcadores = list(re.finditer(padrao, texto, re.IGNORECASE))
    if not marcadores:
        return texto
    falas = []
    for n, m in enumerate(marcadores):
        if m.group(1).casefold() in ('assessor', 'assistente'):
            continue
        fim = marcadores[n+1].start() if n+1 < len(marcadores) else len(texto)
        fala = texto[m.end():fim].strip()
        if fala:
            falas.append(fala)
    return '\n'.join(falas)
