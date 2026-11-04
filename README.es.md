# Laoshifu · Tradición china en tu agente de IA

[English](README.md) · [中文](README.zh-CN.md) · [Português](README.pt-BR.md)

Skill local y gratuito para explorar cartas natales chinas (BaZi + Zi Wei Dou Shu) o una pregunta concreta mediante Liu Yao + Qi Men Dun Jia. Las interpretaciones tradicionales no son predicciones científicamente demostradas.

## Pruébalo sin compartir datos personales

Descarga o clona el repositorio completo. Desde su carpeta, ejecuta:

```sh
python scripts/preview_examples.py --example contract --lang es
python scripts/preview_examples.py --example birth --lang es
```

Son ejemplos fijos con datos simulados; no son testimonios ni lecturas sobre ti. La vista previa verifica la integridad de la fuente y la traducción, no recoge datos, no crea una sesión personal ni inicia pagos. Solo necesita Python.

## Con tu agente

Las lecturas personales necesitan un agente compatible con SKILL.md que ejecute Python y Node.js. Se recomiendan Python 3.11+ y Node.js 20+. Conserva todas las carpetas del repositorio e indica al agente la ruta absoluta de SKILL.md. La instalación depende del programa que utilices.

> Usa Laoshifu desde el SKILL.md de esta carpeta. Responde en español y muestra primero el ejemplo fijo de contrato con --lang es. No solicites mis datos natales ni crees una sesión personal para esta vista previa.

Para empezar después una lectura personal, pide expresamente una consulta tradicional. Antes de recoger datos o guardar un caso, el agente debe explicar la ruta local, el plazo y la limpieza y obtener tu consentimiento. La sesión dura 24 horas por defecto: al caducar se bloquea su uso, pero **no se borran los archivos automáticamente**. La limpieza requiere vista previa y confirmación. El historial y los datos de tu proveedor de IA se gestionan por separado.

## Lugar, hora e idioma

Indica ciudad y país de nacimiento, fecha local en formato YYYY-MM-DD y hora del reloj local. La ruta internacional utiliza la zona IANA histórica y la convención de hora solar verdadera del paquete. No presupone UTC+8 ni el desfase actual. Si el lugar no está en el catálogo, hacen falta una zona IANA y longitud verificadas. Los cambios de horario de verano ambiguos requieren aclaración.

En Windows u otros sistemas sin base IANA, instala en el entorno Python de tu agente:

```sh
python -m pip install -r requirements-international.txt
```

Los ejemplos están traducidos al español. La explicación personal sigue el idioma elegido según la capacidad del modelo; algunas etiquetas de cálculo y auditoría conservan el chino para su comprobación. No todos los lugares o programas se han probado.

## Precio y reseñas

La edición de GitHub es **gratuita**, sin cuenta de pago ni compra. Tu proveedor de IA puede cobrar sus propios servicios. Los pagos de un posible servicio internacional futuro están por decidir.

Se agradecen reseñas independientes, también críticas. Consulta la [guía para evaluadores](references/REVIEWER-GUIDE.md) y no publiques datos personales en incidencias. Versión del skill 4.4.2; motor 4.2.0. [Detalles en inglés](README.md) · [Licencia](LICENSE.txt).
