# Justificación del universo

El Observatorio estudia cómo la tecnología cambia a las empresas. Para eso necesita el sector que produce tecnología, completo, y los sectores de mayor peso económico como comparación. Cubrir las 21 secciones de la CIIU con dos personas en nueve meses obligaría a hacerlo de forma superficial, así que se priorizó la profundidad.

## Por qué estos sectores

**Rol frente a la tecnología.**

| Rol | Grupo | Motivo |
| --- | --- | --- |
| Productor | TEC | Objeto principal del estudio; entran todas |
| Adoptante con mayor peso económico | G, C | Comercio electrónico, logística, automatización |
| Adoptante intensivo en conocimiento | M, K | La digitalización cambia su oferta: consultoras digitales (Sofka, PwC), pagos electrónicos (Datafast, Banred) |

**Peso económico.** Participación en las ventas 2025 de todas las sociedades del ranking (USD 177.353 M):

| Sección | Ventas | ¿Entra? |
| --- | --- | --- |
| G Comercio | 40,8 % | Sí |
| C Manufactura | 18,0 % | Sí |
| A Agro primario | 12,1 % | No; la agroindustria entra en C |
| H Transporte | 5,5 % | No |
| B Minas | 5,2 % | No |
| K Financieras | 2,9 % | Sí |
| F Construcción | 2,8 % | No |
| J Información y comunicación | 2,5 % | Sí, núcleo tecnológico |
| M Profesionales | 2,3 % | Sí |

El universo suma el 62,6 % de las ventas.

**Alcance del proyecto.** El alcance prioriza las tecnológicas sin dejar de lado industria y agro (C), comercio (G) y servicios (M y K).

**Comparabilidad.** Un recorte por sector permite comparar empresas de la misma actividad. Las alternativas se descartaron:

| Alternativa | Problema |
| --- | --- |
| Solo tecnológicas | No hay comparación con el resto de la economía |
| Todos los sectores, solo grandes | Excluye a las tecnológicas medianas, el 80 % de las que tienen ventas relevantes |

## Por qué estas reglas

| Regla | Motivo |
| --- | --- |
| TEC de todos los tamaños | Es el núcleo; muchas empresas de software son pequeñas |
| Medianas y grandes en G, C, M y K | El 89 % de esas empresas son micro o pequeñas, muchas sin ventas ni web |
| Tamaño por ventas | La columna de tamaño viene vacía y el dato de empleados no es confiable |
| Top 50 por ventas | Criterio objetivo y reproducible; mismo número de empresas por grupo |
| Sin holdings en el top 50 de K | Administran acciones y no ofrecen productos ni servicios; su ficha quedaría vacía |

## Por qué un piloto de 500

Las cifras salen de una descarga. La ficha, en cambio, exige encontrar y verificar la web oficial de cada empresa, y la SCVS no la publica.

| Alcance | Empresas | Horas para encontrar las webs (2–3 min por empresa) |
| --- | --- | --- |
| Piloto | 500 | 17–25 |
| Universo | 14.029 | 470–700 |
| Todo el ranking | 154.687 | 5.150–7.700 |

## Limitaciones

| Limitación | Tratamiento |
| --- | --- |
| La SCVS solo supervisa sociedades | El Observatorio describe sociedades, no personas naturales con negocio |
| Bancos, cooperativas y aseguradoras no están en el ranking | El grupo K se describe con lo que contiene |
| Tamaño calculado, no oficial | Se marca `tamano_derivado` |
| Dato de empleados inconsistente | Se marca `alerta_empleados` y el asistente lo advierte |
| Selección con un solo año | El script se vuelve a correr con cada ranking nuevo |
| 87 % del piloto en Pichincha y Guayas | Refleja dónde están las empresas grandes |
| Algunas empresas parecen fuera de sector (Coca-Cola de Ecuador en M) | Se respeta el CIIU que cada empresa declara |

## Trabajo futuro

1. Llevar la ficha completa del piloto al universo, automatizando la búsqueda de webs.
2. Sumar las secciones A, H, F, N y Q con el mismo script.
3. Sumar bancos, cooperativas y aseguradoras con datos de la Superintendencia de Bancos y la SEPS.
4. Incluir micro y pequeñas de G, C, M y K con directorios gremiales.
5. Medir la adopción de IA por sector con el módulo TIC de la [ENESEM](https://www.ecuadorencifras.gob.ec/encuesta-estructural-empresarial-2023/) del INEC.
