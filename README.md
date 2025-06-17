**Tiwut Win AppStore**
![Screenshot 2025-06-16 210734](https://github.com/user-attachments/assets/77625bc9-4789-4db0-a4e5-83c7acf7bb5c)
![Screenshot 2025-06-16 210850](https://github.com/user-attachments/assets/f552af85-54d8-441f-b040-e9cbaf4574bb)
v1.1



###
## 🇬🇧 The .exe just needs to be run without any further installation.
## 🇩🇪 Die .exe muss nur ohne weitere Installation ausgeführt werden.
## 🇪🇸 El .exe sólo necesita ejecutarse sin ninguna instalación adicional.
###


======================================================================
               Tiwut Win AppStore - User Manual
======================================================================


----------------------------------------------------------------------
## 🇬🇧 English: User Manual
----------------------------------------------------------------------

1. Introduction
===============
Welcome to the *Tiwut Win AppStore*! This application provides a modern, graphical user interface (GUI) to manage software on your Windows PC. Instead of using the command line, you can now search, install, update, and uninstall applications from popular package managers like *winget*, *Chocolatey*, and *Scoop* with just a few clicks.


2. Prerequisites
================
Before you can use the application, you must ensure the following are installed on your system:

    1. Python: The application is written in Python. Download it from python.org.
       During installation, make sure to check the box that says "Add Python to PATH".

    2. Required Python Libraries: Open PowerShell or Command Prompt and run this command:
       `pip install customtkinter Pillow duckduckgo-search requests packaging`

    3. Package Managers (Recommended): For the best experience, you should have the package managers installed.
        * winget: Usually comes pre-installed with modern Windows 10/11.
        * Chocolatey: Follow the installation guide at chocolatey.org/install
        * Scoop: Follow the installation guide at scoop.sh


3. Running the Application
==========================
    1. Save the final Python code as a file named `TiwutWinAppStore.py`.
    2. Open PowerShell or Command Prompt in the same directory where you saved the file.
    3. Run the application with the command:
       `python TiwutWinAppStore.py`


4. Interface Overview
=====================
The application is divided into two main tabs:
    * Search & Install: Find and install new applications.
    * Installed Apps: View, filter, update, and uninstall the software you already have.
    * Status Bar: At the bottom, a status bar provides feedback on current operations.
    * Progress Bar: The progress bar activates during long tasks like searching, refreshing, or installing.


5. Features
===========

5.1. Search & Install Tab
-------------------------
    * Searching for Apps: Type the name of an application (e.g., `vscode`, `7zip`) into the top search bar and press Enter or click the "Search" button.
    * Selecting Sources: Use the checkboxes (`winget`, `Chocolatey`, `Scoop`) to choose which package managers to include in your search.
    * Installing an App: In the results list, simply click the blue *"Install"* button next to an application. The installation will start, and the progress bar will be active until it's complete.


5.2. Installed Apps Tab
-----------------------
This tab is your central hub for managing existing software.
    * Refreshing the List: Click the *"Refresh List"* button. The app will perform a two-phase check:
        1. A quick scan to find all installed packages.
        2. A deeper verification to confirm which ones truly have updates available.
    * Filtering Your Apps: Use the search bar at the top of this tab to instantly filter the list. The list updates in real-time as you type.
    * Updating an App: If an application has a verified update, a bright orange *"Update"* button will appear next to it. Click it to update that specific application.
    * Uninstalling an App: Every application in the list has a red *"Uninstall"* button. Clicking it will remove the software from your system.
    * Updating All Apps: Click the *"Update All"* button to automatically update all applications that have a verified update available. The apps will be updated one by one to ensure system stability. The list will refresh automatically when the process is complete.


======================================================================
======================================================================


----------------------------------------------------------------------
## 🇩🇪 Deutsch: Benutzerhandbuch
----------------------------------------------------------------------

1. Einleitung
=============
Willkommen im *Tiwut Win AppStore*! Diese Anwendung bietet eine moderne, grafische Benutzeroberfläche (GUI) zur Verwaltung von Software auf Ihrem Windows-PC. Anstatt die Kommandozeile zu verwenden, können Sie nun Anwendungen von beliebten Paketmanagern wie *winget*, *Chocolatey* und *Scoop* mit nur wenigen Klicks suchen, installieren, aktualisieren und deinstallieren.


2. Voraussetzungen
==================
Bevor Sie die Anwendung nutzen können, stellen Sie bitte sicher, dass die folgenden Komponenten auf Ihrem System installiert sind:

    1. Python: Die Anwendung ist in Python geschrieben. Laden Sie es von python.org herunter.
       Achten Sie bei der Installation darauf, die Option "Add Python to PATH" anzukreuzen.

    2. Benötigte Python-Bibliotheken: Öffnen Sie PowerShell oder die Eingabeaufforderung und führen Sie diesen Befehl aus:
       `pip install customtkinter Pillow duckduckgo-search requests packaging`

    3. Paketmanager (Empfohlen): Für die beste Funktionalität sollten die Paketmanager installiert sein.
        * winget: Ist normalerweise auf modernen Windows 10/11-Systemen vorinstalliert.
        * Chocolatey: Folgen Sie der Installationsanleitung auf chocolatey.org/install
        * Scoop: Folgen Sie der Installationsanleitung auf scoop.sh


3. Starten der Anwendung
========================
    1. Speichern Sie den finalen Python-Code in einer Datei mit dem Namen `TiwutWinAppStore.py`.
    2. Öffnen Sie PowerShell oder die Eingabeaufforderung im selben Verzeichnis, in dem Sie die Datei gespeichert haben.
    3. Starten Sie die Anwendung mit dem Befehl:
       `python TiwutWinAppStore.py`


4. Überblick der Benutzeroberfläche
===================================
Die Anwendung ist in zwei Haupt-Registerkarten (Tabs) unterteilt:
    * Suchen & Installieren: Finden und installieren Sie neue Anwendungen.
    * Installierte Apps: Sehen, filtern, aktualisieren und deinstallieren Sie Ihre bereits vorhandene Software.
    * Statusleiste: Eine Leiste am unteren Rand gibt Feedback zu aktuellen Vorgängen.
    * Fortschrittsbalken: Der Fortschrittsbalken wird bei längeren Aktionen wie Suchen, Aktualisieren oder Installieren aktiv.


5. Funktionen
=============

5.1. Registerkarte "Suchen & Installieren"
------------------------------------------
    * Apps suchen: Geben Sie den Namen einer Anwendung (z.B. `vscode`, `7zip`) in die obere Suchleiste ein und drücken Sie die Eingabetaste oder klicken Sie auf die Schaltfläche "Suchen".
    * Quellen auswählen: Nutzen Sie die Kontrollkästchen (`winget`, `Chocolatey`, `Scoop`), um auszuwählen, welche Paketmanager in Ihre Suche einbezogen werden sollen.
    * Eine App installieren: Klicken Sie in der Ergebnisliste einfach auf die blaue *"Installieren"*-Schaltfläche neben einer Anwendung. Die Installation beginnt, und der Fortschrittsbalken ist aktiv, bis sie abgeschlossen ist.


5.2. Registerkarte "Installierte Apps"
--------------------------------------
Diese Registerkarte ist Ihre zentrale Anlaufstelle zur Verwaltung bestehender Software.
    * Liste aktualisieren: Klicken Sie auf die Schaltfläche *"Liste aktualisieren"*. Die App führt eine zweistufige Prüfung durch:
        1. Ein schneller Scan, um alle installierten Pakete zu finden.
        2. Eine tiefere Verifizierung, um zu bestätigen, für welche davon wirklich Updates verfügbar sind.
    * Ihre Apps filtern: Verwenden Sie die Suchleiste oben in dieser Registerkarte, um die Liste sofort zu filtern. Die Liste aktualisiert sich in Echtzeit, während Sie tippen.
    * Eine App aktualisieren: Wenn für eine Anwendung ein verifiziertes Update verfügbar ist, erscheint daneben eine leuchtend orange *"Update"*-Schaltfläche. Klicken Sie darauf, um diese spezifische Anwendung zu aktualisieren.
    * Eine App deinstallieren: Jede Anwendung in der Liste hat eine rote *"Deinstallieren"*-Schaltfläche. Ein Klick darauf entfernt die Software von Ihrem System.
    * Alle Apps aktualisieren: Klicken Sie auf die Schaltfläche *"Alle aktualisieren"*, um automatisch alle Anwendungen zu aktualisieren, für die ein verifiziertes Update verfügbar ist. Die Apps werden nacheinander aktualisiert, um die Systemstabilität zu gewährleisten. Die Liste wird nach Abschluss des Vorgangs automatisch neu geladen.


======================================================================
======================================================================


----------------------------------------------------------------------
## 🇪🇸 Español: Manual de Usuario
----------------------------------------------------------------------

1. Introducción
===============
¡Bienvenido a *Tiwut Win AppStore*! Esta aplicación proporciona una interfaz gráfica de usuario (GUI) moderna para gestionar software en su PC con Windows. En lugar de usar la línea de comandos, ahora puede buscar, instalar, actualizar y desinstalar aplicaciones de gestores de paquetes populares como *winget*, *Chocolatey* y *Scoop* con solo unos pocos clics.


2. Prerrequisitos
=================
Antes de poder usar la aplicación, debe asegurarse de que los siguientes componentes estén instalados en su sistema:

    1. Python: La aplicación está escrita en Python. Descárguelo desde python.org.
       Durante la instalación, asegúrese de marcar la casilla que dice "Add Python to PATH".

    2. Bibliotecas de Python Requeridas: Abra PowerShell o el Símbolo del sistema y ejecute este comando:
       `pip install customtkinter Pillow duckduckgo-search requests packaging`

    3. Gestores de Paquetes (Recomendado): Para la mejor experiencia, debería tener los gestores de paquetes instalados.
        * winget: Generalmente viene preinstalado con las versiones modernas de Windows 10/11.
        * Chocolatey: Siga la guía de instalación en chocolatey.org/install
        * Scoop: Siga la guía de instalación en scoop.sh


3. Ejecutar la Aplicación
=========================
    1. Guarde el código final de Python en un archivo con el nombre `TiwutWinAppStore.py`.
    2. Abra PowerShell o el Símbolo del sistema en el mismo directorio donde guardó el archivo.
    3. Ejecute la aplicación con el comando:
       `python TiwutWinAppStore.py`


4. Resumen de la Interfaz
=========================
La aplicación se divide en dos pestañas principales:
    * Buscar e Instalar: Encuentre e instale nuevas aplicaciones.
    * Aplicaciones Instaladas: Vea, filtre, actualice y desinstale el software que ya tiene.
    * Barra de Estado: En la parte inferior, una barra de estado proporciona información sobre las operaciones actuales.
    * Barra de Progreso: La barra de progreso se activa durante tareas largas como buscar, refrescar o instalar.


5. Características
==================

5.1. Pestaña "Buscar e Instalar"
--------------------------------
    * Buscar Aplicaciones: Escriba el nombre de una aplicación (p. ej., `vscode`, `7zip`) en la barra de búsqueda superior y presione Enter o haga clic en el botón "Buscar".
    * Seleccionar Fuentes: Use las casillas de verificación (`winget`, `Chocolatey`, `Scoop`) para elegir qué gestores de paquetes incluir en su búsqueda.
    * Instalar una Aplicación: En la lista de resultados, simplemente haga clic en el botón azul *"Instalar"* junto a una aplicación. La instalación comenzará y la barra de progreso estará activa hasta que se complete.


5.2. Pestaña "Aplicaciones Instaladas"
--------------------------------------
Esta pestaña es su centro de control para gestionar el software existente.
    * Refrescar la Lista: Haga clic en el botón *"Refrescar Lista"*. La aplicación realizará una verificación en dos fases:
        1. Un escaneo rápido para encontrar todos los paquetes instalados.
        2. Una verificación más profunda para confirmar cuáles de ellos tienen realmente actualizaciones disponibles.
    * Filtrar sus Aplicaciones: Use la barra de búsqueda en la parte superior de esta pestaña para filtrar instantáneamente la lista. La lista se actualiza en tiempo real a medida que escribe.
    * Actualizar una Aplicación: Si una aplicación tiene una actualización verificada, aparecerá un botón naranja brillante de *"Actualizar"* a su lado. Haga clic en él para actualizar esa aplicación específica.
    * Desinstalar una Aplicación: Cada aplicación en la lista tiene un botón rojo de *"Desinstalar"*. Al hacer clic en él, se eliminará el software de su sistema.
    * Actualizar Todo: Haga clic en el botón *"Actualizar Todo"* para actualizar automáticamente todas las aplicaciones que tengan una actualización verificada disponible. Las aplicaciones se actualizarán una por una para garantizar la estabilidad del sistema. La lista se refrescará automáticamente cuando el proceso finalice.