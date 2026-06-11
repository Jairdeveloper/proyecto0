---
title: "Tutorial de GraphQL con Django y Graphene"
description: "Creación de un backend para un servicio acortador de URL usando GraphQL, Django y Graphene"
tags: [graphql, django, graphene, python, tutorial]
---

# Tutorial de GraphQL con Django y Graphene

## Introducción

GraphQL es un estándar de API de código abierto creado por Facebook como alternativa a las API REST. En vez de las API REST, GraphQL utiliza un sistema escrito para definir su estructura de datos, donde toda la información enviada y recibida debe cumplir con un Schema predefinido. También expone un endpoint individual para todas las comunicaciones en vez de múltiples URLs para diferentes recursos y resuelve el problema de overfetching devolviendo solo los datos pedidos por el cliente, generando así respuestas más pequeñas y concisas.

En este tutorial creará un backend para un servicio acortador de URL que toma cualquier URL y genera una versión más corta y legible. Además profundizaremos en los conceptos de GraphQL, como "Query" y "Mutation", y en las herramientas como la interfaz GraphiQL. Es posible que ya haya usado dichos servicios antes, como bit.ly.

Ya que GraphQL es un lenguaje con tecnología agnóstica, se implemente sobre varios lenguajes y marcos. Aquí, usará el lenguaje de programación Python de uso general, el marco web Django, y la biblioteca Graphene-Django como la implementación de GraphQL Python con integraciones específicas para Django.

## Requisitos previos

Para continuar con este tutorial, necesitará la versión 3.5 o superior de Python instalada en su equipo de desarrollo. Para instalar Python, siga el tutorial Cómo instalar y configurar un entorno de programación local para Python 3 para su SO. Asegúrese de crear e iniciar un entorno virtual; para seguir este tutorial, puede llamar a su directorio de proyecto `shorty`.

Es mejor tener un conocimiento básico de Django, pero no es obligatorio. Si le interesa, puede seguir la serie de Desarrollo de Django creada por la comunidad de DigitalOcean.

## Paso 1: Configurar el proyecto Django

En este paso, instalará todas las herramientas necesarias para la aplicación y para configurar su proyecto de Django.

Una vez que haya creado el directorio de su proyecto e iniciado su entorno virtual, como se indica en los requisitos previos, instale los paquetes necesarios usando pip, el administrador de paquetes de Python. Este tutorial instalará la versión 2.1.7 de Django y la versión 2.2.0 de Graphene-Django o superior.

```sh
pip install "django==2.1.7" "graphene-django>==2.2.0"
```

Ahora tendrá todas las herramientas necesarias para trabajar. A continuación, creará un proyecto Django usando el comando `django-admin`. Un proyecto es la plantilla predeterminada de Django, un conjunto de carpetas y archivos con todo lo necesario para iniciar el desarrollo de una aplicación web. En este caso, llamará a su proyecto `shorty` y lo creará dentro de su carpeta especificando el `.` al final:

```sh
django-admin startproject shorty .
```

Tras crear su proyecto, ejecutará las migraciones de Django. Estos archivos contienen código de Python generado por Django y se encargan de cambiar la estructura de la aplicación según los modelos de Django. Los cambios pueden incluir la creación de una tabla, por ejemplo. Por defecto, Django cuenta con su propio conjuntos de migraciones responsables de los subsistemas como la Autenticación de Django, de forma que es necesario ejecutarlos con el siguiente comando:

```sh
python manage.py migrate
```

Este comando utiliza el intérprete de Python para invocar una secuencia de comandos llamada `manage.py`, responsable de gestionar los diferentes aspectos de su proyecto, como crear aplicaciones o ejecutar migraciones.

Con esto, se mostrará un resultado similar al siguiente:

```
Operations to perform:
  Apply all migrations: admin, auth, contenttypes, sessions
Running migrations:
  Applying contenttypes.0001_initial... OK
  Applying auth.0001_initial... OK
  Applying admin.0001_initial... OK
  Applying admin.0002_logentry_remove_auto_add... OK
  Applying admin.0003_logentry_add_action_flag_choices... OK
  Applying contenttypes.0002_remove_content_type_name... OK
  Applying auth.0002_alter_permission_name_max_length... OK
  Applying auth.0003_alter_user_email_max_length... OK
  Applying auth.0004_alter_user_username_opts... OK
  Applying auth.0005_alter_user_last_login_null... OK
  Applying auth.0006_require_contenttypes_0002... OK
  Applying auth.0007_alter_validators_add_error_messages... OK
  Applying auth.0008_alter_user_username_max_length... OK
  Applying auth.0009_alter_user_last_name_max_length... OK
  Applying sessions.0001_initial... OK
```

Una vez que la base de datos de Django esté lista, inicie su servidor de desarrollo local:

```sh
python manage.py runserver
```

Esto proporcionará lo siguiente:

```
Performing system checks...

System check identified no issues (0 silenced).
March 18, 2020 - 15:46:15
Django version 2.1.7, using settings 'shorty.settings'
Starting development server at http://127.0.0.1:8000/
Quit the server with CONTROL-C.
```

