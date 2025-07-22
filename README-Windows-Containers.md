# Guía para ejecutar con Windows Containers

## Prerrequisitos

1. **Docker Desktop**: Debe estar instalado y configurado para Windows containers
2. **Windows 10/11 Pro** o **Windows Server 2016/2019/2022**
3. **Hyper-V habilitado**

## Configurar Docker para Windows Containers

1. Abrir Docker Desktop
2. Hacer clic derecho en el icono de Docker en la bandeja del sistema
3. Seleccionar "Switch to Windows containers..." si está en modo Linux
4. Esperar a que Docker se reinicie

## Construcción y ejecución

### Opción 1: Usando Docker Compose (Recomendado)
```powershell
# Construir y ejecutar con Windows containers
docker-compose -f docker-compose.windows.yml up --build -d

# Ver logs
docker-compose -f docker-compose.windows.yml logs -f

# Parar y limpiar
docker-compose -f docker-compose.windows.yml down
```

### Opción 2: Usando Docker directamente
```powershell
# Construir imagen
docker build -f Dockerfile.windows -t scripts-python-app-windows .

# Ejecutar contenedor
docker run -d --name gestion-tareas-windows -p 8888:8888 scripts-python-app-windows

# Ver logs
docker logs gestion-tareas-windows

# Parar contenedor
docker stop gestion-tareas-windows
docker rm gestion-tareas-windows
```

## Ventajas de Windows Containers

- ✅ Soporte nativo para Microsoft Access Driver
- ✅ Compatibilidad completa con bases de datos .accdb
- ✅ Sin necesidad de modificar el código para modo demo
- ✅ Funcionalidad completa como en Windows nativo

## Verificar funcionamiento

1. Abrir navegador en: http://localhost:8888
2. El selector de entornos debe estar visible
3. BRASS debe ejecutarse sin errores de driver
4. Las bases de datos Access deben conectarse correctamente

## Troubleshooting

### Si Docker no permite Windows containers:
- Verificar que Hyper-V esté habilitado
- Verificar que Windows esté actualizado
- Reiniciar Docker Desktop

### Si el build falla:
- Verificar conexión a internet (descarga Python y Access Engine)
- Ejecutar como administrador si es necesario
- Revisar logs con: `docker build --no-cache -f Dockerfile.windows -t scripts-python-app-windows .`

### Si no encuentra Access Driver:
- El Dockerfile.windows instala automáticamente Microsoft Access Database Engine 2016
- Verificar que la descarga se completó exitosamente en los logs del build
