Un Poco de Historia#
La década de los 30#
El origen de los modelos abstractos de la computación nacen justamente en esta década. Existen tres modelos computables equivalentes que fueron propuestos en el mismo año, 1937.

Kurt Godel#
img Matemático Austriaco

Teorema de Incompletitud#
A principios de siglo se sostenía que la lógica era un sólido soporte para las verdades matemáticas (Bertran Rsusell, Principia mathematica).

Proposiciones Verdaderas A=[ 2+3 =5 ]
Proposiciones Falsas B= [ 2*3 = ]
Proposiciones Indecibles
Tomó una proposición solo sé que no sé nada y demostró que no podía probarse que fuera cierta (porque sino habría una contradicción), pero tampoco que fuera falsa, por la misma razón.

Godel logró demostrar que dentro de cualquier sistema matemático estrictamente lógico, siempre habría proposiciones cuya veracidad o falsedad no podría ser demostrada, partiendo de los axiomas en los que se basara ese sistema.

Caracteriza a los sistemas incompletos como aquellos en los que no se puede evaluar si sus proposiciones son verdaderas o falsas.

Funciones Recursivas Parciales#
Teoría de las Funciones Recursivas Generales#
Alan Turing#
img

Matemático Inglés

Máquina de Turing .#
En esa misma época se pretendía averiguar si era posible o no construir algún ingenio mecánico, con el que se pudiera averiguar o demostrar en un modo automático, la veracidad o falsedad de alguna demostración de índole matemático.