Este comando eliminará la instrucción en su terminal e iniciará el servidor.

Visite la página http://127.0.0.1:8000 en su navegador local. Verá esta página:

> Página frontal del servidor local de Django

Para detener el servidor y volver a su terminal, pulse `CTRL+C`. Siempre que necesite acceder al navegador, asegúrese de que se esté ejecutando el comando anterior.

A continuación, terminará este paso habilitando la biblioteca Django-Graphene en el proyecto. Django tiene el concepto de *app*, una aplicación web con una responsabilidad específica. Un proyecto se compone de una o múltiples aplicaciones. Por ahora, abra el archivo `shorty/settings.py` en el editor de texto que prefiera. En este tutorial usaremos vim:

```sh
vim shorty/settings.py
```

El archivo `settings.py` gestiona todos los ajustes de su proyecto. Dentro, busque la entrada `INSTALLED_APPS` y añada la línea `'graphene_django'`:

```python
# shorty/shorty/settings.py

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'graphene_django',
]
```

Esta adición indica a Django que usará una aplicación llamada `graphene_django`, que instaló en el paso 1.

Al final del archivo, añada la siguiente variable:

```python
# shorty/shorty/settings.py

GRAPHENE = {
    'SCHEMA': 'shorty.schema.schema',
}
```

Esta última variable apunta a su esquema principal. Lo creará más tarde. En GraphQL, un Schema contiene todos los tipos de objeto, como "Resource", "Query" y "Mutation". Piense en ello como la documentación que representa todos los datos y funcionalidades disponibles en su sistema.

Tras realizar las modificaciones, guarde y cierre el archivo.

Con esto, habrá configurado el proyecto Django. En el siguiente paso, creará una aplicación Django y sus Modelos.

## Paso 2: Configurar una aplicación y modelos Django

Una plataforma Django está normalmente compuesta de un proyecto y muchas aplicaciones o *apps*. Una *app* describe un conjunto de funciones dentro de un proyecto, y, si está bien diseñada, puede reutilizarse en varios proyectos Django.

En este paso, creará una app llamada `shortener`, responsable de la función real de acortamiento de URL. Para crear su esqueleto básico, escriba el siguiente comando en su terminal:

```sh
python manage.py startapp shortener
```

Aquí usó los parámetros `startapp app_name`, que indican a `manage.py` que cree una app llamada `shortener`.

Para terminar de crear la app, abra el archivo `shorty/settings.py`:

```sh
vim shorty/settings.py
```

Añada el nombre de la app a la misma entrada `INSTALLED_APPS` que modificó antes:

```python
# shorty/shorty/settings.py

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'graphene_django',
    'shortener',
]
```

Guarde y cierre el archivo.

Una vez que se añada su `shortener` a `shorty/settings.py`, podrá proceder a crear los modelos para su proyecto. Los modelos son una de las funciones clave de Django. Se usan para representar una base de datos "al estilo de Python", lo cual le permite administrar, consultar y almacenar datos usando código Python.

Antes de abrir el archivo `models.py` para realizar cambios, en este tutorial se le proporcionará una descripción general de los cambios que realizará.

Su archivo modelo, `shortener/models.py`, contendrá el siguiente contenido una vez que haya sustituido el código existente:

```python
# shorty/shortener/models.py
from hashlib import md5

from django.db import models


class URL(models.Model):
    full_url = models.URLField(unique=True)
    url_hash = models.URLField(unique=True)
    clicks = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def clicked(self):
        self.clicks += 1
        self.save()

    def save(self, *args, **kwargs):
        if not self.id:
            self.url_hash = md5(self.full_url.encode()).hexdigest()[:10]
        return super().save(*args, **kwargs)
```

Aquí importará los paquetes requeridos que su código necesita. Añadirá la línea `from hashlib import md5` para importar la biblioteca estándar Python que se usará para crear un hash de la URL. La línea `from django.db import models` es un elemento auxiliar de Django para crear modelos.

> **Advertencia:** Este tutorial se refiere a hash como el resultado de una función que toma una entrada y siempre devuelve el mismo resultado. Este tutorial usará la función hash MD5 con fines demostrativos. Observe que MD5 tiene problemas de colisión y debería evitarse en producción.

A continuación, añadirá un modelo llamado `URL` con los siguientes campos:

- `full_url`: la URL a acortar.
- `url_hash`: un hash corto que representa la URL completa.
- `clicks`: cuántas veces se accedió a la URL corta.
- `created_at`: la fecha y hora en la que se creó la URL.

Generará la `url_hash` aplicando el algoritmo hash MD5 al campo `full_url` y usando solo los 10 primeros caracteres obtenidos durante el método `save()` del modelo, que se ejecuta cada vez que Django guarda una entrada en la base de datos. Adicionalmente, los acortadores de URL normalmente realizan un seguimiento de la cantidad de clics que se hacen sobre un enlace. Conseguirá esto invocando el método `clicked()` cuando un usuario visita una URL.

