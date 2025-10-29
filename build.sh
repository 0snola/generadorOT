#!/bin/bash
set -e

echo "🔧 Configurando entorno de build..."

# Actualizar pip, setuptools y wheel a las últimas versiones
pip install --upgrade pip setuptools wheel

# Instalar herramientas de compilación si es necesario
apt-get update -qq
apt-get install -y -qq build-essential python3-dev

# Instalar dependencias con --only-binary para asegurar que usa wheels precompilados
pip install --only-binary :all: -r requirements.txt || pip install -r requirements.txt

echo "✅ Build completado"
