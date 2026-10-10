"""Validação da agenda sem banco; tempo sempre recebido do Clock."""
from .clock import formatar_utc, parse_instante


class ErroAgenda(Exception):
    def __init__(self, mensagem, campo, status=400, codigo=None):
        self.mensagem, self.campo, self.status = mensagem, campo, status
        self.codigo = codigo or {404: 'nao_encontrado', 409: 'conflito'}.get(status, 'entrada_invalida')


def corpo(corpo, permitidos, obrigatorios=()):
    if not isinstance(corpo, dict):
        raise ErroAgenda('Envie um objeto JSON.', 'corpo')
    extras = corpo.keys() - set(permitidos)
    if extras:
        raise ErroAgenda('Campo não permitido.', sorted(extras)[0])
    for campo in obrigatorios:
        if campo not in corpo:
            raise ErroAgenda('Campo obrigatório.', campo)
    return corpo


def texto(valor, campo, limite=500, vazio=False):
    if not isinstance(valor, str) or len(valor) > limite or (not vazio and not valor.strip()):
        raise ErroAgenda(f'Informe texto {"opcional " if vazio else "obrigatório "}com até {limite} caracteres.', campo)
    return valor.strip()


def inicio(valor):
    try:
        if not isinstance(valor, str) or 'T' not in valor:
            raise ValueError()
        return formatar_utc(parse_instante(valor))
    except ValueError:
        raise ErroAgenda('Informe data e hora ISO 8601 válidas.', 'inicio_em') from None


def proxima(inicio_em, agora):
    return 0 <= (parse_instante(inicio_em) - agora).total_seconds() <= 24 * 60 * 60
