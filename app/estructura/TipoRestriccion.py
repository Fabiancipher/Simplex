from __future__ import annotations
from enum import Enum


class TipoRestriccion(Enum):
    MAYOR = ">="
    MENOR = "<="
    IGUAL = "="
