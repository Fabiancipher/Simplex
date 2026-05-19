"""
Paquete Implementaciones — Solucionadores concretos.

El método a usar lo elige el frontend (campo 'metodo' en el formulario):
  - 'max'        → SimplexMax
  - 'min'        → SimplexMin
  - 'dos_fases'  → SimplexDosFases
  - 'dual'       → SimplexDual

Cada solucionador valida internamente que el problema sea compatible
con el método elegido antes de ejecutarlo.
"""

from __future__ import annotations

from api.interfaces import SimplexSolucionador
from estructura.ProblemaSimplex import ProblemaSimplex
from estructura.TipoRestriccion import TipoRestriccion
from estructura.ConjuntoSimplex import ConjuntoSimplex
from motor.motor import CriterioFactory
from transformadores.transformadores import (
    TransformadorPrimal,
    TransformadorDosFases,
    TransformadorDual,
)


def _requiere_dos_fases(problema: ProblemaSimplex) -> bool:
    """True si el problema tiene restricciones ≥ o = que requieren artificiales."""
    return any(
        r.tipo in (TipoRestriccion.MAYOR, TipoRestriccion.IGUAL)
        for r in problema.restricciones
    )


class SimplexMax(SimplexSolucionador):
    """Simplex primal de maximización. Solo acepta restricciones ≤."""

    def resolver_simplex(self, problema: ProblemaSimplex) -> ConjuntoSimplex:
        if _requiere_dos_fases(problema):
            raise ValueError(
                "El problema tiene restricciones ≥ o =. "
                "Usa el método Dos Fases para este caso."
            )
        tabla = TransformadorPrimal().transformar(problema)
        conjunto = CriterioFactory.para_maximizacion().ejecutar(tabla)
        conjunto.problema = problema
        return conjunto


class SimplexMin(SimplexSolucionador):
    """Simplex primal de minimización. Solo acepta restricciones ≤."""

    def resolver_simplex(self, problema: ProblemaSimplex) -> ConjuntoSimplex:
        if _requiere_dos_fases(problema):
            raise ValueError(
                "El problema tiene restricciones ≥ o =. "
                "Usa el método Dos Fases para este caso."
            )
        tabla = TransformadorPrimal().transformar(problema)
        conjunto = CriterioFactory.para_maximizacion().ejecutar(tabla)
        conjunto.problema = problema
        for tabla in conjunto.iteraciones:
            tabla.z = -tabla.z
        return conjunto


class SimplexDosFases(SimplexSolucionador):
    """Método de las Dos Fases. Acepta cualquier tipo de restricción."""

    def resolver_simplex(self, problema: ProblemaSimplex) -> ConjuntoSimplex:
        transformador = TransformadorDosFases()

        # Fase 1
        motor_f1 = CriterioFactory.para_dos_fases()
        tabla_f1 = transformador.transformar(problema)
        conjunto_f1 = motor_f1.ejecutar(tabla_f1)

        if abs(conjunto_f1.tabla_final().z) > 1e-8:
            raise ValueError(
                f"Problema infactible (Z' = {conjunto_f1.tabla_final().z:.6f} al final de la Fase 1)."
            )

        # Fase 2
        tabla_f2 = transformador.preparar_fase2(conjunto_f1.tabla_final())
        # Siempre maximizar en Fase 2: preparar_fase2 ya negó los coefs si era minimización
        motor_f2 = CriterioFactory.para_maximizacion()
        conjunto_f2 = motor_f2.ejecutar(tabla_f2)

        if not problema.maximizar:
            for t in conjunto_f2.iteraciones:
                t.z = -t.z

        return ConjuntoSimplex(
            problema=problema,
            iteraciones=conjunto_f1.iteraciones + conjunto_f2.iteraciones,
        )


class SimplexDual(SimplexSolucionador):
    """Método Dual del Simplex."""

    def resolver_simplex(self, problema: ProblemaSimplex) -> ConjuntoSimplex:
        transformador = TransformadorDual()
        tabla = transformador.transformar(problema)

        # Determinar el motor basado en los recursos
        if any(r < 0 for r in tabla.recursos):
            conjunto = CriterioFactory.para_dual().ejecutar(tabla)
        else:
            # Si no hay recursos negativos, se resuelve con simplex normal de maximización
            conjunto = CriterioFactory.para_maximizacion().ejecutar(tabla)
        conjunto.problema = problema

        # Guardar metadata dual para la presentación
        conjunto._dual_metadata = {
            "n_vars_dual": transformador._n_vars_dual,
            "n_res_dual": transformador._n_res_dual,
            "n_vars_primal": transformador._n_vars_primal,
            "dual_maximizar": transformador._dual_maximizar,
        }

        # Si el primal era MAX, el dual es MIN, y Z del dual = Z del primal
        # Negar Z si corresponde (ya que resolvimos como MAX -c)
        if problema.maximizar:
            # Resolvimos MIN como MAX(-c), el Z real es -Z
            for t in conjunto.iteraciones:
                t.z = -t.z

        return conjunto
