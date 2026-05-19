from flask import Flask, render_template, request

from estructura.ProblemaSimplex import ProblemaSimplex
from estructura.Restriccion import Restriccion
from estructura.TipoRestriccion import TipoRestriccion
from implementaciones import SimplexMax
from implementaciones import SimplexMin
from implementaciones import SimplexDosFases
from implementaciones import SimplexDual

app = Flask(__name__)

OPERADOR_MAP = {
    "<=": TipoRestriccion.MENOR,
    ">=": TipoRestriccion.MAYOR,
    "=": TipoRestriccion.IGUAL,
}

# El frontend elige el método; aquí solo lo instanciamos
METODO_MAP = {
    "max": SimplexMax,
    "min": SimplexMin,
    "dos_fases": SimplexDosFases,
    "dual": SimplexDual,
}


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/solve", methods=["POST"])
def resolver():
    try:
        num_variables = int(request.form.get("numVariables", 2))
        num_restricciones = int(request.form.get("numRestricciones", 2))

        if num_variables > 30 or num_restricciones > 30:
            raise ValueError("El máximo permitido es 30 variables y 30 restricciones.")
        if num_variables < 1 or num_restricciones < 1:
            raise ValueError("Debe haber al menos 1 variable y 1 restricción.")

        metodo = request.form.get("metodo", "max")  # viene del frontend
        objetivo = request.form.get("objetivo", "max")  # para dos_fases y dual

        # dos_fases y dual usan el select de objetivo
        maximizar = objetivo == "max"

        # Coeficientes de la FO
        coeficientes_objetivo = [
            float(request.form.get(f"cffCj_v{j}", 0))
            for j in range(1, num_variables + 1)
        ]

        # Restricciones
        restricciones = []
        for i in range(1, num_restricciones + 1):
            coefs = [
                float(request.form.get(f"cffR{i}_v{j}", 0))
                for j in range(1, num_variables + 1)
            ]
            tipo = OPERADOR_MAP.get(
                request.form.get(f"operador_r{i}", "<="), TipoRestriccion.MENOR
            )
            recurso = float(request.form.get(f"valorR{i}", 0))
            restricciones.append(Restriccion(coefs, tipo, recurso))

        problema = ProblemaSimplex(
            coeficientes_objetivo=coeficientes_objetivo,
            restricciones=restricciones,
            maximizar=maximizar,
        )

        clase_solucionador = METODO_MAP.get(metodo)
        if clase_solucionador is None:
            raise ValueError(f"Método desconocido: '{metodo}'.")

        resultado = clase_solucionador().resolver_simplex(problema)

        # Preparar datos para la plantilla
        es_dual = metodo == "dual" and hasattr(resultado, "_dual_metadata")

        if es_dual:
            meta = resultado._dual_metadata
            n_vars_dual = meta["n_vars_dual"]
            n_res_dual = meta["n_res_dual"]
            n_dec = n_vars_dual

            def get_nombres_variables(num_cols):
                nombres = [f"Y{j+1}" for j in range(n_vars_dual)]
                nombres += [f"s{j+1}" for j in range(num_cols - n_vars_dual)]
                return nombres

            def nombre_var(self, idx): #Dos argumentos necesarios por cosas de Python. Ignorar
                if idx < n_vars_dual:
                    return f"Y{idx+1}"
                else:
                    return f"s{idx - n_vars_dual + 1}"

        else:
            n_dec = problema.num_variables
            n_hol = sum(
                1 for r in problema.restricciones if r.tipo == TipoRestriccion.MENOR
            )
            n_exc = sum(
                1 for r in problema.restricciones if r.tipo == TipoRestriccion.MAYOR
            )

            def get_nombres_variables(num_cols):
                nombres = [f"X{j+1}" for j in range(n_dec)]
                nombres += [f"s{j+1}" for j in range(num_cols - n_dec)]
                if num_cols > n_dec + n_hol + n_exc: #El método sí o sí es DF
                    nombres = [f"X{j+1}" for j in range(n_dec)]
                    nombres += [f"s{j+1}" for j in range(n_hol + n_exc)]
                    num_art = num_cols - (n_dec + n_hol + n_exc)
                    nombres += [f"A{j+1}" for j in range(num_art)]
                return nombres

            def nombre_var(idx, num_cols):
                if idx < n_dec:
                    return f"X{idx+1}"
                elif (
                    num_cols > n_dec + n_hol + n_exc
                    and idx >= n_dec + n_hol + n_exc
                ):
                    return f"A{idx - (n_dec + n_hol + n_exc) + 1}"
                else:
                    return f"s{idx - n_dec + 1}"

        iteraciones_data = []
        for i_idx, tabla in enumerate(resultado.iteraciones):
            num_cols = len(tabla.coeficientes)
            encabezados_iter = get_nombres_variables(num_cols)
            filas = [
                {
                    "base": nombre_var(tabla.variables_base[i], num_cols),
                    "cbase": round(tabla.coeficientes_base[i], 4),
                    "coefs": [round(v, 4) for v in fila],
                    "recurso": round(tabla.recursos[i], 4),
                }
                for i, fila in enumerate(tabla.tableau)
            ]

            entrante_str = (
                nombre_var(tabla.variable_entrante, num_cols)
                if getattr(tabla, "variable_entrante", None) is not None
                else None
            )
            saliente_str = (
                nombre_var(tabla.variable_saliente, num_cols)
                if getattr(tabla, "variable_saliente", None) is not None
                else None
            )

            iteraciones_data.append(
                {
                    "numero": i_idx,
                    "encabezados": encabezados_iter,
                    "coeficientes_cj": [round(v, 4) for v in tabla.coeficientes],
                    "filas": filas,
                    "zj": [round(v, 4) for v in tabla.zj],
                    "cj_minus_zj": [round(v, 4) for v in tabla.cj_minus_zj],
                    "z": round(tabla.z, 4),
                    "optima": tabla.es_optima(),
                    "entrante": entrante_str,
                    "saliente": saliente_str,
                }
            )

        tabla_final = resultado.tabla_final()

        if es_dual:
            # Solución dual en variables Y
            solucion_dual = {f"Y{j+1}": 0.0 for j in range(n_vars_dual)}
            for i, var_idx in enumerate(tabla_final.variables_base):
                if 0 <= var_idx < n_vars_dual:
                    solucion_dual[f"Y{var_idx+1}"] = round(tabla_final.recursos[i], 4)

            # Solución primal desde los valores de Cj-Zj de las holguras
            solucion_primal = {}
            for j in range(n_res_dual):
                idx_holgura = n_vars_dual + j
                if idx_holgura < len(tabla_final.cj_minus_zj):
                    val = abs(round(tabla_final.cj_minus_zj[idx_holgura], 4))
                    solucion_primal[f"X{j+1}"] = val

            solucion = solucion_dual
            solucion_primal_data = solucion_primal
        else:
            solucion = {f"X{j+1}": 0.0 for j in range(n_dec)}
            for i, var_idx in enumerate(tabla_final.variables_base):
                if 0 <= var_idx < n_dec:
                    solucion[f"X{var_idx+1}"] = round(tabla_final.recursos[i], 4)
            solucion_primal_data = None


        return render_template(
            "resultados.html",
            metodo=metodo,
            maximizar=maximizar,
            es_dual=es_dual,
            iteraciones=iteraciones_data,
            solucion=solucion,
            solucion_primal=solucion_primal_data,
            z_optimo=round(tabla_final.z, 4),
            num_iteraciones=resultado.numero_iteraciones(),
        )

    except ValueError as e:
        return render_template("resultados.html", error=str(e))
    except Exception as e:
        return render_template("resultados.html", error=f"Error inesperado: {e}")


if __name__ == "__main__":
    app.run(debug=True)
