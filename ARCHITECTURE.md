# Ghost Bank Miner Architecture

## Producto activo

Aplicacion web para procesar PDFs localmente, extraer un numero OP de la primera pagina, planear nombres, generar un ZIP y exportar un reporte CSV. Incluye un asistente de analisis con IA sin persistencia.

## Runtime activo

- Cliente web: `index.html`.
- Procesamiento PDF: navegador mediante PDF.js y JSZip.
- API de IA: funciones en `api/` y servidor local `server.js`.
- Persistencia: ninguna.

## Non-goals

- No es un sistema documental persistente.
- No almacena PDFs, chats ni resultados.
- No conserva el parser oculto `pdf-to-excel` como feature activa.
- No conserva los scripts Python de procesamiento masivo como producto activo.
- No migra a TypeScript.

## Datos

| Dato | Ubicacion o destino | Politica |
|---|---|---|
| PDFs seleccionados | Memoria del navegador | No se persisten ni se envian al servidor en el flujo de renombrado. |
| Mensajes e imagenes del asistente | Proveedor durante la consulta | No se persisten. |
| Credenciales de proveedores | `.env`, ignorado por Git | No se versionan ni se mueven a `legacy/`. |
| Reportes de procesamiento reales | `ghost-bank-script/resumen-*` | Son datos generados; deben salir del repositorio, no ir a `legacy/`. |
| Parser `pdf-to-excel` y scripts Python | Codigo dormido | Candidatos a `legacy/`. |
| Fixtures de extraccion | `test/fixtures/synthetic/` | Deben ser texto y metadata sinteticos. |

## Direccion objetivo

La migracion futura usara Vite, React y JavaScript. `app/` compondra la aplicacion, `features/documentos` procesara PDFs localmente, `features/asistente` manejara IA y `shared/` contendra utilidades reutilizables.

## Invariantes

- El renombrado de PDFs permanece local.
- No existe persistencia de documentos ni chat.
- El codigo activo no importa desde `legacy/`.
- `legacy/` no entra en build ni despliegue.
- Los datos reales no se usan como fixtures.
