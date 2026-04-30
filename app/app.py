from flask import Flask, render_template, request#, redirect, url_for 

app = Flask(__name__)

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

#TODO: El diccionario data debería ser generado dinámicamente a partir de los datos enviados por el formulario
@app.route("/solve", methods=["GET", "POST"])
def resolver():
    if request.method == "POST":
        #data = {} ; Inicializar vacio
        #data["objetivo"] = request.form.get("objetivo")... ; Añadir datos. Quizás en un bucle?
        data={
            "objetivo": request.form.get("objetivo"),
            "cffCj1": request.form.get("cffCj1"),
            "cffCj2": request.form.get("cffCj2"),
            "cffR11": request.form.get("cffR11"),
            "cffR12": request.form.get("cffR12"),
            "operador1": request.form.get("operador1"),
            "valorR1": request.form.get("valorR1")
        }
    return render_template("resultados.html", data=data)

if __name__ == "__main__":
    app.run(debug=True)
