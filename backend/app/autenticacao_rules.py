"""Contrato de credenciais da demonstração; validação sem I/O."""


class ErroCredenciais(ValueError):
    def __init__(self, campo, mensagem):
        self.campo = campo
        super().__init__(mensagem)


def validar_login(corpo):
    if not isinstance(corpo, dict):
        raise ErroCredenciais("corpo", "Envie um objeto JSON com usuário e senha.")
    extras = corpo.keys() - {"usuario", "senha"}
    if extras:
        raise ErroCredenciais(sorted(extras)[0], "Campo não permitido.")
    usuario, senha = corpo.get("usuario"), corpo.get("senha")
    if not isinstance(usuario, str) or not 1 <= len(usuario.strip()) <= 80:
        raise ErroCredenciais("usuario", "Informe um usuário de 1 a 80 caracteres.")
    if not isinstance(senha, str) or not 1 <= len(senha) <= 256:
        raise ErroCredenciais("senha", "Informe uma senha de 1 a 256 caracteres.")
    return usuario.strip(), senha
