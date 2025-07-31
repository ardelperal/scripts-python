Siempre que tengas dudas de como usar los sql en pruebas o en refactorizaciones mira el archivo legacy de donde proviene
Siempre revisa el SQL para que sea compatible con access, SELECT TOP 5, o cosas como CASE en where no están permitidas
Antes de implementar una nueva función mira a ver si ya está en la parte común del proyecto
Los tests de integración siempre que sea posible quiero que tengan interacción real con las bases de datos, pero siempre las locales independientemente del entorno que esté en .env
Revisa las dependencias que no tengan vulnerabilidades críticas
Nunca dejes placeholders en las funcionalidades. 
Nunca hagas pruebas de sql injections en este proyecto
