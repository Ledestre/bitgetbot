import os
import sys
import winshell
import win32com.client

# === Nom du fichier .bat et du raccourci ===
bat_name = "LANCER_BOT.bat"
shortcut_name = "Lancer le bot.lnk"

# === Contenu du fichier .bat ===
bat_content = f'@echo off\ncd /d "{os.getcwd()}"\npython startup.py\npause'

# === Création du .bat dans le dossier actuel ===
bat_path = os.path.join(os.getcwd(), bat_name)
with open(bat_path, "w", encoding="utf-8") as f:
    f.write(bat_content)
print(f"✅ Fichier {bat_name} créé dans {os.getcwd()}")

# === Chemin vers le bureau (automatique) ===
desktop = winshell.desktop()
shortcut_path = os.path.join(desktop, shortcut_name)

# === Création du raccourci ===
shell = win32com.client.Dispatch("WScript.Shell")
shortcut = shell.CreateShortcut(shortcut_path)
shortcut.TargetPath = bat_path
shortcut.WorkingDirectory = os.getcwd()
shortcut.IconLocation = "cmd.exe"
shortcut.Save()

print(f"✅ Raccourci '{shortcut_name}' créé sur le Bureau.")