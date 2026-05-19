/**
 * 
 *  Cada input tiene un id único con formato:
         * - cffCj_v{numVariable}: coeficiente de variable j en función objetivo
         * - cffR{numRestriccion}_v{numVariable}: coeficiente variable en restricción
         * - valorR{numRestriccion}: valor derecho de la restricción
 */
function generarTabla() {
            const numVariables = parseInt(document.getElementById('numVariables').value);
            const numRestricciones = parseInt(document.getElementById('numRestricciones').value);

            if (numVariables <= 0 || numRestricciones <= 0) {
                alert('Por favor ingresa números mayores a 0');
                return;
            }
            if (numVariables > 30 || numRestricciones > 30) {
                alert('El máximo permitido es 30 variables y 30 restricciones');
                return;
            }

            const cuerpoTabla = document.getElementById('cuerpoTabla');
            cuerpoTabla.innerHTML = ''; // Limpiar tabla anterior

            // ===== FUNCIÓN OBJETIVO =====
            let filaObjetivo = document.createElement('tr');
            let celdaObjetivo = document.createElement('td');

            let tablaObjetivo = document.createElement('table');
            let tbodyObjetivo = document.createElement('tbody');

            let trObjetivo = document.createElement('tr');

            // Select de método simplex
            let tdSelect = document.createElement('td');
            let selectMetodo = document.createElement('select');
            selectMetodo.id = 'metodo';
            selectMetodo.name = 'metodo';
            selectMetodo.innerHTML = `
                    <option value="dos_fases">Dos Fases</option>
                    <option value="dual">Dual</option>
                `;
            tdSelect.appendChild(selectMetodo);

            // Select de objetivo (max/min) para Dos Fases y Dual
            let selectObjetivo = document.createElement('select');
            selectObjetivo.id = 'objetivo';
            selectObjetivo.name = 'objetivo';
            selectObjetivo.innerHTML = `
                    <option value="max">Maximizar</option>
                    <option value="min">Minimizar</option>
                `;
            selectObjetivo.style.display = 'none';
            selectObjetivo.style.marginLeft = '6px';
            tdSelect.appendChild(selectObjetivo);

            // Mostrar/ocultar selectObjetivo según el método
            function actualizarSelectObjetivo() {
                const metodo = selectMetodo.value;
                if (metodo === 'dos_fases' || metodo === 'dual') {
                    selectObjetivo.style.display = 'inline-block';
                } else {
                    selectObjetivo.style.display = 'none';
                }
            }
            selectMetodo.addEventListener('change', actualizarSelectObjetivo);
            actualizarSelectObjetivo();

            tdSelect.appendChild(document.createTextNode(' Z = '));
            trObjetivo.appendChild(tdSelect);

            function actualizarMetodosDisponibles() {
                const operadores = document.querySelectorAll('select[name^="operador_r"]');

                // Verificar si alguna restricción NO es <= (es decir, es >= o =)
                const tieneRestriccionNoEstandar = Array.from(operadores).some(
                    s => s.value === '>=' || s.value === '='
                );

                const metodoSel = document.getElementById('metodo');
                if (!metodoSel) return;

                const opcionMax = metodoSel.querySelector('option[value="max"]');
                const opcionMin = metodoSel.querySelector('option[value="min"]');

                // El método primal (Max/Min) SOLO funciona con todas las restricciones <=
                // Si hay alguna >= o =, deshabilitar Max y Min
                if (tieneRestriccionNoEstandar) {
                    opcionMax.disabled = true;
                    opcionMin.disabled = true;

                    // Si el usuario tenía seleccionado max o min, cambiar a dos_fases
                    if (metodoSel.value === 'max' || metodoSel.value === 'min') {
                        metodoSel.value = 'dos_fases';
                        actualizarSelectObjetivo();
                        // Mostrar feedback al usuario
                        const mensaje = document.getElementById('mensajeMetodo');
                        if (mensaje) mensaje.style.display = 'block';
                    }
                } else {
                    // Todas las restricciones son <=, habilitar Max y Min
                    opcionMax.disabled = false;
                    opcionMin.disabled = false;
                }
            }
            // Escuchar cambios en operadores (delegación en el tbody)
            document.getElementById('cuerpoTabla').addEventListener('change', function (e) {
                if (e.target.name && e.target.name.startsWith('operador_r')) {
                    actualizarMetodosDisponibles();
                }
            });

            // Generar inputs para cada variable en función objetivo
            for (let j = 1; j <= numVariables; j++) {
                // Input coeficiente
                let tdInput = document.createElement('td');
                let input = document.createElement('input');
                input.type = 'number';
                input.id = `cffCj_v${j}`;
                input.name = `cffCj_v${j}`;
                input.value = '0';
                input.step = 'any';
                tdInput.appendChild(input);
                trObjetivo.appendChild(tdInput);

                // Label variable (X1, X2, etc.)
                let tdVariable = document.createElement('td');
                tdVariable.textContent = `X${j}`;
                if (j < numVariables) {
                    tdVariable.textContent += ' +';
                }
                trObjetivo.appendChild(tdVariable);
            }

            tbodyObjetivo.appendChild(trObjetivo);
            tablaObjetivo.appendChild(tbodyObjetivo);
            celdaObjetivo.appendChild(tablaObjetivo);
            filaObjetivo.appendChild(celdaObjetivo);
            cuerpoTabla.appendChild(filaObjetivo);

            // ===== SEPARADOR "Sujeto a:" =====
            let filaSeparador = document.createElement('tr');
            let tdSeparador = document.createElement('td');
            tdSeparador.setAttribute('class', 'tdSeparador');
            tdSeparador.textContent = 'Sujeto a:';
            filaSeparador.appendChild(tdSeparador);
            cuerpoTabla.appendChild(filaSeparador);

            // ===== RESTRICCIONES =====
            let filaRestricciones = document.createElement('tr');
            let celdaRestricciones = document.createElement('td');

            let tablaRestricciones = document.createElement('table');
            let tbodyRestricciones = document.createElement('tbody');

            // Generar cada restricción
            for (let i = 1; i <= numRestricciones; i++) {
                let trRestriccion = document.createElement('tr');

                // Generar coeficientes para cada variable
                for (let j = 1; j <= numVariables; j++) {
                    // Input coeficiente
                    let tdInput = document.createElement('td');
                    let input = document.createElement('input');
                    input.type = 'number';
                    input.id = `cffR${i}_v${j}`;
                    input.name = `cffR${i}_v${j}`;
                    input.value = '0';
                    input.step = 'any';
                    tdInput.appendChild(input);
                    trRestriccion.appendChild(tdInput);

                    // Label variable
                    let tdVariable = document.createElement('td');
                    tdVariable.textContent = `X${j}`;
                    if (j < numVariables) {
                        tdVariable.textContent += ' +';
                    }
                    trRestriccion.appendChild(tdVariable);
                }

                // Select operador (<=, >=, =)
                let tdOperador = document.createElement('td');
                let selectOperador = document.createElement('select');
                selectOperador.id = `operador_r${i}`;
                selectOperador.name = `operador_r${i}`;
                selectOperador.innerHTML = `
                        <option value=">=">&ge;</option>
                        <option value="<=">&le;</option>
                        <option value="=">=</option>
                    `;
                tdOperador.appendChild(selectOperador);
                trRestriccion.appendChild(tdOperador);

                // Input valor derecho
                let tdValor = document.createElement('td');
                let inputValor = document.createElement('input');
                inputValor.type = 'number';
                inputValor.id = `valorR${i}`;
                inputValor.name = `valorR${i}`;
                inputValor.value = '0';
                inputValor.step = 'any';
                tdValor.appendChild(inputValor);
                trRestriccion.appendChild(tdValor);

                tbodyRestricciones.appendChild(trRestriccion);
            }

            tablaRestricciones.setAttribute('class', 'tablaRestricciones');
            tablaRestricciones.appendChild(tbodyRestricciones);
            celdaRestricciones.appendChild(tablaRestricciones);
            filaRestricciones.appendChild(celdaRestricciones);
            cuerpoTabla.appendChild(filaRestricciones);
        }

        // Event listener para el botón "Generar Tabla"
        document.getElementById('generarBtn').addEventListener('click', generarTabla);

        // ===== PERSISTENCIA CON sessionStorage =====
        function guardarFormulario() {
            const form = document.querySelector('form');
            const data = {};
            const inputs = form.querySelectorAll('input, select');
            inputs.forEach(el => {
                if (el.name) data[el.name] = el.value;
            });
            data['_numVariables'] = document.getElementById('numVariables').value;
            data['_numRestricciones'] = document.getElementById('numRestricciones').value;
            sessionStorage.setItem('simplexFormData', JSON.stringify(data));
        }

        function restaurarFormulario() {
            const raw = sessionStorage.getItem('simplexFormData');
            if (!raw) return;
            const data = JSON.parse(raw);
            if (data['_numVariables']) {
                document.getElementById('numVariables').value = data['_numVariables'];
            }
            if (data['_numRestricciones']) {
                document.getElementById('numRestricciones').value = data['_numRestricciones'];
            }
            // Regenerar la tabla con esas dimensiones
            generarTabla();
            // Restaurar cada valor
            setTimeout(() => {
                Object.keys(data).forEach(key => {
                    if (key.startsWith('_')) return;
                    const el = document.querySelector(`[name="${key}"]`);
                    if (el) el.value = data[key];
                });
            }, 50);
        }

        // Guardar al hacer submit
        document.querySelector('form').addEventListener('submit', guardarFormulario);

        // Al cargar: restaurar si hay datos guardados, si no generar tabla vacía
        window.addEventListener('load', function () {
            if (sessionStorage.getItem('simplexFormData')) {
                restaurarFormulario();
            } else {
                generarTabla();
            }
        });