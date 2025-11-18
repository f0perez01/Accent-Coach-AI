# 🔧 Solución Inmediata para Streamlit Cloud

## El Problema

Tu app en Streamlit Cloud está fallando con `OSError` porque:
1. El código antiguo (con modelo Large) está cacheado
2. O el código nuevo aún no se ha subido

## ✅ Solución en 3 Pasos

### Paso 1: Limpiar el Caché en Streamlit Cloud

**EN LA APP EN STREAMLIT CLOUD**:

1. Ve al **sidebar** (barra lateral izquierda)
2. Scroll hasta abajo
3. Click en **"🗑️ Clear Model Cache"**
4. La app se recargará automáticamente

**ALTERNATIVA** (si no ves el botón):

1. En el menú hamburguesa (☰) arriba a la derecha
2. Click **"Settings"**
3. Click **"Clear cache"**
4. Click **"Rerun"**

### Paso 2: Verificar que el Código Nuevo está Deployed

**EN TU COMPUTADORA**:

```bash
# 1. Asegúrate de tener los últimos cambios
git status

# 2. Si hay cambios sin commitear:
git add .
git commit -m "Fix: Use base model for Streamlit Cloud"
git push origin main
```

**EN STREAMLIT CLOUD**:

1. Ve a tu dashboard: https://share.streamlit.io/
2. Click en tu app "Accent-Coach-AI"
3. Espera a que diga "App is running" (puede tardar 1-2 minutos)
4. La app se actualizará automáticamente al detectar el push

### Paso 3: Verificar el Modelo por Defecto

**EN LA APP**:

1. Abre **"Advanced Settings"** en el sidebar
2. Verifica que el modelo seleccionado es: **"Wav2Vec2 Base (Fast, Cloud-Friendly)"**
3. Si no lo es, selecciónalo y cierra el panel

## 🎯 Verificación Rápida

Para confirmar que está arreglado:

1. La app carga sin errores
2. El sidebar muestra el modelo correcto
3. Puedes grabar audio
4. Al analizar, NO sale OSError

## ❌ Si Aún Falla

### Opción A: Forzar Rebuild en Streamlit Cloud

1. En Streamlit Cloud dashboard
2. Click en los **3 puntos** (⋮) junto a tu app
3. Click **"Reboot app"**
4. Espera 2-3 minutos

### Opción B: Recrear la App

1. **Delete** la app actual en Streamlit Cloud
2. Click **"New app"**
3. Conecta tu repositorio de nuevo
4. Selecciona `app.py` o `app_alternative.py`
5. Click **"Deploy"**

### Opción C: Verificar Secrets

1. En Streamlit Cloud → Tu app → **"Settings"** → **"Secrets"**
2. Verifica que existe:
   ```toml
   GROQ_API_KEY = "tu-clave-aqui"
   ```
3. Si falta, añádela y **"Save"**

## 🐛 Debugging en Tiempo Real

### Ver los Logs

1. En tu app en Streamlit Cloud
2. Click **"Manage app"** (abajo a la derecha)
3. Click **"Logs"**
4. Busca líneas con ERROR

### Qué Buscar en los Logs

**BUENO** ✅:
```
Loading model facebook/wav2vec2-base-960h...
Successfully loaded model
```

**MALO** ❌:
```
OSError: Disk quota exceeded
Failed to download facebook/wav2vec2-large-960h
```

Si ves el error malo:
1. El caché no se limpió → Repite Paso 1
2. El código nuevo no está deployed → Repite Paso 2

## 🚀 Solución Rápida Alternativa: Usar app_alternative.py

Si `app.py` sigue fallando, cambia a la versión de upload:

**EN STREAMLIT CLOUD**:

1. Settings → General → Main file path
2. Cambia de `app.py` a `app_alternative.py`
3. Save
4. La app se recargará

**Ventajas de app_alternative.py**:
- Misma funcionalidad
- Usa upload en lugar de grabación directa
- Más confiable en navegadores

## 📊 Comparación de Modelos

| Modelo | Funciona en Cloud Free? |
|--------|------------------------|
| Wav2Vec2 Base | ✅ SÍ (default ahora) |
| Wav2Vec2 Large | ❌ NO (muy grande) |
| Wav2Vec2 XLSR | ⚠️ A veces |

## 💡 Tips para Evitar Problemas

1. **Siempre usa modelo Base** en producción en Streamlit Cloud free
2. **Limpia el caché** si cambias de modelo
3. **Monitorea los logs** después de cada deploy
4. **Prueba localmente primero** con `streamlit run app.py`

## 🔄 Workflow Recomendado

```bash
# Local
git pull
# hacer cambios
streamlit run app.py  # Probar localmente
git add .
git commit -m "descripción"
git push

# Streamlit Cloud
# Esperar auto-deploy (1-2 min)
# Limpiar caché si es necesario
# Verificar que funciona
```

## 📞 Última Opción: Streamlit Cloud Pro

Si necesitas el modelo Large:
- **$20/mes**
- 4GB RAM, más disco
- Sin límites de cache

Upgrade aquí: https://streamlit.io/cloud

---

## ✅ Checklist Final

Antes de reportar un bug, verifica:

- [ ] Código pusheado a GitHub
- [ ] Streamlit Cloud muestra "App is running"
- [ ] Caché limpiado
- [ ] Secrets configurados (GROQ_API_KEY)
- [ ] Modelo Base seleccionado por defecto
- [ ] Logs revisados (sin OSError)

Si todo está ✅ y aún falla:
1. Copia el error completo de los logs
2. Abre un issue en GitHub con el error
3. O contáctame

---

**¿Funcionó?** ¡Perfecto! Ahora puedes usar tu Accent Coach AI sin problemas. 🎉
