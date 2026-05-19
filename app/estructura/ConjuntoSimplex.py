from __future__ import annotations
from .TablaSimplex import TablaSimplex
from .ProblemaSimplex import ProblemaSimplex


class ConjuntoSimplex:
    def __init__(
        self,
        problema: ProblemaSimplex,
        iteraciones: list[TablaSimplex] | None = None,
    ) -> None:
        self.problema = problema
        self.iteraciones: list[TablaSimplex] = iteraciones or []

    def tabla_inicial(self) -> TablaSimplex:
        if not self.iteraciones:
            raise IndexError("No hay iteraciones registradas.")
        return self.iteraciones[0]

    def tabla_final(self) -> TablaSimplex:
        if not self.iteraciones:
            raise IndexError("No hay iteraciones registradas.")
        return self.iteraciones[-1]

    def numero_iteraciones(self) -> int:
        return len(self.iteraciones)

    def agregar_iteracion(self, tabla: TablaSimplex) -> None:
        self.iteraciones.append(tabla)

    def __repr__(self) -> str:
        z = self.tabla_final().z if self.iteraciones else "N/A"
        return f"ConjuntoSimplex(iteraciones={self.numero_iteraciones()}, Z_final={z})"
