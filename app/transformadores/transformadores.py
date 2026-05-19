"""
Paquete Transformadores — Convierte un ProblemaSimplex en una TablaSimplex.
"""

from __future__ import annotations
from abc import ABC, abstractmethod

from estructura.ProblemaSimplex import ProblemaSimplex
from estructura.TablaSimplex import TablaSimplex
from estructura.TipoRestriccion import TipoRestriccion


class TransformadorTabla(ABC):
    @abstractmethod
    def transformar(self, problema: ProblemaSimplex) -> TablaSimplex: ...

    def _agregar_holguras(
        self,
        tableau: list[list[float]],
        tipos: list[TipoRestriccion],
        offset: int,
    ) -> int:
        for i, tipo in enumerate(tipos):
            if tipo == TipoRestriccion.MENOR:
                tableau[i][offset] = 1.0
                offset += 1
        return offset

    def _agregar_excesos(
        self,
        tableau: list[list[float]],
        tipos: list[TipoRestriccion],
        offset: int,
    ) -> int:
        for i, tipo in enumerate(tipos):
            if tipo == TipoRestriccion.MAYOR:
                tableau[i][offset] = -1.0
                offset += 1
        return offset

    @staticmethod
    def _contar_variables_extra(tipos: list[TipoRestriccion]) -> tuple[int, int]:
        holguras = sum(1 for t in tipos if t == TipoRestriccion.MENOR)
        excesos = sum(1 for t in tipos if t == TipoRestriccion.MAYOR)
        return holguras, excesos


class TransformadorPrimal(TransformadorTabla):
    def transformar(self, problema: ProblemaSimplex) -> TablaSimplex:
        tipos = [r.tipo for r in problema.restricciones]
        n_vars = problema.num_variables
        n_res = problema.num_restricciones
        n_hol, n_exc = self._contar_variables_extra(tipos)
        total_cols = n_vars + n_hol + n_exc

        tableau = [[0.0] * total_cols for _ in range(n_res)]
        recursos = []

        for i, r in enumerate(problema.restricciones):
            for j, c in enumerate(r.coeficientes):
                tableau[i][j] = float(c)
            recursos.append(float(r.recurso))

        offset = n_vars
        offset = self._agregar_holguras(tableau, tipos, offset)
        self._agregar_excesos(tableau, tipos, offset)

        coeficientes = [float(c) for c in problema.coeficientes_objetivo] + [0.0] * (
            n_hol + n_exc
        )
        if not problema.maximizar:
            coeficientes = [-c for c in coeficientes]

        variables_base, coeficientes_base = [], []
        hol_idx = n_vars
        for tipo in tipos:
            if tipo == TipoRestriccion.MENOR:
                variables_base.append(hol_idx)
                coeficientes_base.append(0.0)
                hol_idx += 1
            else:
                variables_base.append(-1)
                coeficientes_base.append(0.0)

        return TablaSimplex(
            coeficientes, tableau, recursos, variables_base, coeficientes_base
        )


class TransformadorDosFases(TransformadorTabla):
    def transformar(self, problema: ProblemaSimplex) -> TablaSimplex:
        tipos = [r.tipo for r in problema.restricciones]
        n_vars = problema.num_variables
        n_res = problema.num_restricciones
        n_hol, n_exc = self._contar_variables_extra(tipos)
        n_art = sum(
            1 for t in tipos if t in (TipoRestriccion.MAYOR, TipoRestriccion.IGUAL)
        )
        total_cols = n_vars + n_hol + n_exc + n_art

        tableau = [[0.0] * total_cols for _ in range(n_res)]
        recursos = []

        for i, r in enumerate(problema.restricciones):
            for j, c in enumerate(r.coeficientes):
                tableau[i][j] = float(c)
            recursos.append(float(r.recurso))

        offset = n_vars
        offset = self._agregar_holguras(tableau, tipos, offset)
        offset = self._agregar_excesos(tableau, tipos, offset)
        self.agregar_artificiales(tableau, tipos, offset)

        coeficientes = [0.0] * (n_vars + n_hol + n_exc) + [1.0] * n_art

        variables_base, coeficientes_base = [], []
        hol_idx = n_vars
        art_idx = n_vars + n_hol + n_exc
        for tipo in tipos:
            if tipo == TipoRestriccion.MENOR:
                variables_base.append(hol_idx)
                coeficientes_base.append(0.0)
                hol_idx += 1
            else:
                variables_base.append(art_idx)
                coeficientes_base.append(1.0)
                art_idx += 1

        # Guardar contexto para prepararFase2
        self._problema = problema
        self._n_vars = n_vars
        self._n_hol = n_hol
        self._n_exc = n_exc

        return TablaSimplex(
            coeficientes, tableau, recursos, variables_base, coeficientes_base
        )

    def agregar_artificiales(
        self,
        tableau: list[list[float]],
        tipos: list[TipoRestriccion],
        offset: int,
    ) -> int:
        for i, tipo in enumerate(tipos):
            if tipo in (TipoRestriccion.MAYOR, TipoRestriccion.IGUAL):
                tableau[i][offset] = 1.0
                offset += 1
        return offset

    def preparar_fase2(self, tabla_fase1: TablaSimplex) -> TablaSimplex:
        problema = self._problema
        cols_mantener = self._n_vars + self._n_hol + self._n_exc

        nuevo_tableau = [fila[:cols_mantener] for fila in tabla_fase1.tableau]
        nuevos_coefs = [float(c) for c in problema.coeficientes_objetivo] + [0.0] * (
            self._n_hol + self._n_exc
        )
        if not problema.maximizar:
            nuevos_coefs = [-c for c in nuevos_coefs]

        nuevos_coefs_base = [
            nuevos_coefs[idx] if 0 <= idx < len(nuevos_coefs) else 0.0
            for idx in tabla_fase1.variables_base
        ]

        return TablaSimplex(
            nuevos_coefs,
            nuevo_tableau,
            list(tabla_fase1.recursos),
            list(tabla_fase1.variables_base),
            nuevos_coefs_base,
        )


