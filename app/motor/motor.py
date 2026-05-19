"""
Paquete Motor — Estrategias y MotorSimplex.
"""

from __future__ import annotations
import copy

from api.interfaces import CriterioEntradaStrategy, CriterioParadaStrategy
from estructura.TablaSimplex import TablaSimplex
from estructura.ConjuntoSimplex import ConjuntoSimplex

# ── Estrategias de entrada ────────────────────────────────────────────────────


class CriterioEntradaMax(CriterioEntradaStrategy):
    """Elige la columna con mayor Cj-Zj positivo (maximización)."""

    def elegir_columna(self, cj_minus_zj: list[float]) -> int:
        mejor, mejor_val = -1, 1e-8
        for j, val in enumerate(cj_minus_zj):
            if val > mejor_val:
                mejor_val, mejor = val, j
        return mejor


class CriterioEntradaMin(CriterioEntradaStrategy):
    """Elige la columna con Cj-Zj más negativo (minimización)."""

    def elegir_columna(self, cj_minus_zj: list[float]) -> int:
        mejor, mejor_val = -1, -1e-8
        for j, val in enumerate(cj_minus_zj):
            if val < mejor_val:
                mejor_val, mejor = val, j
        return mejor


class CriterioEntradaDual(CriterioEntradaStrategy):
    """Elige la columna con Cj-Zj más negativo (método dual)."""

    def elegir_columna(self, cj_minus_zj: list[float]) -> int:
        mejor, mejor_val = -1, 0.0
        for j, val in enumerate(cj_minus_zj):
            if val < mejor_val:
                mejor_val, mejor = val, j
        return mejor


# ── Estrategias de parada ─────────────────────────────────────────────────────


class CriterioParadaMax(CriterioParadaStrategy):
    """Óptimo cuando todos los Cj-Zj ≤ 0."""

    def es_optima(self, cj_minus_zj: list[float]) -> bool:
        return all(v <= 1e-8 for v in cj_minus_zj)


class CriterioParadaMin(CriterioParadaStrategy):
    """Óptimo cuando todos los Cj-Zj ≥ 0."""

    def es_optima(self, cj_minus_zj: list[float]) -> bool:
        return all(v >= -1e-8 for v in cj_minus_zj)


class CriterioParadaDual(CriterioParadaStrategy):
    """Óptimo dual cuando todos los Cj-Zj ≤ 0."""

    def es_optima(self, cj_minus_zj: list[float]) -> bool:
        return all(v <= 0 for v in cj_minus_zj)


# ── Motor (contexto del patrón Strategy) ─────────────────────────────────────


class MotorSimplex:
    def __init__(
        self,
        criterio_entrada: CriterioEntradaStrategy,
        criterio_parada: CriterioParadaStrategy,
    ) -> None:
        self._criterio_entrada = criterio_entrada
        self._criterio_parada = criterio_parada
        self._tabla: TablaSimplex | None = None

    def ejecutar(self, tabla: TablaSimplex) -> ConjuntoSimplex:
        self._tabla = copy.deepcopy(tabla)
        conjunto = ConjuntoSimplex(problema=None)  # type: ignore[arg-type]
        conjunto.agregar_iteracion(copy.deepcopy(self._tabla))

        while not self._criterio_parada.es_optima(self._tabla.cj_minus_zj):
            col = self._criterio_entrada.elegir_columna(self._tabla.cj_minus_zj)
            if col == -1:
                break

            fila = self._elegir_fila_pivote(col)

            # Guardamos la variable que entra y la que sale en la tabla actual antes de pivotear
            conjunto.iteraciones[-1].variable_entrante = col
            conjunto.iteraciones[-1].variable_saliente = self._tabla.variables_base[
                fila
            ]

            self._pivotear(fila, col)

            self._tabla.variables_base[fila] = col
            self._tabla.coeficientes_base[fila] = self._tabla.coeficientes[col]
            self._tabla.calcular_zj()
            self._tabla.calcular_cj_minus_zj()
            self._tabla.calcular_z()
            conjunto.agregar_iteracion(copy.deepcopy(self._tabla))

        return conjunto

    def _elegir_fila_pivote(self, col: int) -> int:
        min_ratio, fila_pivote = float("inf"), -1
        for i, fila in enumerate(self._tabla.tableau):
            if fila[col] > 1e-8:
                ratio = self._tabla.recursos[i] / fila[col]
                # Modificado para ignorar ratios negativos debido a precisión
                if ratio >= -1e-8 and ratio < min_ratio:
                    min_ratio = max(0.0, ratio)
                    fila_pivote = i
        if fila_pivote == -1:
            raise ValueError(f"Solución no acotada (columna {col}).")
        return fila_pivote

    def _pivotear(self, fila: int, col: int) -> None:
        pivote = self._tabla.tableau[fila][col]
        num_cols = len(self._tabla.coeficientes)
        for j in range(num_cols):
            self._tabla.tableau[fila][j] /= pivote
        self._tabla.recursos[fila] /= pivote
        for i in range(len(self._tabla.tableau)):
            if i == fila:
                continue
            factor = self._tabla.tableau[i][col]
            for j in range(num_cols):
                self._tabla.tableau[i][j] -= factor * self._tabla.tableau[fila][j]
            self._tabla.recursos[i] -= factor * self._tabla.recursos[fila]