Ahora que ha revisado el código, abra el archivo `shortener/models.py`:

```sh
vim shortener/models.py
```

Sustituya el código con el contenido mostrado anteriormente. Asegúrese de guardar y cerrar el archivo.

Para aplicar estos cambios en la base de datos, deberá crear las migraciones ejecutando el siguiente comando:

```sh
python manage.py makemigrations
```

Esto generará el siguiente resultado:

```
Migrations for 'shortener':
  shortener/migrations/0001_initial.py
    - Create model URL
```

Luego ejecute las migraciones:

```sh
python manage.py migrate
```

Verá el siguiente resultado en su terminal:

```
Operations to perform:
  Apply all migrations: admin, auth, contenttypes, sessions, shortener
Running migrations:
  Applying shortener.0001_initial... OK
```

Ahora que ha configurado los modelos, en el siguiente paso creará el endpoint GraphQL y una "Query".

## Paso 3: Crear consultas

La arquitectura REST expone diferentes recursos en diferentes extremos, cada uno con una estructura de datos bien definida. Por ejemplo, puede recuperar una lista de usuarios en `/api/users`, esperando siempre los mismos campos. GraphQL, por otro lado, tiene un endpoint único para todas las interacciones, y utiliza *Query* para acceder a los datos. La principal diferencia, y la más valiosa, es que puede usar una "Query" para recuperar todos los usuarios en una única solicitud.

Comience creando una "Query" para recuperar todas las URL. Necesitará algunos elementos:

- Un tipo de URL, vinculado a su modelo definido previamente.
- Una instrucción "Query" llamada `urls`.
- Un método para resolver su "Query", lo que implica obtener todas las URL de la base de datos y devolverlas al cliente.

Cree un nuevo archivo llamado `shortener/schema.py`:

```sh
vim shortener/schema.py
```

Comience añadiendo las instrucciones `import` de Python:

```python
# shorty/shortener/schema.py
import graphene
from graphene_django import DjangoObjectType

from .models import URL
```

La primera línea importa la biblioteca principal `graphene`, que contiene los tipos GraphQL básicos, como `List`. `DjangoObjectType` es un elemento auxiliar para crear una definición de esquema desde cualquier modelo de Django y la tercera línea importa su modelo `URL` creado previamente.

Tras eso, cree un nuevo tipo de GraphQL para el modelo `URL` añadiendo las siguientes líneas:

```python
# shorty/shortener/schema.py

class URLType(DjangoObjectType):
    class Meta:
        model = URL
```

Finalmente, añada estas líneas para crear un tipo de "Query" para el modelo `URL`:

```python
# shorty/shortener/schema.py

class Query(graphene.ObjectType):
    urls = graphene.List(URLType)

    def resolve_urls(self, info, **kwargs):
        return URL.objects.all()
```

Este código crea una clase `Query` con un campo llamado `urls`, que es una lista del `URLType` definido previamente. Cuando se resuelve la "Query" a través del método `resolve_urls`, muestra las URL almacenadas en la base de datos.

El archivo completo `shortener/schema.py` se muestra aquí:

```python
# shorty/shortener/schema.py
import graphene
from graphene_django import DjangoObjectType

from .models import URL


class URLType(DjangoObjectType):
    class Meta:
        model = URL


class Query(graphene.ObjectType):
    urls = graphene.List(URLType)

    def resolve_urls(self, info, **kwargs):
        return URL.objects.all()
```

Guarde y cierre el archivo.

Todas las "Query" deben añadirse ahora al esquema principal. Piense en él como un depósito para todos sus recursos.

Cree un nuevo archivo en la ruta `shorty/schema.py` y ábralo con su editor:

```sh
vim shorty/schema.py
```

Importe los siguientes paquetes de Python añadiendo las líneas que se muestran a continuación. La primera, como se ha mencionado, contiene los tipos GraphQL básicos. La segunda línea importa el archivo de esquema creado previamente.

```python
# shorty/shorty/schema.py
import graphene

import shortener.schema
```

A continuación, añada la clase `Query` principal. Contendrá, mediante herencia, todas las "Query" para las operaciones futuras creadas:

```python
# shorty/shorty/schema.py

class Query(shortener.schema.Query, graphene.ObjectType):
    pass
```

Por último, cree la variable `schema`:

```python
# shorty/shorty/schema.py

schema = graphene.Schema(query=Query)
```

El ajuste `SCHEMA` que definió en el paso 2 apunta a la variable `schema` que acaba de crear.

El archivo completo `shorty/schema.py` se muestra aquí:

```python
# shorty/shorty/schema.py
import graphene

import shortener.schema


class Query(shortener.schema.Query, graphene.ObjectType):
    pass

schema = graphene.Schema(query=Query)
```

Guarde y cierre el archivo.

A continuación, habilite el extremo GraphQL y la interfaz GraphiQL, una interfaz web gráfica que se usa para interactuar con el sistema GraphQL.