Maquina-a y maquina-u (https://turingmachine.io/)

En la actualidad no hay ningún algoritmo que permita determinar las propiedades de los número naturales

Problema de la Parada#
El problema de la parada o problema de la detención para máquinas de Turing consiste en lo siguiente: dada una Máquina de Turing M y una palabra w, determinar si M terminará en un número finito de pasos cuando es ejecutada usando w como dato de entrada. Alan Turing, en su famoso artículo On Computable Numbers, with an Application to the Entscheidungsproblem (1936), demostró que el problema de la parada de la Máquina de Turing es indecible (no computable o no recursivo), en el sentido de que ninguna máquina de Turing lo puede resolver.

Alonzo Church#
img

Cálculo Lambda ()#
El cálculo lambda es un sistema formal diseñado para investigar la definición de función, la noción de aplicación de funciones y la recursión. Church usó el cálculo lambda en 1936 para resolver el Entscheidungsproblem. Puede ser usado para definir de manera limpia y precisa qué es una "función computable".

La función identidad I(x) = x, que toma un único argumento, x, e inmediatamente devuelve x.

Por otro lado, la función suma S(x,y) = x + y, que toma dos argumentos, x e y, y devuelve la suma de ambos: x + y.

Las funciones no necesitan ser explícitamente nombradas. Esto es, la función S(x,y) = x + y puede ser reescrita como una función anónima: x,y → x + y (que se lee: «el par de x e y se mapea a x + y»).

Del mismo modo, I(x) = x puede ser reescrita de forma anónima como x → x, que se lee: «el argumento x se mapea a sí mismo».

El nombre que se asigne a los argumentos de la función es generalmente irrelevante. Esto es, x → x e y → y expresan la misma función: la función identidad. Del mismo modo, x,y → x + y y u,v → u + v expresan la misma función: la función suma.

Toda función que requiere dos argumentos, como por ejemplo la función suma, puede ser reescrita como una función que acepta un único argumento, pero que devuelve otra función, la cual a su vez acepta un único argumento.

Por ejemplo, x,y → x + y puede ser reescrita como x → (y → x + y). Esta transformación se conoce como currificación, y puede generalizarse para funciones que aceptan cualquier número de argumentos. Esto puede parecer difícil de entender, pero se entiende mejor mediante un ejemplo. Considérese la función suma no currificada:

x,y → x + y

Al tomar a los números 2 y 3 como argumentos, se obtiene:

2 + 3
Lo cual es igual a 5. Considérese ahora la versión currificada de la función:

x → (y → x + y)
Si se toma al número 2 como argumento, se obtiene la función:

y → 2 + y
Y tomando luego al número 3 como argumento, se obtiene:

2 + 3

Los tes modelos son equivalentes, vale decir que todos describen en concepto de computabilidad desde distintas torres axiomática.
La década de los 40#
Hacia los años 40 con el advenimiento de la primera computadora con programa almacenado, de la mano de John Von Neumann, hizo necesario escribir secuencias de código o programas en lenguaje de máquina.
    C7 06 0000 0002
Así para mover un valor literal 2 a una dirección de memoria se debía escribir la secuencia anterior de comandos, esto hacia imposible que se pudieran escribir programas rápidamente y de forma poco tediosa. Por ello nace el llamado lenguaje ensamblador , en el cual los códigos de instrucción se reemplazaron por 3 letras que representa una instrucción mnemotécnica y por direcciones de memoria que podían se dadas en forma simbólica.
    MOV X,2
Lo que se buscaba era poder mejorar aun todas esas mejoras que el lenguaje ensamblador había introducido, de manera de simplificar aun más la escritura de programas
    X=2
Entre 1954 y 1954 John Backus desarrollo el primer lenguaje de programación de alto nivel, FORTRAN I y su compilador.
El Aporte de Noam Chomsky#
Al mismo tiempo Noam Chomsky, lingüista estadounidense que aun vive, Comenzó a estudiar la estructura del lenguaje natural. Sus descubrimientos hicieron que la construcción de compiladores se volviera mucho más fácil e incluso pudiera ser automatizada en cierto grado.

Sus estudios desembocaron en una clasificación de los lenguajes de acuerdo con la complejidad de sus gramáticas y la potencia de los algoritmos necesarios para reconocerlas.

img

La Jerarquía de Chomsky#
Se compone de 4 niveles gramaticales:

Gramáticas de Tipo 3:
Gramáticas Regulares: Estos lenguajes son aquellos que pueden ser aceptados por un autómata finito. También esta familia de lenguajes pueden ser obtenidas por medio de expresiones regulares.
Gramáticas de Tipo 2:
Gramáticas Libres del Contexto: Estos lenguajes son aquellos que pueden ser reconocidos por un autómata con pila.
Gramáticas de Tipo 1:
gramáticas sensibles al contexto: Los lenguajes descritos por estas gramáticas son exactamente todos aquellos lenguajes reconocidos por una máquina de Turing determinista cuya cinta de memoria está acotada por un cierto número entero de veces sobre la longitud de entrada, también conocidas como autómatas linealmente acotados.
Gramáticas de Tipo 0:
que incluye a todas las gramáticas formales. Estas gramáticas generan todos los lenguajes capaces de ser reconocidos por una máquina de Turing.
Fases de un Compilación#
(tiger:chap1)

Análisis Léxico

Rompe el código fuente en palabras individuales, o tokens

Esta es la primera fase de un compilador se denomina análisis léxico o escaneo.

El analizador léxico lee código fuente como un flujo de caracteres y los agrupa en secuencias significativas conocidas como lexemas.

Para cada lexema el analizador léxico produce un token de la forma –> {nombre-token,valor-atributo} (Aho:p6). El lexer toma un stream de caracteres y lo transforma en un stream de palabras clasificadas. Esto es pares de forma {p,s}, donde p es la parte del discurso de la palabra y s es como se escribe.

Por ejemplo la frase "los compiladores son objetos ingenieriles", el lexer debería producir el siguiente stream:

{articulo,"los"},{sustantivo,"compiladores"},{verbo, "son"},{sustantivo,"objetos"},{adjetivo,"ingenieriles"}

Son unidades significativas que se corresponden a las palabras de un lenguaje natural (Lou:p8)

El token es pasado a la fase siguiente que corresponde al análisis sintáctico como el stream de entrada para el parser.

nombre-token: representa es un símbolo abstracto que se utiliza en la próxima fase.

valor-atributo: apunta a una entrada en la tabla de símbolos para ese token.

Por ejemplo una asignación en lenguaje C:

total = inicial + contador * 2
El resultado una vez escaneada esa línea sería:

{id1,1} {=} {id2,2} {+} {id3,3} {*} {2}

y la tabla de símbolos:

| 1 | total | … | | 2 | inicial | … | | 3 | contador | … |

Cabe aclarar que el concepto de token se verá más detalladamente en el estudio de esta etapa especifica posteriormente.

Análisis Sintáctico

Esta el la segunda fase del compilador, también se denomina parsing. La idea es que el compilador trata de hacer corresponder el stream de palabras clasificadas contra las reglas que especifican la sintaxis del lenguaje de entrada. Por ejemplo en español algunas reglas gramaticales pueden ser :
Oración -> Sujeto verbo Objeto marca de fin Sujeto -> Sustantivo Sujeto -> Sustantivo Modificador Objeto -> Nombre Objeto -> Sustantivo Modificador Modificador -> adjetivo …

El analizador sintáctico o parser es el que realiza este trabajo.

Utiliza los primeros componentes de los tokens producidos por el lexer para crear una representación intermedia en forma de árbol que describa la estructura gramáticas del flujo de tokens.

Esta representación se denomina árbol sintáctico. Este se caracteriza porque sus nodos intermedios representan operaciones y los hijos de estos nodos representan los argumentos.

Para el ejemplo anterior :

total = inicial + contador * 2
Cuyo resultado es: {id1,1} {=} {id2,2} {+} {id3,3} {*} {2}

se obtendría el siguiente árbol sintáctico

img

Las fases siguientes utilizan la estructura gramatical para ayudar a analizar el código fuente y generar el programa destino.
Análisis Semántico

(lou:p9)

La semántica de un programa es su "significado", en oposición a su sintaxis o estructura. La semántica de un programa determina su comportamiento durante el tiempo de ejecución, pero la mayoría de los lenguajes de programación tienen características que se pueden determinar antes de la ejecución e incluso no se pueden expresar de manera adecuada como sintaxis y analizarse mediante el analizador sintáctico. Tales características se denominan semántica estática, y el análisis de tal semántica es tarea del analizador semántico.

La semántica "dinámica" de un programa, es decir, aquellas propiedades que solamente se pueden determinar al ejecutarlo no se pueden determinar mediante un compilador porque este no ejecuta el programa.

Las características típicas de la semántica estática de los lenguajes de programación incluyen:

las declaraciones
la verificación de tipos
conversiones de tipos de datos conocidas como coerciones (suma de un entero mas un flotante se obliga a convertir a flotante)
img

Administración de la Tabla de Símbolos

Una función muy importante del compilador durante las etapas de análisis léxico, análisis sintáctico y análisis semántico es la de registrar los nombres de las variables que se utilizan en el código fuente, y recolectar información sobre varios atributos de cada nombre.

Estos atributos pueden proporcionar información acerca del espacio de almacenamiento que se asigna para un nombre, su tipo, su alcance.

En el caso de las funciones registra los nombres, el tipo y numero de argumentos, el método para pasar cada argumento y el tipo devuelto.

La tabla de símbolos es una estructura de datos que contiene un registro para cada nombre de variable, con campos para los atributos del nombre. Esta estructura de datos debe diseñarse de forma tal que permita al compilador buscar el registro para cada nombre, y almacenar u obtener datos de ese registro con rapidez.

(ajo:p11)

Generación de código intermedio

En el proceso de traducir código fuente a código destino, un compilador puede construir una o mas representaciones intermedias que pueden tener una variedad de formas.

Los arboles sintácticos son una forma de representación intermedia que por lo general se utilizan durante el análisis sintáctico y semántico.

Posteriormente a estas dos fases los compiladores generan una representación similar al código maquina que se puede considerar como un programa para una maquina abstracta (aho:p9).

Esta representación intermedia debe tener dos propiedades:

debe ser fácil de producir y fácil de traducir en la maquina destino
t1=inttofloat(60)
t2=id3 * t1
t3=id2 + t2
id1= t3
Posteriormente se abordara las principales representaciones intermedias que se utilizan comúnmente en los compiladores.
Front-end de un compilador

Todas las fases enumeradas hasta este punto conforman el front-end de un compilador moderno.

img

A partir de este punto la siguiente etapa es llevada a cabo por el optimizador.

Optimización de código

En esta fase se optimiza el código intermedio generado en la fase anterior que es independiente de la arquitectura de la maquina en la que se generara el código destino. Su objetivo es mejorar el código intermedio de forma tal que produzca mejor código destino.

Mejor significa:

más rápido
obtener código mas corto
generar código destino que consuma menos energía
Siguiendo con el ejemplo anterior el algoritmo de optimización de código IR generaría el siguiente código:

t1 = id3 * 60.0
id1 = id2 + t1
Back-End de Un Compilador

A partir de este punto entra a jugar el denominado Back-End de un compilador moderno que se encarga de la generación de código destino a partir de la arquitectura de la maquina que ejecutará el programa.

Generador de código

El generador de código toma el código intermedio y genera el código para la arquitectura de la maquina destino. Normalmente se genera en este punto el código objeto de la maquina destino directamente.

Si el lenguaje destino es código maquina, se seleccionan registros y/o posiciones de memoria para cada una de las variables utilizadas en el programa.

Posteriormente, las instrucciones intermedias se traducen en secuencias de instrucciones maquina que realizan la misma tarea.

Un aspecto importante de esto es la asignación juiciosa de los registros para guardar las variables.

LDF     R2,id3
MULF    R2,R2,#60.0
LDF     R1,id2
ADDF    R1,R1,R2
STF     id1,R1
(leer Coo:p15)

Optimizador de código destino

En esta fase el compilador intenta mejorar el código destino generado en la etapa anterior.

Estas mejoras pueden ser:

selección de modos de direccionamiento para mejorar el rendimiento

reemplazo de instrucciones lentas por otras rápidas

eliminar operaciones redundantes o innecesarias

Algunos de estos ejemplos pueden ser: eliminar la multiplicación utilizando corrimientos, utilizar el redireccionamiento indexado para realizar el almacenamiento de arreglos.

Estructuras de Datos Principales en un Compiladores#
(Lou:p13)

Tokens

Generalmente cuando el analizador léxico reúne los caracteres correspondientes a un token, representa al token de manera simbólica, es decir, como un valor de un tipo de dato enumerado que representa al conjunto de tokens del lenguaje fuente.

typedef enum  { T_END_OF_INPUT, T_VAR, T_IDENTIFIER, T_LPAREN, ... }
TokenType;
En ocasiones también es necesario mantener la cadena de caracteres misma u otra información derivada de ella, tal como el nombre asociado con un token identificador o el valor de un token numero.

En la mayoría de los lenguajes el analizador léxico solo necesita generar un token a la vez (esto se conoce como búsqueda de símbolo simple).

Árbol Sintáctico

El analizador sintáctico genera una estructura de datos que representa un árbol n-ario y lo hace en forma dinámica a medida que se efectúa dicho análisis. Normalmente el árbol entero se puede conservar como una estructura en la cual se apunta a un nodo raíz y este a sus hijos.

Cada nodo de la estructura es un registro cuyos campos representan la información recolectada tanto por el analizador sintáctico como, posteriormente, por el analizador semántico.
Tabla de Símbolos

Esta estructura de datos mantiene la información asociada con los identificadores:

funciones

variables

constantes

tipos de datos

La tabla se símbolos interactúa con casi todas las fases de compilación:

analizador léxico
analizador sintáctico
analizador semántico
generación de código y optimización de código intermedio
Dado que la tabla de símbolos tiene acceso con tanta frecuencia las operaciones de inserción, eliminación y acceso necesitan ser muy eficientes, preferiblemente operaciones de tiempo constante (O(1))

Tabla de Literales

La tabla de literales almacena constantes y cadenas que se utilizan el programa.

Sus operaciones de acceso y búsqueda deben ser rápidas.

La tabla de literales es importante en la reducción del tamaño de un programa en la memoria al permitir la reutilización de constantes y cadenas.

Análisis Léxico
Introducción [dragon-3]#
Como la primera fase de un compilador la principal tarea del analizador léxico es:

leer los caracteres de la entrada del programa fuente,

agruparlos en lexemas

y producir como salida una secuencia de tokens para cada lexema del programa fuente.

Interactúa con:

El analizador sintáctico para su análisis
También con la tabla de símbolos.
Análisis Léxico vs Análisis Sintáctico

Existen varias razones por la cual separar al análisis léxico del análisis sintáctico dentro de un compilador:

La sencillez del diseño es la consideración más importante -> permite simplificar alguna de las dos tareas.

Se mejora la eficiencia del compilador. Escribir el lexer separado permite aplicar técnicas especificas que sólo sirven para esta tarea.

Se mejora la portabilidad del compilador -> Las particularidades de los dispositivos de entrada se restringen solo al lexer.

Definiciones

Token

Un token es un par que consiste en un nombre de token y un valor de atributo opcional

El nombre del token es un símbolo abstracto que representa un tipo de unidad léxica; por ejemplo una palabra clave, un identificador. Es una palabra clasificada.

Son los símbolos de entrada del analizador sintáctico.
Patrón

Un patrón es una descripción de la forma que pueden tomar los lexemas de un token. En el caso de una palabra reservada como token, el patrón es sólo la secuencia de caracteres que forman la palabra reservada.
Lexema

Es una secuencia de caracteres en el programa fuente, que coinciden con el patrón para un token y que el analizador léxico identifica como una instancia de ese token
Expresiones Regulares: Introducción#
Las expresiones regulares son lenguajes para expresar patrones. Fueron descriptas en 1950 por Stephen Kleene como un elemento de su trabajo fundacional en la teoría de autómatas y computabilidad. Actualmente, las expresiones regulares son ampliamente utilizadas por distintos tipos de programas ( editores de texto, programas de linea de comando,etc.

Alfabeto

Alfabeto es un conjunto finito de símbolos. Se denomina con una letra griega Σ.
Σ1={0,1} → alfabeto binario
Σ2={a,b} → alfabeto formado por las letras a y b
Σ3={I,V,X,L,C,D,M} → alfabeto formados por los símbolos de los números romanos
ASCII → es un alfabeto, cumple con la definición
UTF-8 → es un alfabeto también.
Cadena

Una cadena sobre un alfabeto es una secuencia finita de símbolos que se extraen de un determinado alfabeto. Normalmente en teoría del lenguaje los término "palabra" y "oración" se utilizan como sinónimos.

Una cadena se denota con la letra s.

Todas las cadenas de determinada longitud k que se pueden construir con un alfabeto Σ se representan convencionalmente Σk

Por ejemplo, dado el alfabeto Σ= {a, b}, se dan las siguientes extensiones:

Σ0 = {∅}
Σ1 = {a, b}
Σ2 = {aa, ab, ba, bb}
Σ3 = {aaa, aab, abb, aba, bbb, bba, baa, bab}…
Para representar el conjunto de todas las cadenas posibles que se pueden obtener a partir de un alfabeto Σ se usa la notación Σ∗. En términos de teoría de conjuntos, Σ∗ = {Σ0 ∪ Σ1 ∪ Σ2 ∪ Σ3 ∪ Σ ^{4} ∪ …}

La longitud de una cadena |s|.

La cadena vacía se representa por ε, cuya longitud es cero.

Lenguaje

Un lenguaje es cualquier conjunto contable de cadenas sobre algún alfabeto fijo.

Operaciones más importantes en los lenguajes son:

Unión: es la misma operación que se realiza con los conjuntos.

Concatenación: La concatenación de lenguajes es cuando se concatenan todas las cadenas que se forman al tomar la primer cadena del primer lenguaje y una cadena del segundo lenguaje , en todas las formas posibles.

Clausura Positiva: de un lenguaje L, se denota como L(s+). En términos de teoría de conjuntos, Σ+ = { Σ1 ∪ Σ2 ∪ Σ3 ∪ Σ4 ∪ …}

La Clausura de Kleene: de un lenguaje L, se denota como L(s∗). En términos de teoría de conjuntos, Σ∗ = {Σ0 ∪ Σ1 ∪ Σ2 ∪ Σ3 ∪ Σ4 ∪…}

Expresión regular

Una expresión regular s es una cadena que denota L(s), un conjunto de cadenas derivados a partir de un alfabeto Σ. L(s) es conocido como "Lenguaje de s"

L(s) se define inductivamente con los siguientes casos base:

Si a es un símbolo que pertenece a Σ, entonces a es una expresión regular, y L(a)={a}, es decir el lenguaje con una cadena de longitud uno, con a en su única posición

ε es una expresión regular, y L(ε) = {ε}, es decir el lenguaje cuyo único miembro es la cadena vacía.

hay cuatro partes que constituyen la inducción,mediante la cual las expresiones regulares más grandes se construyen a partir de las más pequeñas. Entonces, para cualquier expresión regular s y t,y denotan a los lenguajes L(s) y L(t) :

(s)|(t) es una Expresión Regular tal que L(s|t)=L(s) U L(t).

(s)(t) es una expresión regular tal que L(st) contiene todas las cadenas formadas por la concatenación de una cadena de L(s) seguida por una cadena de L(t).

(s)∗ es una expresión regular tal que ( L(s)* )= L(s) concatenado cero o muchas veces.

(s) es una expresión regular que denota al lenguaje L(s)

Tener en cuenta que:

El operador unario ∗ tiene la precedencia más alta y es asociativo a la izquierda.
La concatenación tiene la segunda precedencia más alta y es asociativa a la izquierda.
| tiene la precedencia más baja y es asociativa a la izquierda
recordar:

Propiedad	Ejemplo
asociatividad	a|(b|c) = (a|b)|c
Conmutatividad	a|b = b|a
distribución	a(b|c)= ab|ac
idempotencia	a** = a*
Desde Kleene se han ampliado varios operadores para mejorar la habilidad de especificar patrones, algunos de ellos son :

Una o mas instancias. El operador unario post-fijo + representa la clausura positiva de una expresión regular.

Cero o una instancia. El operador post-fijo ?. Es equivalente a r|ε , o dicho de otra forma L(r?)= L(r) U L(ε)

Clases de caracteres. [a-z] rango de letras minúsculas . Otra forma es utilizando el operador |

Ejemplos

Un identificador es una secuencia de letras mayúsculas y números, pero un numero nunca puede estar primero:
expresión regular	[A-Z]+([A-Z] | [0-9] )∗
verifican la rexp	PRINT
MODE5
NO VERIFICAN	print
5contador
Un número es una secuencia de dígitos con un punto decimal opcional. Como nota el punto decimal debe tener dígitos a ambos lados:

expresión regular	[A-Z]+([A-Z] | [0-9] )∗
verifican la rexp	PRINT
MODE5
NO VERIFICAN	print
5contador
Tabla de expresiones regulares comunes:

Expresión	Descripción
.	Any character is required.
a	The character a is required.
[abcdef]	Any character in the set abcdef is required.
[a-f]	Any character in the range a to f is required.
a?	The character a is optional.
a*	Zero or more of the character a are required.
a+	One or more of the character a are required.
\^	The start of input is required.
\$	The end of input is required.
Reconocimiento de Tokens#
Una vez con capacidad para expresar patrones usando expresiones regulares es necesario estudiar como tomar todos los patrones para todos los tokens necesarios. Además, construir una pieza de código que examine la cadena de entrada y busque un prefijo que sea un lexema que coincida con esos patrones.
Por ejemplo:
inst -> if expr then instr
      | if expr then instr else instr 
      | &epsilon;                     

expr -> term oprel term
      | term |
   
term -> id 
     | numero 
Las terminales de la gramática, que son if, then, else, oprel (operación relacional), id, numero corresponden a los nombres de los tokens que el analizador léxico respecta. A continuación se escriben los patrones para estos tokens que se describen como expresiones regulares:

digito   -> [0-9] 
digitos  -> digito+ 
numero   -> digitos(.disgitos)? (E[=-]? digitos) ? 
letra    -> [A-Za-z]
id       -> letra (letra &vert; digito)\* 
if       -> T_IF 
then     -> T_THEN 
else     -> T_ELSE 
oprel    -> < | > | <= | >= | = | <> 
ws       -> ( \n\n)+
Autómatas Finitos#
(Dou:p15)(Hop:31)

Se dice que un Autómata Finito es una máquina abstracta que puede ser utilizada para representar ciertas formas de cómputo. Gráficamente un AF consiste en un número de estados y un numero de vértices entre esos estados. Cada uno de estos vértices se etiqueta con uno de los símbolos de un alfabeto.

La máquina siempre comienza en el estado S0. Para cada símbolo de entrada que se presente al AF, este se mueve al estado indicado por el vértice con la misma etiqueta que el símbolo de entrada.

Algunos estados de AF son conocidos como accepting states (estados de aceptación o finales) estos se marcan con un doble circulo.

Si un AF se encuentra en un estado de aceptación después de consumir todo el input, entonces se dice que el AF acepta el input. Se dice que rechaza el string de entrada si este termina en un estado no final.

Cada Expresión Regular puede ser transformada en un Autómata Finito y viceversa.

Ejemplo1: palabra reservada for:

img

Ejemplo2: Reconocimiento de identificadores [a-z][a-z0-9]+
img

Ejemplo3: AF para reconocer números de la forma ([1-9][0-9]∗)|0:
img

Autómatas Finitos Deterministas

(lou:p49) Un autómata finito determinista o DFA M se compone de un alfabeto Σ, un conjunto de estados D, una función de transición T:S x Σ -> S, un estado inicial S0 ∈ S y un conjunto de estados de aceptación A perteneciente a S.

El lenguaje aceptado por M, se escribe como L(M), se define como el conjunto de cadenas de caracteres c1c2….cn con cada ci ∈ Σ, tal que existen estados S1=T(s1,c1), S2=T(s2,c2)…. Sn=T(sn,cn) con Ss un elemento de A, es decir un estado de aceptación.

S x Σ se refiere al producto cartesiano

La función T registra transiciones de estado: T(s,c)=s'

img

La aceptación como la existencia de una secuencia de estados S1…..Sn siendo Sn un estado de aceptación.

En otras palabras:

un DFA es un autómata finito que además es un sistema determinista; es decir:

para cada estado en que se encuentre el autómata, y con cualquier símbolo del alfabeto leído, existe siempre no más de una transición posible desde ese estado y con ese símbolo.
Ejemplo de DFA:

img

S={S0,S1,S2} (conjunto de estados)

S0 es el estado inicial

Σ={0,1} (alfabeto)

A={S2} (conjunto de estados de aceptación)

T función de transición: T(S0,0 )= S1 T(S0, 1)= S0 T(S1, 0)= S1 T(S1, 1)= S2 T(S2, 0)= S2 T(S2, 1)= S2

  Se define el autómata finito deterministico en función de una quíntupla de la siguiente forma M=(S, S0, Σ, A, T)

  
La función de transición extendida y la tabla de transiciones:

Sea el siguiente autómata :

img

definido formalmente por la quíntupla :

A=(Q, Σ, δ, q0, F)

La tabla de transición se arma, poniendo haciendo una tabla de doble entrada entre los símbolos del alfabeto y los estados del autómata.

La tabla de transición del autómata viene dada por:

0	1
-> S0	S1	S0
S1	S1	S2
* S2	S2	S2
Esta tabla puede usarse para verificar si una cadena pertenece al lenguaje, por ejemplo:11010

A su vez se define a la función de transición extendida \δ, llamada delta hat o delta sombrero. Esta es una función de dos variables \δ(q0,w), donde w es una cadena.

Sea w=11011 entonces

\δ(q0,w)=q2

Autómatas Finito No Deterministas

Un **Autómata Finito No Determinista** o **NFA** M consta de un alfabeto &Sigma;, un conjunto de estados S, una función de transición T: S x ( &Sigma; &cup; {&epsilon;} ) &rarr; \wp()(S), así un estado de inicio s<sub>0</sub> de S y un conjunto de estados de aceptación A de S.

El Lenguaje aceptado por M, escrito por L(M), se define como el conjunto de cadenas de caracteres c<sub>1</sub>c{2}&#x2026;c<sub>n</sub> con cada c<sub>i</sub> de &sigma; &isin; (&epsilon;) tal que existen estados s<sub>1</sub> en T(s<sub>0</sub>,c1) &#x2026;.. con s<sub>n</sub> un elemento de A.



-   ¿Dónde está la diferencia?

La diferencia está en que para un mismo símbolo del alfabeto existen múltiples posibles transiciones, o incluso puede no existir transición. Por ello el autómata se denomina **No Determinista**.

La Clave está en la función de transición : T: S x ( &Sigma; &cup; {&epsilon;} ) &rarr; \wp()(S),

1.  Ejemplo de NFA

    ![img](../images/automata-finito-no-deterministico-ejemplo.png)
    
    Analisis de hilos en un NFA, dada la cadena: 00101 realizar el análisis de hilos.
    
    ![img](../images/hilo-nfa.png)

2.  La tabla de transiciones:

    Si se tiene en cuenta la definición formal de un **automata finito no determinista**:
    
    A=(Q, &Sigma;, &de lta;, q<sub>0</sub>,F), donde:
    
    1. Q es un conjunto de estados.
    
    2. &Sigma; es un conjunto finito de símbolos de entrada, un alfabeto.
    
    3. q<sub>0</sub>, un elemento de Q, que es el estado inicial.
    
    4. F, un subconjunto de Q de estados de aceptación.
    
    5. &delta; la función de transición que toma un estado de Q y un símbolo de &Sigma; como argumentos y devuelve un **subconjunto de Q**.
    
       
    
    Dado el ejemplo anterior, obtener la tabla de transiciones para w=00101:
    
    ![img](../images/automata-finito-no-deterministico-ejemplo.png)
    
    |      | 0    | 1  |
    | --- | ----- | -- |
    | &larr; S<sub>0</sub>   | {S<sub>0</sub>,S<sub>1</sub>} | {S<sub>0</sub>} |
| S1 | ∅ | {S2 | | ∗ S2 | ∅ | emptyset | |

Un Poco de Código#
(lou)

Un Token:

typedef enum {IF, THEN, ELSE , PLUS,NUM, ID  } token_type;

typedef struct {
    token_type token_val;
    char * string_val;
    int num_val;
} TOKEN;

o

typedef enum {IF, THEN, ELSE , PLUS,NUM, ID  } token_type;

typedef struct {
    token_type token_val;

    union{
    char * string_val;
    int num_val;
    } atributos;

} TOKEN;


2.  La Tabla de Símbolos:

    (Ben:65) A medida que se va realizando el proceso de compilación es necesario buscar nombres en la **Tabla de Símbolos**, para ver si un identificador ha sido declarado. Esto además tiene que ser hecho de una forma muy eficiente, un arreglo de registro o por una lista enlazada son una estructura muy ineficiente para las búsquedas, para ello es necesario y una **Tabla de Hash Abierto**:
    
    ```C
    struct symbol_table{
        struct symbol_table* siguiente;
        char*                nombre;
        int                  tipo;
        int                  block_no;
        int                  direccion;              
    }
Un lexer

(dra,lou)

Para mostrar como es la arquitectura de un analizador léxico a partir de autómatas se utilizará el siguiente autómata que representa el reconocimiento de las operaciones de relación:

img

tener en cuenta que el símbolo ∗ implica que se debe retroceder la entrada en un caracter.

img

para implementar un analizador gráfico a partir de un automata, en primer lugar se debe pensar en una variable llamada estado, que contenga el estado actual en el que se encuentra el autómata. Una instrucción switch que esté basada en el valor del estado y para cada uno de estos valores se ejecutara el código necesario para cada uno de los estados. Un ejemplo en C:

    
    TOKEN * ObtenerOpRel(){
        TOKEN * token_ret= malloc(TOKEN);
    
        while(1){
        switch (estado) {
            case 0: c=sig_char();
                if (c == '<') estado =1;
                else if (c == '=') estado = 5;
                else if (c == '>') estado = 6;
                else error(); /*el lexema no es un operacion relacional */    
                break;
            case 1:  ...
            case 2:  ...
            case 3:
            ...
    
            case 8: retroceder();
                token_ret->val= GD;
                return (token_ret);
        } 
        }
    }
Dado que esto último se debe realizar por cada tipo de token, el programar a mano un analizador léxico de un lenguaje de programación se torna una cuestión muy compleja. Por ello normalmente se utilizan Generadores de Analizadores Léxicos

Generadores de Analizadores Sintácticos
Generadores de Analizadores Sintácticos#
Yacc

Yacc (Yet Another Compiler Compiler) esta herramienta permite especificar una gramática (libre de contexto) y genera un analizador sintáctico que reconoce oraciones validas de dicha gramática.

Yacc y Lex trabajan juntos:

Lex: Realiza el análisis lexicográfico.

Dado un stream de caracteres devuelve un stream de palabras clasificadas o tokens.

Se definen en un archivo expresiones regulares y para cada expresión regular se escribe una o un conjunto de acciones asociadas a esa expresión regular:


[a-zA-Z][a-zA-Z0-9]+  {return COMMAND}

Lex toma un archivo de entrada, un stream de caracteres transforma en un archivo de salida, un stream de trokens
Yacc: Yet Another Compiler Compiler

  - Yacc genera un parser y un analizador semántico que generan el parseo y el correspondiente análisis, sobre el stream de tokens que produce lex. A medida que se está generando el análisis sintáctico va armando el **Árbol de Parsing** y también se puede realizar cierto análisis semántico con la misma herramienta.

    

  -   Bison: Esta herramienta es la versión de GNU, que es compatible con Yacc, pero además hace otras muchas cosas.

  <img src="../images/yacc1.png" alt="img" style="zoom:200%;" />

  El input de yacc es una **gramática libre de contexto**, el analizador sintáctico generado va a construir un **árbol de parsing**.

  <img src="../images/yacc2.png" alt="img" style="zoom:200%;" />

  -   mylang.y: define la gramática del lenguaje. Se puede definir tokens, tipos de tokens y eso se guarda en y.tab.h

  Una vez que se tienen definidos ambos archivos el de la gramática y el del analizador léxico, se compilan para generar o el interprete o el compilador.

  <img src="../images/yacc2.png" alt="img" style="zoom:200%;" />
Un Archivo YACC

La estructura de un archivo Yacc es muy similar a la estructura de los achivos lex:

Primera Parte
%%
 producción   {accion}
%%
Tercera Parte
Primera Parte

La primera parte del archivo de Yacc contiene:

Declaraciones en C que están delimitadas por %{%}

Definiciones específicas de Yacc

%start
%token
%union (tokens de diferente tipos)
%type (el tipo que puede tomar un token)
Producciones

La sección del medio representa la gramática.

las acciones asociadas a una producción ven entre {}

Ejemplo:


statements: statement             {printf("statement");}
          | statement statements  {printf("statements \n");}
          ;

statement: identifier '+' identifier {printf("suma"); }

statement: identifier '-' identifier {printf("resta"); }

Un aspecto interesante de las producciones es que Yacc permite acceder a los valores que están asociados con los símbolos de las producciones:

$1, $2, $3, … $N : se refieren a los valores de los símbolos asociados a las producciones.

e
s
e
l
v
a
l
o
r
a
s
o
c
i
a
d
o
a
l
L
H
S
eselvalorasociadoalLHS
Todos los símbolos tienen un valor asociado, sean terminales o no terminales.

La asociación por defecto es $$=$1

Entonces se puede escribir:

statement: identifier '+' identifier {$$ = $1 + $3; }

statement: identifier '-' identifier {$$ = $1 - $3; }
Representan la semántica de la producción.

Manos a la Obra

En este ejemplo se desarrolla una calculadora muy básica

mi gramática:

instruccion -> NOMBRE '=' expresion
         | expresion


expresion: -> NUMERO '+' NUMERO
        | NUMERO '-' NUMERO
        | NUMERO
Características:

Reconocer las operaciones
Evaluar los resultados
mi_lenguaje.y:

%{
#include<stdio.h>

extern int yylex(void);
extern char * yytext;
void yyerror(char * s);

}%
%token NOMBRE NUMERO
%%
instruccion: NOMBRE '=' expresion
       | expresion             {printf("= %d\n",$1);}
       ;

expresion: NUMERO '+' NUMERO   {$$ = $1 + $3;}
     | NUMERO '-' NUMERO   {$$ = $1 - $3;}
     | NUMERO              {$$ = $1;}
     ;
%%
void yyerror (char *s){
   printf("%s",s);
}


int main(){
   yyparse();
   return 0;
}

mi_lenguaje.l:

%{
#include<stdlib.h>    
#include "y.tab.h"
extern int yylval;
%}

%% 
[0-9]+       { yylval=atoi(yytext); return NUMERO;}
[ \t] ;
\n           return 0;   //EOF  
.            return yytext[0];
%%

Analisis Semantico
Análisis Semántico#
El análisis semántico es la fase en la cual el compilador calcula la información adicional necesaria para la compilación una vez que se conoce la estructura sintáctica de un programa.

Esta fase se conoce como análisis semántico debido a que involucra el calculo de información que sobrepasa las capacidades de las gramáticas libres de contexto y los algoritmos de análisis sintáctico estándar, por lo que no se considera sintaxis.

La información calculada también esta estrechamente relacionada con el significado final, o semántica, del programa que se traduce.

Como el análisis que realiza el compilador es estático por definición, el análisis semántico también se conoce como análisis semántico estático.

En un lenguaje típico estáticamente tipado como C, en análisis semántico involucra la construcción de una tabla de símbolos para mantenerse al tanto de los significados de los nombres establecidos en las declaraciones, inferir los tipos y verificarlos en las expresiones y sentencias con el fin de determinar la exactitud dentro de las reglas de tipos del lenguaje.
El análisis semántico se divide en dos categorías:

La primera es el análisis de un programa que requiere las reglas del lenguaje de programación para establecer su exactitud y garantizar una ejecución adecuada. La complejidad de este tipo de análisis varia según lo requerido por la definición del lenguaje. En lenguajes orientados en forma dinámica tales como LISP y SMALLTALK pueden no haber análisis semántico estático mientras que en lenguajes como ADA existen fuertes requerimientos que debe cumplir un programa para ser ejecutable.

La segunda categoría de análisis semántico es el análisis realizado por un compilador para mejorar la eficiencia de ejecución del programa traducido. Esta clase de análisis, por lo regular, se incluye en análisis de optimización o técnicas de mejoramiento de código. El análisis semántico a diferencia del análisis léxico y del análisis sintáctico no posee generadores automáticos de analizadores semánticos, como el caso de lex o yacc.

En el análisis sintáctico existen tres componentes importantes

La tabla de símbolos

La verificación y control de tipos

Las gramáticas con atributos

Estas últimas son más útiles para los lenguajes que obedecen el principio de la semántica dirigida por sintaxis, la cual asegura que el contenido semántico de un programa se encuentra estrechamente relacionado con su sintaxis. Todos los lenguajes modernos tienen esta propiedad.

Normalmente quien escribe un compilador casi siempre debe construir una gramática con atributos a mano a partir del manual del lenguaje, ya que rara vez la da el diseñador del lenguaje.

Los algoritmos para la implementación del análisis semántico tampoco son tan claramente expresables como los algoritmos de análisis sintáctico.

Existe un problema adicional causado por la temporalidad del análisis durante el proceso de compilación. Si el análisis semántico se puede suspender hasta que todo el análisis sintáctico este completo, entonces la tarea de implementar el análisis semántico se vuelve considerablemente más fácil. Y consiste en esencia en la especificación de orden para el recorrido del árbol sintáctico, junto con los cálculos a realizar cada vez que se encuentra un nodo en el recorrido. Sin embargo, esto implica que el compilador debe realizar varias pasadas de análisis. Si por otra parte el compilador necesita realizar todas sus operaciones (incluyendo la generación de código en un solo paso), entonces la implementación del análisis semántico se convierte en mucho mas que un proceso a propósito para encontrar un orden correcto y un método para calcula la información semántica. En la actualidad los escritores de compiladores utilizan varias pasadas para simplificar los procesos de análisis semántico y generación de código.

La Tabla de Símbolos#
La tabla de símbolos es el principal atributo heredado en un compilador, y, después del árbol sintáctico, también forma la principal estructura de datos. Si bien la tabla de símbolos esta estrechamente relacionada con el análisis sintáctico y el análisis léxico, los cuales pueden consultarla para resolver ambigüedades.

Pero sin embargo, en ciertos lenguajes como Ada y PASCAL, es posible e incluso razonable posponer las operaciones de la tabla de símbolos hasta después de realizar en análisis sintáctico completo, es decir cuando se sabe que el programa que se esta traduciendo es sintácticamente correcto.

Principales operaciones en la tabla de símbolos:
Inserción: Se utiliza para almacenar la información proporcionada por las declaraciones de nombre cuando se procesan estas declaraciones.
insert(name, record);
Búsqueda: Es necesaria para recuperar la información asociada con un nombre cuando éste se utiliza en el código.
look_up(name);
Eliminación: Es necesaria para eliminar la información proporcionada por una declaración cuando ya no se aplica.
La propiedades de estas operaciones son dictadas por las reglas del lenguaje de programación que se esta traduciendo. En particular la información que se necesita almacenar en la tabla de símbolos está en función de la estructura y propósito de las declaraciones.

La información que incluye puede ser:

Tipo de Dato
Lexema
Posición
Ámbito (scope): información de la aplicabilidad.
Información acerca de la ubicación posible en la memoria.
Estructura de la Tabla de Símbolos

La Tabla de Símbolos en un compilador es una estructura de datos llamada diccionario o tabla de hash, obviamente por sus bondades en los tiempos de acceso a los datos. Las operaciones sobre la tabla de Símbolos deben ser lo más eficientes posible.

Normalmente se utiliza un diccionario con resolución de colisiones de tipo abierto:

img

Obviamente en este punto se debe tener en cuenta todo lo que se conoce sobre la implementación de diccionarios o tablas de hash: correcta elección de la función de hash, la longitud inicial del diccionario, etc. Todo ese análisis debiera realizarse con los conocimientos sobre la estructura de dato en cuestión.

Declaraciones

El comportamiento de la tabla de símbolos depende mucho de las propiedades de las declaraciones del lenguaje que se está traduciendo. ¿Que se inserta?

Existen cuatro clases básicas de declaraciones:

Declaraciones de Constantes

const int SIZE = 199;
Declaraciones de Tipos

struct Entry
  {
      char * name;
      int count;
      struct Entry * next;
  }
  typedef struct Entry * Entry_ptr;

Declaraciones de Variables
int x;
int vector[10];
Declaraciones de Funciones
int funcion (int x, int y);
Un Ejemplo

A continuación se muestra una posible implementación para crear una entrada en una tabla de símbolos en C:

typedef enum { SYMBOL_LOCAL, SYMBOL_PARAM, SYMBOL_GLOBAL, SYMBOL_FUNCTION, SYMBOL_CONST} symbol_t;

struct symbol
{ 
  symbol_t kind;        
  struct type *type;
  char *name;
  int  which;
};

struct symbol * symbol_create(symbol_t kind, struct type * type, char * name)
{
    struct symbol *s = malloc(sizeof(*s));
    s->kind=kind;
    s->type=type;
    s->name=name;
    return s;
{

kind: indica si un símbolo es una variable local, función, variable global, etc.
type: apunta a una estructura de dato que indica el tipo de la variable.
name: el nombre de la variable.
which: la posición ordinal de la variable local o del parámetro en una función.
Reglas de Ámbito y Estructura de Bloques#
Las reglas de ámbito en los lenguajes de programación varían mucho, pero existen varias reglas que son comunes a muchos lenguajes.

Declaración antes de uso: Es una regla común utilizada en C y en PASCAL que requiere que se declare un nombre en el texto del programa antes que cualquier referencia al nombre. Esta declaración antes del uso permite construir la tabla de símbolos a medida que el análisis sintáctico continúa y que las búsquedas se realicen tan pronto como se encuentra una referencia de nombre en el código; si la búsqueda falla es que ha ocurrido una violación de la declaración antes del uso. Este tipo de regla fomenta compilaciones de una sola fase
Estructura de bloques: Es una propiedad común de los lenguajes modernos. Un bloque en un lenguaje de programación es cualquier construcción que pueda contener declaraciones. En C los bloques son unidades de compilación, es decir las declaraciones de procedimientos y funciones y las sentencias compuestas (encerradas entre llaves). En un lenguaje orientado a objetos la declaración de clases también son bloques. Un lenguaje esta estructurado en bloques si permite la anidación de bloques dentro de otros bloques, y si el ámbito de declaraciones en un bloque esta limitado a ese y otros bloques contenidos en el mismo, sujeto a la regla de anidación mas próxima: dadas varias declaraciones diferentes para el mismo nombre, la declaración que se aplica a una referencia es la única en ese bloque anidado mas próximo a la referencia.
En muchos lenguajes, como PASCAL y Ada, los procedimientos y funciones también pueden estar anidados (esto presenta un factor de complicación en el ambiente de tiempo de ejecución para tales lenguajes).
int i,j;

int f(int size)
   { char i, temp;
     ...
     { double j;
       ...
     } 
     ...
     { char * j;
       ...
     }
   } 
Para implementar ámbitos anidados, la operación de inserción de la tabla de símbolos no debe sobrescribir declaraciones anteriores, sino que las debe ocultar temporalmente, de manera que la operación de búsqueda solo encuentre la declaración para un nombre que se haya insertado más recientemente.

La operación de eliminación no debe eliminar todas las declaraciones correspondientes a un nombre, sino sólo la más reciente, revelando cualquier declaración previa.

Existen varias alternativas posibles para la implementación de ámbitos anidados. Una solución es construir una nueva tabla de símbolos para cada ámbito y vincular las tablas desde ámbitos internos a ámbitos externos.

img

De manera adicional o alternativa, pueden necesitarse asignar un nivel de anidación o profundidad de anidación a cada ámbito y registrar en cada entrada de la tabla de símbolos el nivel de anidación de cada nombre.
Gramáticas con Atributos#
Es un formalismo para expresar semántica.
Dada una gramática libre de contexto se le agregan:

Atributos: Estos atributos se agregan principalmente a los nodos no terminales

Funciones o Acciones Semánticas: B → Ab {accion semántica}

Idea: Para cada una de las producciones de los nodos no terminales

​ P,A,B ⇒ B.atributo1 Son arbitrarios

​ B.atributo2

​ B.atributo3

Las gramáticas con atributos trabajan con el árbol de parsing.

Una vez que se construye el árbol de parsing.

Se puede establecer un orden de dependencia en relación a los atributos

Existen tres clases de atributos:

Sintetizados: Son los atributos que en general suben desde el árbol, es decir, vienen de las hojas y van hacia la raíz.

E → T E.x=f(T,y)

A → B A.x=f(B,y)

y es un atributo de T x es un atributo de E

Heredados: Es justo el caso inverso de esta situación.

A → B B.y=f(A,x)

E → T T.y=f(E,x)

Los atributos de T están utilizando cosas que vienen de E

Inherentes: Son atributos fijos A → 0|1|2 A.x=0 "HARCODEADOS"
Son los generadores, van a estar generando los valores de los atributos en algún punto del árbol; generan las semillas de los valores.

Los atributos y las acciones semánticas establecen una relación de flujo de información, en cuanto a que para ejecutar una acción semántica particular en algún momento particular, se necesitan atributos, y estos atributos provienen de diferentes lugares, ramas que los sinteticen o definiciones de las raíces heredadas.

Sobre el árbol de parsing se sobreimprime un árbol de dependencia dado por cómo se necesitan los atributos. Lo que hace falta hacer es cómo sincronizar ese doble esquema

Por un lado el árbol se va a parsear en el orden en que se van a ir determinando las derivaciones en la pila, eso depende de cómo es la gramática, el tipo de parser, etc.

Ese orden es arbitrario y viene dado por las dependencias que se establecen a través de los atributos (si son sintetizados o heredados).

Una vez que se tiene un árbol sintáctico de cómo un parser reconoce una palabra para un lenguaje, se hace un grafo que se sobrescribe por arriba del árbol de parsing y que determina una relación de dependencia, es decir, que hay que hacer primero, después, y así… dependiendo de las reglas semánticas y lo que éstas hacen.

Ejemplo:

A → AB|B

B → 0|1

Reglas semánticas que permitan obtener el equivalente decimal del numero binario dado por el lenguaje generado por la gramática.

Sea S=101

Usar LL(1)

Se construye el árbol de parsing utilizando el método LL(1)
img

img

Se listan todas las producciones individual mente y se le asignan acciones y atributos:
A1 → A2B {A1.val=A2val*2 + B.val }

$$ 1 {$=$1}

A → B {A.val=B.val } (Se esta sintetizando el valor hacia arriba)

B → 0 {B.val=0}

B → 1 {B.val=1}

Atributos:

A.val

B.val

Analisis Semantico
Tipos de Datos y Verificación de Tipos#
Una de las tareas principales de un compilador es el cálculo y mantenimiento de la información de tipos de datos (inferencia de tipos), y el uso detal información para asegurar que cada parte de un programa tenga sentido bajo las reglas detipo del lenguaje (verificación de tipos).

La información del tipo de dato puede ser estática o dinámica, o una mezcla de las dos.

​ LISP –> Dinámica

​ C, Ada –> Estática

Teóricamente un tipo de dato es un conjunto de valores, o más precisamente, un conjunto de valores con ciertas operaciones sobre ellos.

En el terreno de la construcción de compiladores estos conjuntos por lo regular se describen mediante una expresión de tipo, que es un nombre de tipo –> integer, o una expresión estructurada tal como array[1..10] of real.

La información de tipo puede almacenarse:

1 En la tabla de símbolos (ver tabla de símbolos)

2 En la tabla de tipos

Introducción

Un lenguaje de programación siempre contiene un número de tipos incluidos, llamados tipos predefinidos. Normalmente corresponden a tipos numéricos, dependientes de la arquitectura de la máquina. También tipos elementales como char o boolean. Éstos se denominan tipos simples de datos. Ejemplo: Enteros –> complemento a 2.

Dado un conjunto de tipos predefinidos, se pueden crear nuevos tipos de datos utilizando constructores de tipos (array, struct, record) .

Estos constructores pueden veres como funciones que toman tipos existentes como parámetros y devuelven nuevos tipos con una estructura que depende del constructor; tipos estructurados.

Tabla de tipos

Generalmente, la tabla de tipos contiene información del nombre del tipo, el tamaño, el padre si se trata de un tipo compuesto, y alguna información más dependiendo del compilador.

La tabla suele estar ordenada por el nombre del tipo ya que no se debe repetir el mismo tipo.

Si el compilador no admite ámbitos anidados con una sola tabla, es suficiente.

Si el compilador admite ámbitos anidados, es necesario gestionarlos mediante la utilización de una pila de tablas.

Los campos mínimos necesarios:

Nombre: puede ser un int

Tipo base: se utiliza para tipos compuestos char[] –> tipo base char

Padre: es el tipo en el caso de declarar registros o structs

Dimensión: número de elementos de un tipo predefinido contenido en un tipo estructurado

Mínimo: se utiliza para el caso de la definición de arreglos

Máximo: ídem, pero el máximo índice

Ámbito: es el ámbito donde se definió el tipo; normalmente inicia en 0, se va incrementando o decrementando según se mueva uno dentro de los distintos ámbitos. Cuando se sale de un ámbito se deben eliminar todos los tipos que declaramos en él

cod	nombre	tipo base	padre	dimension	min	max	amb
Ejemplo:

Program P;

   Type vector = array[5..10] of integer;
   var v : vector;  x : integer;

   begin
      v[7] := 15;
      x:= v[7];
   end;
Se procesa la línea 1.

Tabla de tipos:

Cod	Nombre	TipoBase	Padre	Dimensión	Mínimo	Máximo	Ámbito
0	integer	-1	-1	1	-1	-1	0
1	boolean	-1	-1	1	-1	-1	0
Tabla de símbolos:

Cod	Nombre	Categoría	Tipo	NumPar	ListaPar	Dirección	Ámbito
Se procesa la línea 2.

Tabla de tipos:

Cod	Nombre	TipoBase	Padre	Dimensión	Mínimo	Máximo	Ámbito
0	integer	-1	-1	1	-1	-1	0
1	boolean	-1	-1	1	-1	-1	0
2	vector	0	-1	6	5	10	0
Tabla de símbolos:

Cod	Nombre	Categoría	Tipo	NumPar	ListaPar	Dirección	Ámbito
Se procesa la línea 3.

Tabla de tipos:

Cod	Nombre	TipoBase	Padre	Dimensión	Mínimo	Máximo	Ámbito
0	integer	-1	-1	1	-1	-1	0
1	boolean	-1	-1	1	-1	-1	0
2	vector	0	-1	6	5	10	0
Tabla de símbolos:

Cod	Nombre	Categoría	Tipo	NumPar	ListaPar	Dirección	Ámbito
1	x	variable	0	-1	null	9006	0
Gramática de declaraciones modula 2

S → var id: T;

T → array[num.. num] of T;

T → real | integer | char;

Construir un traductor (transpilador) a C

int x;
float y[4];
Dada una gramática con atributos se debe:

Decidir los atributos y asignarlos a los símbolos

Se deben insertar las acciones semánticas necesarias

Tener en cuenta:

i. Si todos los atributos son sintetizados, se pondrán las acciones S. Después de los atributos implicados, lo mejor es situarlos al final de la regla de producción. Los atributos sintetizados siempre hay que calcularlos después que hayan tomado valor los demás atributos.

ii. Si hay atributos heredados:

Un atributo heredado A.h debe calcularse antes que aparezca el símbolo A.
Un atributo sintetizado A.S no debe utilizarse antes de que aparezca el símbolo A.
iii. Una acción semántica no debe referirse a un atributo sintetizado de un símbolo a la derecha de la acción.

Abributos no terminales

T → REAL

​ {

​ T.array="";

​ T.tipo="float";

​ }

| INTEGER

{

​ T.array="";

​ T.tipo="int";

​ }

| CHAR

​ {

​ T.array="";

​ T.tipo="char";

​ }

T → array[num.. num1] of T1;

​ {

​ T.Tipo=T1.Tipo;

​ int lbound=atol(num);

​ int hbound=atol(num1);

​ int indice=hbound-lbound;

​ if [T.array=='/0']

​ {

​ T.array="[" + str(indice) + "]";​ }

​ else

​ {

​ T.array="[" + str(indice) +"]" + T1.array;

​ }

}

S → var id: T;

​ {

​ if [T.array=='/0']

​ S.trad= T.tipo + id.lexema +";";

​ else

​ S.trad= T.tipo. + id.lexema + T.array " ";"; }

Ejercicio:

Dada la siguiente gramática :

E → E + E

E → E * E

E → (E)

E → num | id

num es int, id un identificador de la tabla de símbolos.