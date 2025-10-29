#!/bin/bash
set -e

echo "🔧 Configurando entorno de build..."

# Actualizar pip, setuptools y wheel a las últimas versiones
pip install --upgrade pip setuptools wheel

# Instalar dependencias
echo "📦 Instalando dependencias..."
pip install -r requirements.txt

echo "✅ Build completado"