Abra el archivo `shorty/urls.py`:

```sh
vim shorty/urls.py
```

Con fines de aprendizaje, elimine el contenido del archivo y guárdelo, para que pueda comenzar desde cero.

Las primeras líneas que añadirá son las instrucciones de importación de Python:

```python
# shorty/shorty/urls.py
from django.urls import path
from django.views.decorators.csrf import csrf_exempt

from graphene_django.views import GraphQLView
```

Django utiliza la función `path` para crear una URL accesible para la interfaz GraphiQL. A continuación, importe `csrf_exempt`, que permite a los clientes enviar datos al servidor. Puede encontrar una explicación completa en la Documentación de Graphene. En la última línea, importó el código real responsable de la interfaz a través de `GraphQLView`.

A continuación, cree una variable llamada `urlpatterns`:

```python
# shorty/shorty/urls.py

urlpatterns = [
    path('graphql/', csrf_exempt(GraphQLView.as_view(graphiql=True))),
]
```

Esto unirá todo el código necesario para hacer que la interfaz GraphiQL esté disponible en la ruta `graphql/`:

El archivo completo `shorty/urls.py` se muestra aquí:

```python
# shorty/shorty/urls.py
from django.urls import path
from django.views.decorators.csrf import csrf_exempt

from graphene_django.views import GraphQLView

urlpatterns = [
    path('graphql/', csrf_exempt(GraphQLView.as_view(graphiql=True))),
]
```

Guarde el archivo y ciérrelo.

De vuelta en el terminal, ejecute el comando `python manage.py runserver` (si no se está ejecutando aún):

```sh
python manage.py runserver
```

Abra su navegador web en la dirección http://localhost:8000/graphql. Se le presentará esta pantalla:

> Interfaz GraphiQL

GraphiQL es una interfaz donde puede ejecutar instrucciones de GraphQL y ver los resultados. Una función es la sección *Docs* en la parte superior derecha. Debido a que en GraphQL se debe escribir todo, obtendrá documentación gratuita sobre sus "Type" (tipo), "Query" (consulta) y "Mutation" (mutación), entre otros aspectos.

Tras explorar la página, inserte su primera "Query" en el área de texto principal:

```graphql
query {
  urls {
    id
    fullUrl
    urlHash
    clicks
    createdAt
  }
}
```

Este contenido muestra cómo se estructura una "Query" de GraphQL: primero utiliza la palabra clave `query` para indicar al servidor que solo desea recuperar algunos de los datos. A continuación, usará el campo `urls` definido en el archivo `shortener/schema.py` dentro de la clase `Query`. Desde ahí, solicita explícitamente todos los campos definidos en el modelo `URL` usando el estilo de capitalización *camelCase*, que es el predeterminado para GraphQL.

Ahora, haga clic en el botón de flecha de reproducción en la parte superior izquierda.

Recibirá la siguiente respuesta, indicando que aún no tiene URLs:

```json
{
  "data": {
    "urls": []
  }
}
```

Esto muestra que GraphQL está funcionando. En su terminal, pulse `CTRL+C` para detener su servidor.

En este paso, logró un gran avance al crear el extremo de GraphQL, realizar una "Query" para obtener todas las URLs y habilitar la interfaz de GraphiQL. Ahora, creará "Mutation" para cambiar la base de datos.

## Paso 4: Crear mutaciones

La mayoría de las aplicaciones tienen una forma de cambiar el estado de la base de datos añadiendo, actualizando o eliminando datos. En GraphQL, estas operaciones se denominan *Mutation*. Tienen el aspecto de las "Query" pero utilizan argumentos para enviar datos al servidor.

Para crear su primera "Mutation", abra `shortener/schema.py`:

```sh
vim shortener/schema.py
```

Al final del archivo, comience añadiendo una nueva clase llamada `CreateURL`:

```python
# shorty/shortener/schema.py

class CreateURL(graphene.Mutation):
    url = graphene.Field(URLType)
```

Esta clase hereda el elemento auxiliar `graphene.Mutation` para tener las capacidades de una mutación GraphQL. También tiene un nombre de propiedad `url`, que define el contenido mostrado por el servidor tras completarse la "Mutation". En este caso, será una estructura de datos `URLType`.

A continuación añada una subclase llamada `Arguments` a la clase ya definida:

```python
# shorty/shortener/schema.py

    class Arguments:
        full_url = graphene.String()
```

Esto define qué datos serán aceptados por el servidor. Aquí está esperando un parámetro llamado `full_url` con un contenido `String`.

Ahora añada las siguientes líneas para crear el método `mutate`:

```python
# shorty/shortener/schema.py

    def mutate(self, info, full_url):
        url = URL(full_url=full_url)
        url.save()
        return CreateURL(url=url)
```

Este método `mutate` hace gran parte del trabajo al recibir los datos del cliente y guardarlos en la base de datos. Al final, muestra la clase que contiene el elemento recién creado.

