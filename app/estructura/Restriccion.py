from __future__ import annotations
from .TipoRestriccion import TipoRestriccion


class Restriccion:
    def __init__(
        self,
        coeficientes: list[float],
        tipo: TipoRestriccion,
        recurso: float,
    ) -> None:
        self.coeficientes = coeficientes
        self.tipo = tipo
        self.recurso = recurso

    def __repr__(self) -> str:
        terms = " + ".join(f"{c}·x{i+1}" for i, c in enumerate(self.coeficientes))
        return f"Restriccion({terms} {self.tipo.value} {self.recurso})"
