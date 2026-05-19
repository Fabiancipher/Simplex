from __future__ import annotations


class TablaSimplex:
    def __init__(
        self,
        coeficientes: list[float],
        tableau: list[list[float]],
        recursos: list[float],
        variables_base: list[int],
        coeficientes_base: list[float],
    ) -> None:
        self.coeficientes = coeficientes
        self.tableau = tableau
        self.recursos = recursos
        self.variables_base = variables_base
        self.coeficientes_base = coeficientes_base
        self.zj: list[float] = []
        self.cj_minus_zj: list[float] = []
        self.z: float = 0.0

        self.variable_entrante: int | None = None
        self.variable_saliente: int | None = None

        self.calcular_zj()
        self.calcular_cj_minus_zj()
        self.calcular_z()

    def calcular_zj(self) -> None:
        num_cols = len(self.coeficientes)
        self.zj = []
        for j in range(num_cols):
            suma = 0
            for i in range(len(self.tableau)):
                suma += self.coeficientes_base[i] * self.tableau[i][j]
            self.zj.append(suma)

    def calcular_cj_minus_zj(self) -> None:
        self.cj_minus_zj = []
        for j in range(len(self.coeficientes)):
            self.cj_minus_zj.append(self.coeficientes[j] - self.zj[j])

    def calcular_z(self) -> None:
        suma_total = 0
        for i in range(len(self.recursos)):
            suma_total += self.coeficientes_base[i] * self.recursos[i]
        self.z = suma_total

    def es_optima(self) -> bool:
        return all(v <= 0 for v in self.cj_minus_zj)

    def __repr__(self) -> str:
        return f"TablaSimplex(Z={self.z:.4f}, base={self.variables_base})"