Por último, cree una clase `Mutation` para albergar todas las "Mutation" para su app añadiendo estas líneas:

```python
# shorty/shortener/schema.py

class Mutation(graphene.ObjectType):
    create_url = CreateURL.Field()
```

Hasta ahora, solo tendrá una mutación llamada `create_url`.

El archivo completo `shortener/schema.py` se muestra aquí:

```python
# shorty/shortener/schema.py
import graphene
from graphene_django import DjangoObjectType

from .models import URL


class URLType(DjangoObjectType):
    class Meta:
        model = URL


class Query(graphene.ObjectType):
    urls = graphene.List(URLType)

    def resolve_urls(self, info, **kwargs):
        return URL.objects.all()


class CreateURL(graphene.Mutation):
    url = graphene.Field(URLType)

    class Arguments:
        full_url = graphene.String()

    def mutate(self, info, full_url):
        url = URL(full_url=full_url)
        url.save()
        return CreateURL(url=url)


class Mutation(graphene.ObjectType):
    create_url = CreateURL.Field()
```

Cierre y guarde el archivo.

Para terminar de añadir la "Mutation", cambie el archivo `shorty/schema.py`:

```sh
vim shorty/schema.py
```

Altere el archivo para incluir el siguiente código resaltado:

```python
# shorty/shorty/schema.py
import graphene

import shortener.schema


class Query(shortener.schema.Query, graphene.ObjectType):
    pass


class Mutation(shortener.schema.Mutation, graphene.ObjectType):
    pass


schema = graphene.Schema(query=Query, mutation=Mutation)
```

Guarde y cierre el archivo. Si no está ejecutando el servidor local, inícielo:

```sh
python manage.py runserver
```

Navegue a http://localhost:8000/graphql en su navegador web. Ejecute su primera "Mutation" en la interfaz web GraphiQL ejecutando la siguiente instrucción:

```graphql
mutation {
  createUrl(fullUrl:"https://www.digitalocean.com/community") {
    url {
      id
      fullUrl
      urlHash
      clicks
      createdAt
    }
  }
}
```

Compuso la "Mutation" con el nombre `createURL`, el argumento `fullUrl` y los datos que desea en la respuesta definida dentro del campo `url`.

El resultado contendrá la información de la URL que acaba de crear dentro del campo `data` de GraphQL, como se muestra aquí:

```json
{
  "data": {
    "createUrl": {
      "url": {
        "id": "1",
        "fullUrl": "https://www.digitalocean.com/community",
        "urlHash": "077880af78",
        "clicks": 0,
        "createdAt": "2020-01-30T19:15:10.820062+00:00"
      }
    }
  }
}
```

Con eso, se añadió una URL a la base de datos con su versión en hash, como puede ver en el campo `urlHash`. Intente ejecutar la "Query" que creó en el último paso para ver su resultado:

```graphql
query {
  urls {
    id
    fullUrl
    urlHash
    clicks
    createdAt
  }
}
```

El resultado mostrará la URL almacenada:

```json
{
  "data": {
    "urls": [
      {
        "id": "1",
        "fullUrl": "https://www.digitalocean.com/community",
        "urlHash": "077880af78",
        "clicks": 0,
        "createdAt": "2020-03-18T21:03:24.664934+00:00"
      }
    ]
  }
}
```

También puede intentar ejecutar la misma "Query", pero solo pidiendo los campos que desea.

A continuación, inténtelo una vez más con una URL diferente:

```graphql
mutation {
  createUrl(fullUrl:"https://www.digitalocean.com/write-for-donations/") {
    url {
      id
      fullUrl
      urlHash
      clicks
      createdAt
    }
  }
}
```

El resultado será lo siguiente:

```json
{
  "data": {
    "createUrl": {
      "url": {
        "id": "2",
        "fullUrl": "https://www.digitalocean.com/write-for-donations/",
        "urlHash": "703562669b",
        "clicks": 0,
        "createdAt": "2020-01-30T19:31:10.820062+00:00"
      }
    }
  }
}
```

El sistema ahora puede crear URLs cortas y listarlas. En el siguiente paso, permitirá a los usuarios acceder a una URL por medio de su versión corta y los redirigirá a la página correcta.

## Paso 5: Crear el endpoint de acceso

En este paso, usará el método Django Views, un método que toma una solicitud y devuelve una respuesta, para redirigir a cualquiera que acceda al endpoint http://localhost:8000/url_hash a su URL completa.

Abra el archivo `shortener/views.py` con su editor:

```sh
vim shortener/views.py
```

Para comenzar, importe los dos paquetes sustituyendo el contenido con las siguientes líneas:

```python
# shorty/shortener/views.py
from django.shortcuts import get_object_or_404, redirect

from .models import URL
```

A continuación, creará un Django View llamado `root`. Añada este código responsable de la vista al final del archivo:

```python
# shorty/shortener/views.py

def root(request, url_hash):
    url = get_object_or_404(URL, url_hash=url_hash)
    url.clicked()
    return redirect(url.full_url)
```

