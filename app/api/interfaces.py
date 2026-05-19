"""
Paquete API — Contratos / interfaces del sistema Simplex.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from estructura import ProblemaSimplex, ConjuntoSimplex


class SimplexSolucionador(ABC):
    @abstractmethod
    def resolver_simplex(self, problema: "ProblemaSimplex") -> "ConjuntoSimplex": ...


class CriterioEntradaStrategy(ABC):
    @abstractmethod
    def elegir_columna(self, cj_minus_zj: list[float]) -> int: ...


class CriterioParadaStrategy(ABC):
    @abstractmethod
    def es_optima(self, cj_minus_zj: list[float]) -> bool: ...
