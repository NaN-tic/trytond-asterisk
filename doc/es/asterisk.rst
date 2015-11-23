.. _how-to-configure-asterisk:

¿Como configurar Tryton para connectar con una centralita telefónica Asterisk?
==============================================================================

Asterisk nos permite crear una conexión AMI (Asterisk Manager 
Instance) para cada empresa y llamar directamente des de la ficha de cliente, 
usando la centralita que tengamos, siempre y cuando esta sea Asterisk y tenga 
conexión AMI configurada.

 * Crear la conexión: Para ello nos vamos al menú "Administración/ Asterisk/ 
   Asterisk Configuración".
   Aquí rellenemos todos los valores que tengamos de la centralita. El 
   **Nombre** 
   es puramente informativo. Lo demás depende de como se haya configurado la 
   centralita Asterisk.

Importante tener presente los posibles firewalls que haya configurados en los 
servidores, ya sea el de la centralita Asterisk como el de Tryton. 