Esto recibe un argumento llamado `url_hash` desde la URL solicitada por un usuario. Dentro de la función, la primera línea intenta obtener la URL de la base de datos usando el argumento `url_hash`. Si no se encuentra, devuelve el error HTTP 404 al cliente, lo que significa que falta el recurso. Después, aumenta la propiedad `clicked` de la entrada de URL, asegurando que realiza un seguimiento de la cantidad de veces que se accede a la URL. Al final, redirige el cliente a la URL solicitada.

El archivo completo `shortener/views.py` se muestra aquí:

```python
# shorty/shortener/views.py
from django.shortcuts import get_object_or_404, redirect

from .models import URL


def root(request, url_hash):
    url = get_object_or_404(URL, url_hash=url_hash)
    url.clicked()
    return redirect(url.full_url)
```

Guarde y cierre el archivo.

A continuación, abra `shorty/urls.py`:

```sh
vim shorty/urls.py
```

Añada el siguiente código para habilitar la vista `root`:

```python
# shorty/shorty/urls.py
from django.urls import path
from django.views.decorators.csrf import csrf_exempt

from graphene_django.views import GraphQLView

from shortener.views import root


urlpatterns = [
    path('graphql/', csrf_exempt(GraphQLView.as_view(graphiql=True))),
    path('<str:url_hash>/', root, name='root'),
]
```

La vista `root` será accesible en la ruta `/` de su servidor, aceptando un `url_hash` como parámetro de la cadena.

Guarde y cierre el archivo. Si no está ejecutando el servidor local, inícielo ejecutando `python manage.py runserver`.

Para probar su nueva adición, abra su navegador web y acceda a la URL http://localhost:8000/077880af78. Observe que la última parte de la URL es el hash creado por la "Mutation" del paso 5. Accederá a la página URL del hash; en este caso, el sitio web de la comunidad de DigitalOcean.

Ahora que el redireccionamiento de la URL funciona, hará que la aplicación sea más segura implementando la gestión de errores cuando se ejecute la "Mutation".

## Paso 6: Implementar la gestión de errores

Gestionar errores es una práctica recomendada en todas las aplicaciones, ya que los desarrolladores normalmente no controlan lo que se enviará al servidor. En un sistema complejo como GraphQL, pueden salir mal muchas cosas, desde que el cliente pida los datos erróneos hasta que el servidor pierda el acceso a la base de datos.

Como sistema escrito, GraphQL puede verificar todo lo que el cliente solicite y reciba en una operación conocida como *validación de esquema*. Puede ver esto en acción realizando una "Query" con un campo no existente.

Diríjase a http://localhost:8000/graphql en su navegador una vez más y ejecute la siguiente "Query" en la interfaz GraphiQL con el campo `iDontExist`:

```graphql
query {
  urls {
    id
    fullUrl
    urlHash
    clicks
    createdAt
    iDontExist
  }
}
```

Ya que no hay un campo `iDontExist` definido en su "Query", GraphQL muestra un mensaje de error:

```json
{
  "errors": [
    {
      "message": "Cannot query field \"iDontExist\" on type \"URLType\".",
      "locations": [
        {
          "line": 8,
          "column": 5
        }
      ]
    }
  ]
}
```

Esto es importante porque, en el sistema escrito de GraphQL, el objetivo es enviar y recibir solo la información ya definida en el esquema.

La aplicación actual acepta cualquier cadena arbitraria en el campo `full_url`. El problema es que si alguien envía una URL mal construida, usted no redirigiría al usuario a ningún sitio al probar la información almacenada. En este caso, necesita verificar si la `full_url` está bien formateada antes de guardarla en la base de datos, y, si hay cualquier error, elevar la excepción `GraphQLError` con un mensaje personalizado.

Vamos a implementar esta funcionalidad en dos pasos. Primero, abra el archivo `shortener/models.py`:

```sh
vim shortener/models.py
```

Añada las siguientes importaciones:

```python
# shorty/shortener/models.py
from hashlib import md5

from django.db import models
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError

from graphql import GraphQLError
```

`URLValidator` es un ayudante de Django para validar una cadena URL y Graphene utiliza `GraphQLError` para elevar excepciones con un mensaje personalizado.

A continuación, asegúrese de validar la URL recibida por el usuario antes de guardarla en la base de datos. Modifique el método `save` del modelo `URL`:

```python
# shorty/shortener/models.py

class URL(models.Model):
    full_url = models.URLField(unique=True)
    url_hash = models.URLField(unique=True)
    clicks = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def clicked(self):
        self.clicks += 1
        self.save()

    def save(self, *args, **kwargs):
        if not self.id:
            self.url_hash = md5(self.full_url.encode()).hexdigest()[:10]

        validate = URLValidator()
        try:
            validate(self.full_url)
        except ValidationError as e:
            raise GraphQLError('invalid url')

        return super().save(*args, **kwargs)
```

