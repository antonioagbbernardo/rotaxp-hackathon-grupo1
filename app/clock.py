"""Relógio único e injetável. Nenhuma regra chama date.today()/datetime.now()."""
from datetime import UTC, date, datetime
from zoneinfo import ZoneInfo

TZ = ZoneInfo("America/Sao_Paulo")


class Clock:
    def __init__(self, agora_fn=None):
        self._agora_fn = agora_fn or (lambda: datetime.now(UTC))

    def agora(self) -> datetime:
        """Instante atual, com fuso (UTC)."""
        return self._agora_fn().astimezone(UTC)

    def hoje(self) -> date:
        """Data local em America/Sao_Paulo."""
        return self.agora().astimezone(TZ).date()


def relogio_fixo(instante: datetime) -> Clock:
    """Para testes: instante com fuso; sem fuso é interpretado como America/Sao_Paulo."""
    if instante.tzinfo is None:
        instante = instante.replace(tzinfo=TZ)
    return Clock(lambda: instante)


def parse_instante(texto: str) -> datetime:
    """ISO 8601 -> datetime em UTC. Sem fuso explícito = America/Sao_Paulo. ValueError se inválido."""
    valor = datetime.fromisoformat(texto)
    if valor.tzinfo is None:
        valor = valor.replace(tzinfo=TZ)
    return valor.astimezone(UTC)


def formatar_utc(instante: datetime) -> str:
    """Formato canônico persistido (ordenável como texto)."""
    return instante.astimezone(UTC).isoformat(timespec="microseconds")