# ── Fábrica ───────────────────────────────────────────────────────────────────


class CriterioFactory:
    @staticmethod
    def para_maximizacion() -> MotorSimplex:
        return MotorSimplex(CriterioEntradaMax(), CriterioParadaMax())

    @staticmethod
    def para_minimizacion() -> MotorSimplex:
        return MotorSimplex(CriterioEntradaMin(), CriterioParadaMin())

    @staticmethod
    def para_dos_fases() -> MotorSimplex:
        return MotorSimplex(CriterioEntradaMin(), CriterioParadaMin())

    @staticmethod
    def para_dual() -> MotorDualSimplex:
        return MotorDualSimplex()


class MotorDualSimplex:
    """Motor que implementa el algoritmo Simplex Dual.
    Funciona eligiendo el recurso más negativo (fila) y el mínimo cociente con entradas negativas (columna).
    """

    def ejecutar(self, tabla: TablaSimplex) -> ConjuntoSimplex:
        tabla_actual = copy.deepcopy(tabla)
        conjunto = ConjuntoSimplex(problema=None)  # type: ignore[arg-type]
        conjunto.agregar_iteracion(copy.deepcopy(tabla_actual))

        while True:
            # 1. Elegir fila pivote (el recurso más negativo)
            min_rhs = -1e-8
            fila = -1
            for i, r in enumerate(tabla_actual.recursos):
                if r < min_rhs:
                    min_rhs = r
                    fila = i

            if fila == -1:
                break  # Todos los recursos >= 0, es primalmente factible y por ende óptima

            # 2. Elegir columna pivote (min ratio |Cj - Zj| / |a_ij| con a_ij < 0)
            min_ratio = float("inf")
            col = -1
            num_cols = len(tabla_actual.coeficientes)
            for j in range(num_cols):
                val = tabla_actual.tableau[fila][j]
                if val < -1e-8:
                    ratio = abs(tabla_actual.cj_minus_zj[j] / val)
                    if ratio < min_ratio:
                        min_ratio = ratio
                        col = j

            if col == -1:
                raise ValueError(
                    "El problema primal es infactible (no hay elementos negativos en la fila pivote)."
                )

            # Guardamos la variable que entra y la que sale en la tabla actual antes de pivotear
            conjunto.iteraciones[-1].variable_entrante = col
            conjunto.iteraciones[-1].variable_saliente = tabla_actual.variables_base[
                fila
            ]

            # 3. Pivotear
            self._pivotear(tabla_actual, fila, col)

            tabla_actual.variables_base[fila] = col
            tabla_actual.coeficientes_base[fila] = tabla_actual.coeficientes[col]
            tabla_actual.calcular_zj()
            tabla_actual.calcular_cj_minus_zj()
            tabla_actual.calcular_z()
            conjunto.agregar_iteracion(copy.deepcopy(tabla_actual))

        return conjunto

    def _pivotear(self, tabla: TablaSimplex, fila: int, col: int) -> None:
        pivote = tabla.tableau[fila][col]
        num_cols = len(tabla.coeficientes)
        for j in range(num_cols):
            tabla.tableau[fila][j] /= pivote
        tabla.recursos[fila] /= pivote

        for i in range(len(tabla.tableau)):
            if i == fila:
                continue
            factor = tabla.tableau[i][col]
            for j in range(num_cols):
                tabla.tableau[i][j] -= factor * tabla.tableau[fila][j]
            tabla.recursos[i] -= factor * tabla.recursos[fila]