Primero, este código inicia el `URLValidator` en la variable `validate`. Dentro del bloque `try/except`, `validate()` la URL recibida y eleva un `GraphQLError` con el mensaje personalizado `invalid url` si se produjo algún error.

El archivo completo `shortener/models.py` se muestra aquí:

```python
# shorty/shortener/models.py
from hashlib import md5

from django.db import models
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError

from graphql import GraphQLError


class URL(models.Model):
    full_url = models.URLField(unique=True)
    url_hash = models.URLField(unique=True)
    clicks = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def clicked(self):
        self.clicks += 1
        self.save()

    def save(self, *args, **kwargs):
        if not self.id:
            self.url_hash = md5(self.full_url.encode()).hexdigest()[:10]

        validate = URLValidator()
        try:
            validate(self.full_url)
        except ValidationError as e:
            raise GraphQLError('invalid url')

        return super().save(*args, **kwargs)
```

Guarde y cierre el archivo. Si no está ejecutando el servidor local, inícielo con `python manage.py runserver`.

A continuación, pruebe su nueva gestión de errores en http://localhost:8000/graphql. Intente crear una nueva URL con una `full_url` no válida en la interfaz GraphiQL:

```graphql
mutation {
  createUrl(fullUrl:"not_valid_url"){
    url {
      id
      fullUrl
      urlHash
      clicks
      createdAt
    }
  }
}
```

Cuando envíe una URL no válida, su excepción se elevará con el mensaje personalizado:

```json
{
  "errors": [
    {
      "message": "invalid url",
      "locations": [
        {
          "line": 2,
          "column": 3
        }
      ],
      "path": [
        "createUrl"
      ]
    }
  ],
  "data": {
    "createUrl": null
  }
}
```

Si mira en su terminal donde está en ejecución `python manage.py runserver`, aparecerá un error:

```
graphql.error.located_error.GraphQLLocatedError: invalid url

[30/Jan/2020 19:46:32] "POST /graphql/ HTTP/1.1" 200 121
```

Un extremo de GraphQL siempre generará un error con un código de estado HTTP 200, lo que normalmente significa que el resultado es correcto. Recuerde que, aunque GraphQL se construye sobre HTTP, no utiliza los conceptos de los códigos de estado HTTP o los métodos HTTP como REST hace.

Con el manejo de errores implementado, ahora puede implementar un mecanismo para filtrar sus "Query", minimizando la información devuelta por el servidor.

## Paso 7: Implementar filtros

Imagine que ha comenzado a usar el acortador de URL para añadir sus propios enlaces. Después de un tiempo, habrá tantas entradas que será difícil encontrar la correcta. Puede resolver este problema usando filtros.

El filtrado es un concepto común en las API de REST; normalmente, se anexa a la URL un parámetro Query con un campo y un valor. A modo de ejemplo, para filtrar todos los usuarios llamados *jojo*, podría usar `GET /api/users?name=jojo`.

En GraphQL, usará argumentos "Query" como filtros. Crean una interfaz perfecta y limpia.

Puede resolver el problema de encontrar una URL permitiendo que el cliente filtre las URL por nombre con el campo `full_url`. Para implementar eso, abra el archivo `shortener/schema.py`:

```sh
vim shortener/schema.py
```

Primero, importe el método `Q`:

```python
# shorty/shortener/schema.py
import graphene
from graphene_django import DjangoObjectType
from django.db.models import Q

from .models import URL
```

Esto se usará para filtrar la consulta de su base de datos.

A continuación, reescriba toda la clase `Query`:

```python
# shorty/shortener/schema.py

class Query(graphene.ObjectType):
    urls = graphene.List(URLType, url=graphene.String())

    def resolve_urls(self, info, url=None, **kwargs):
        queryset = URL.objects.all()

        if url:
            _filter = Q(full_url__icontains=url)
            queryset = queryset.filter(_filter)

        return queryset
```

Las modificaciones que está realizando son:

- Añadir el parámetro de filtro `url` dentro de la variable `urls` y el método `resolve_urls`.
- Dentro de `resolve_urls`, si se da un parámetro llamado `url`, filtrar los resultados de la base de datos para devolver solo las URLs que contienen el valor dado, usando el método `Q(full_url__icontains=url)`.

El archivo completo `shortener/schema.py` se muestra aquí:

```python
# shorty/shortener/schema.py
import graphene
from graphene_django import DjangoObjectType
from django.db.models import Q

from .models import URL


class URLType(DjangoObjectType):
    class Meta:
        model = URL


class Query(graphene.ObjectType):
    urls = graphene.List(URLType, url=graphene.String())

    def resolve_urls(self, info, url=None, **kwargs):
        queryset = URL.objects.all()

        if url:
            _filter = Q(full_url__icontains=url)
            queryset = queryset.filter(_filter)

        return queryset


class CreateURL(graphene.Mutation):
    url = graphene.Field(URLType)

    class Arguments:
        full_url = graphene.String()

    def mutate(self, info, full_url):
        url = URL(full_url=full_url)
        url.save()
        return CreateURL(url=url)


class Mutation(graphene.ObjectType):
    create_url = CreateURL.Field()
```

