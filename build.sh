#!/bin/bash
# build.sh — compilar APK en Termux/Linux
# Requiere: pip install buildozer cython
# Requiere: pkg install openjdk-17 git

set -e
echo "[*] Limpiando builds previos..."
rm -rf bin .buildozer

echo "[*] Compilando APK (debug)..."
buildozer android debug

echo "[*] Listo. APK en ./bin/"
ls -la bin/
