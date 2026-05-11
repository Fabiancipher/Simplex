from flask import Flask, render_template, request#, redirect, url_for 
from static.simplex import Simplex

app = Flask(__name__)

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

#TODO: El diccionario data debería ser generado dinámicamente a partir de los datos enviados por el formulario
@app.route("/solve", methods=["GET", "POST"])
def resolver():
    if request.method == "POST":
        #Obtener numero de variables y restricciones. Se suma 1 para los rangos
        num_variables = int(request.form.get("numVariables"))+1
        num_restricciones = int(request.form.get("numRestricciones"))+1
        
        data = {} #Inicializar diccionario vacio
        data["objetivo"] = request.form.get("objetivo") #Añadir objetivo
        
        #Añadir coeficientes de la funcion objetivo a una lista
        coeficientes_objetivo = []
        for j in range(1, num_variables):
            coeficiente = request.form.get(f"cffCj_v{j}")
            if(coeficiente!=None):
                coeficientes_objetivo.append(coeficiente)
        data["coeficientes"] = coeficientes_objetivo
        
        #Añadir las partes de las restricciones a multiples listas, por su comportamiento queda en orden
        coeficientes_restricciones = [] #Esto es una matriz
        operadores = []
        lado_derecho = []
        for i in range(1, num_restricciones): #Restriccion a restriccion
            restriccion_n = []
            
            operador = request.form.get(f"operador_r{i}")
            if(operador!=None):
                operadores.append(operador)
            
            valor = request.form.get(f"valorR{i}")
            if(valor!=None):
                lado_derecho.append(valor)
                
            for j in range (1, num_variables): #Variable a variable
                restriccion = request.form.get(f"cffR{i}_v{j}")
                if(restriccion!=None):
                    restriccion_n.append(restriccion)
            coeficientes_restricciones.append(restriccion_n)
            
        data["restricciones"] = coeficientes_restricciones
        data["operadores"] = operadores
        data["valores"] = lado_derecho
        #Si se quisieran generar objetos de tipo, por ejemplo, "Restriccion", si este recibe una lista de coeficientes,
        #un operador y un lado derecho, se puede acceder al diccionario con la clave y un indice; ergo:
        #data.get("restricciones")[i] y así con los demás
        
        #Versión anterior
        
        """
        data={
            "objetivo": request.form.get("objetivo"),
            "cffCj1": request.form.get("cffCj1"),
            "cffCj2": request.form.get("cffCj2"),
            "cffR11": request.form.get("cffR11"),
            "cffR12": request.form.get("cffR12"),
            "operador1": request.form.get("operador1"),
            "valorR1": request.form.get("valorR1")
        }
        #Misma cuestión, la función objetivo y las restricciones deberían generarse dinámicamente
        objective = (data["objetivo"], f"{data['cffCj1']}x_1 + {data['cffCj2']}x_2")
        constraints = [f"{data['cffR11']}x_1 + {data['cffR12']}x_2 {data['operador1']} {data['valorR1']}"]
        Lp_system = Simplex(num_vars=2, constraints=constraints, objective_function=objective)
        """
    return render_template("resultados.html", data=data)

if __name__ == "__main__":
    app.run(debug=True)