class TransformadorDual(TransformadorTabla):
    """
    Transforma un problema primal a su problema dual:
    - Transpone la matriz de coeficientes
    - Los coeficientes de la FO primal → recursos del dual
    - Los recursos del primal → coeficientes de la FO dual
    - Max ↔ Min se invierte
    - ≤ ↔ ≥ se invierte
    - Las variables pasan de x a y
    """

    def transformar(self, problema: ProblemaSimplex) -> TablaSimplex:
        n_vars_primal = problema.num_variables
        n_res_primal = problema.num_restricciones

        # Guardar metadata para poder mapear de vuelta
        self._n_vars_primal = n_vars_primal
        self._n_res_primal = n_res_primal
        self._problema = problema

        # --- Construir el problema dual ---
        # Variables duales: y1..y_m (una por restricción primal)
        # Restricciones duales: n (una por variable primal)
        n_vars_dual = n_res_primal   # variables del dual = restricciones del primal
        n_res_dual = n_vars_primal   # restricciones del dual = variables del primal

        # Coeficientes de la FO dual = recursos del primal
        coefs_fo_dual = [float(r.recurso) for r in problema.restricciones]

        # Restricciones del dual: transponer la matriz de coeficientes
        # Si primal es MAX con ≤, el dual es MIN con ≥
        # Si primal es MIN con ≥, el dual es MAX con ≤
        restricciones_dual_coefs = []
        for j in range(n_vars_primal):
            # Columna j del primal → fila j del dual
            fila = [float(problema.restricciones[i].coeficientes[j]) for i in range(n_res_primal)]
            restricciones_dual_coefs.append(fila)

        # Recursos del dual = coeficientes de la FO primal
        recursos_dual = [float(c) for c in problema.coeficientes_objetivo]

        # Tipo de restricciones del dual
        if problema.maximizar:
            # Primal MAX con ≤ → Dual MIN con ≥
            # Todas las restricciones duales son ≥
            tipo_dual = TipoRestriccion.MAYOR
        else:
            # Primal MIN con ≥ → Dual MAX con ≤
            tipo_dual = TipoRestriccion.MENOR

        # Construir la tabla simplex para el dual
        # Como el dual con ≥ necesita dos fases o tratamiento especial,
        # vamos a convertir a forma estándar:
        # Si dual es MIN con ≥: multiplicamos por -1 para convertir a ≤
        # y luego usamos simplex normal
        if tipo_dual == TipoRestriccion.MAYOR:
            # Dual es MIN con ≥
            # Convertir restricciones ≥ a ≤ multiplicando por -1
            total_cols = n_vars_dual + n_res_dual  # y's + holguras
            tableau = [[0.0] * total_cols for _ in range(n_res_dual)]
            recursos = []

            for i in range(n_res_dual):
                for j in range(n_vars_dual):
                    tableau[i][j] = -restricciones_dual_coefs[i][j]
                recursos.append(-recursos_dual[i])
                tableau[i][n_vars_dual + i] = 1.0  # variable de holgura

            # FO dual: MIN b^T y → como negamos restricciones, la FO queda igual
            # Pero para usar simplex de maximización, negamos la FO:
            # MIN c → MAX -c
            coeficientes = [-c for c in coefs_fo_dual] + [0.0] * n_res_dual
        else:
            # Dual es MAX con ≤ — forma estándar directa
            total_cols = n_vars_dual + n_res_dual
            tableau = [[0.0] * total_cols for _ in range(n_res_dual)]
            recursos = []

            for i in range(n_res_dual):
                for j in range(n_vars_dual):
                    tableau[i][j] = restricciones_dual_coefs[i][j]
                recursos.append(recursos_dual[i])
                tableau[i][n_vars_dual + i] = 1.0

            coeficientes = list(coefs_fo_dual) + [0.0] * n_res_dual

        variables_base = list(range(n_vars_dual, n_vars_dual + n_res_dual))
        coeficientes_base = [0.0] * n_res_dual

        self._n_vars_dual = n_vars_dual
        self._n_res_dual = n_res_dual
        self._dual_maximizar = not problema.maximizar

        return TablaSimplex(
            coeficientes, tableau, recursos, variables_base, coeficientes_base
        )

