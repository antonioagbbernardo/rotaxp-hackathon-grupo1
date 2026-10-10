"""Validação pura dos dados públicos do assessor da demonstração."""
import re

from .agenda_rules import ErroAgenda, corpo, texto

LIMITES = {'name': 120, 'role': 80, 'email': 254, 'phone': 30, 'office': 120}


def validar_perfil(dados):
    dados = corpo(dados, LIMITES, LIMITES)
    perfil = {campo: texto(dados[campo], campo, limite, vazio=campo not in ('name', 'role'))
              for campo, limite in LIMITES.items()}
    if perfil['email'] and not re.fullmatch(r'[^\s@]+@[^\s@.]+(?:\.[^\s@.]+)+', perfil['email']):
        raise ErroAgenda('Informe um e-mail válido.', 'email')
    if perfil['phone'] and (not re.fullmatch(r'[0-9 +().-]+', perfil['phone'])
                             or not re.search(r'[0-9]', perfil['phone'])):
        raise ErroAgenda('Informe um telefone com dígitos e formatação válida.', 'phone')
    return perfil
