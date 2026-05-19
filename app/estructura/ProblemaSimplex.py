from __future__ import annotations
from .Restriccion import Restriccion


class ProblemaSimplex:
    def __init__(
        self,
        coeficientes_objetivo: list[float],
        restricciones: list[Restriccion],
        maximizar: bool = True,
    ) -> None:
        if not restricciones:
            raise ValueError("El problema debe tener al menos una restricción.")
        self.coeficientes_objetivo = coeficientes_objetivo
        self.restricciones = restricciones
        self.maximizar = maximizar

    @property
    def num_variables(self) -> int:
        return len(self.coeficientes_objetivo)

    @property
    def num_restricciones(self) -> int:
        return len(self.restricciones)

    def __repr__(self) -> str:
        modo = "MAX" if self.maximizar else "MIN"
        return f"ProblemaSimplex({modo} Z={self.coeficientes_objetivo}, {self.num_restricciones} restricciones)"
