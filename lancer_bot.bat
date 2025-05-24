@echo off
title Lancement du bot de trading

cd /d "%~dp0"

echo === Lancement du bot...
start "" python start-up.py

echo === Lancement du serveur...
start "" python server.py

echo === Lancement du watchdog...
start "" python watchdog.py

echo.
echo === Tout est lancé. Fermez cette fenêtre pour quitter.
pause