Guarde y cierre el archivo. Si no ejecuta el servidor local, inícielo con `python manage.py runserver`.

Pruebe sus últimos cambios en http://localhost:8000/graphql. En la interfaz GraphiQL, escriba la siguiente instrucción. Filtrará todas las URL con la palabra `community`:

```graphql
query {
  urls(url:"community") {
    id
    fullUrl
    urlHash
    clicks
    createdAt
  }
}
```

El resultado es solo una entrada, ya que acaba de añadir una URL con la cadena `community` en ella. Si añadió más URL antes, el resultado puede variar.

```json
{
  "data": {
    "urls": [
      {
        "id": "1",
        "fullUrl": "https://www.digitalocean.com/community",
        "urlHash": "077880af78",
        "clicks": 1,
        "createdAt": "2020-01-30T19:27:36.243900+00:00"
      }
    ]
  }
}
```

Ahora, tiene la capacidad de buscar en sus URLs. Sin embargo, con demasiados enlaces, sus clientes pueden quejarse de que la lista de URLs devuelve más datos de los que la aplicación puede gestionar. Para resolver esto, implementará la paginación.

## Paso 8: Implementar la paginación

Los clientes que usen su backend pueden quejarse de que el tiempo de respuesta es demasiado largo o que el tamaño es demasiado grande si hay demasiadas entradas de URL. Incluso puede ser difícil para su base de datos reunir un conjunto tan enorme de información. Para resolver este problema, puede permitir que el cliente especifique cuántos elementos quiere dentro de cada solicitud usando una técnica llamada *paginación*.

No existe una forma predeterminada de implementar esta función. Incluso en las API de REST puede verlo en los encabezados HTTP o en los parámetros de consulta, con diferentes nombres y comportamientos.

En esta aplicación, implementará la paginación habilitando dos argumentos más en la "Query" de URL: `first` y `skip`. `first` seleccionará el primer número de elementos variables y `skip` especificará cuántos elementos deben omitirse desde el principio. Por ejemplo, si usa `first == 10` y `skip == 5` se obtendrán las primeras 10 URL, pero se omitirán 5, con lo cual se mostrarán solo las 5 restantes.

Implementar esta solución es similar a añadir un filtro.

Abra el archivo `shortener/schema.py`:

```sh
vim shortener/schema.py
```

En el archivo, cambie la clase `Query` añadiendo los dos nuevos parámetros en la variable `urls` y el método `resolve_urls`:

```python
# shorty/shortener/schema.py
import graphene
from graphene_django import DjangoObjectType
from django.db.models import Q

from .models import URL


class Query(graphene.ObjectType):
    urls = graphene.List(URLType, url=graphene.String(), first=graphene.Int(), skip=graphene.Int())

    def resolve_urls(self, info, url=None, first=None, skip=None, **kwargs):
        queryset = URL.objects.all()

        if url:
            _filter = Q(full_url__icontains=url)
            queryset = queryset.filter(_filter)

        if first:
            queryset = queryset[:first]

        if skip:
            queryset = queryset[skip:]

        return queryset
```

Este código utiliza los parámetros `first` y `skip` recién creados dentro del método `resolve_urls` para filtrar la consulta de la base de datos.

Guarde y cierre el archivo. Si no está ejecutando el servidor local, inícielo con `python manage.py runserver`.

Para probar la paginación, emita la siguiente "Query" en la interfaz GraphiQL en http://localhost:8000/graphql:

```graphql
query {
  urls(first: 2, skip: 1) {
    id
    fullUrl
    urlHash
    clicks
    createdAt
  }
}
```

Su acortador de URL mostrará la segunda URL creada en su base de datos:

```json
{
  "data": {
    "urls": [
      {
        "id": "2",
        "fullUrl": "https://www.digitalocean.com/write-for-donations/",
        "urlHash": "703562669b",
        "clicks": 0,
        "createdAt": "2020-01-30T19:31:10.820062+00:00"
      }
    ]
  }
}
```

Esto muestra que la función de paginación funciona. Puede experimentar añadiendo más URLs y probando diferentes conjuntos de `first` y `skip`.

## Conclusión

Todo el ecosistema de GraphQL crece día a día y una comunidad activa lo respalda. Empresas como GitHub y Facebook han demostrado que está listo para la producción, y ahora puede aplicar esta tecnología a sus propios proyectos.

En este tutorial, creó un acortador de URL usando GraphQL, Python y Django y conceptos como "Query" y "Mutation". Pero sobre todo, ahora comprende cómo depender de estas tecnologías para crear aplicaciones web usando el marco web Django.

Puede explorar más sobre GraphQL y las herramientas usadas aquí en el sitio web de [GraphQL](https://graphql.org) y en los sitios web de documentación de [Graphene](https://docs.graphene-python.org). Además, DigitalOcean tiene tutoriales adicionales para Python y Django que puede usar si desea aprender más sobre esto.
