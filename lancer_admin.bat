@echo off
chcp 65001 > nul
cd /d "%~dp0"
echo Installation des dependances...
pip install flask beautifulsoup4 -q
echo.
echo Back office disponible sur http://localhost:5000
echo Fermez cette fenetre pour arreter le serveur.
echo.
python admin.py
pause
