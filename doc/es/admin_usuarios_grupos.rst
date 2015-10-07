#:inside:trytond_doc/admin_usuarios_grupos:section:usuarios#

Permitir hacer llamadas automáticamente usando la centralita Asterisk
=====================================================================

Hay que tener :ref:`configurada la centralita<how-to-configure-asterisk>`.

1. Dar permisos a los usuarios que podrán configurar el asterisk es decir, 
   crear una conexión. Para ello, sólo tenemos que poner el grupo "*Asterisk 
   Administrator*" a aquél o aquellos usuarios que queremos que puedan 
   configurar/modificar la conexión AMI (Administración/ Usuarios/ Usuarios)

2. Una vez el asterisk configurado, podemos ir a cada usuario (Administración/ 
   Usuarios/ Usuarios) y configurarle la conexión asterisk. Dentro de la ficha 
   del usuario hay una pestaña Asterisk en la que hay que indicar la extensión 
   que se va a usar **Número interno**, el tipo de teléfono contra el que se va 
   a llamar **Tipo canal Asterisk** (normalmente SIP) y si queremos que la 
   pantalla del teléfono ponga siempre nuestro nombre o bien si lo dejamos en 
   blanco nos pondrá el nombre de a quién llamamos **ID de llamada**.

