import customtkinter as ctk
import subprocess
import threading
import json
import os
import re
import requests
from tkinter import messagebox
from PIL import Image
from duckduckgo_search import DDGS
from concurrent.futures import ThreadPoolExecutor
from packaging import version

# --- Constants and Configuration ---
SETTINGS_FILE = "settings.json"
CACHE_DIR = "cache"
IMAGE_CACHE_DIR = os.path.join(CACHE_DIR, "images")
PLACEHOLDER_ICON = "placeholder.png"

# --- Helper Functions & Parsers (Unchanged) ---
def ensure_dirs():
    os.makedirs(IMAGE_CACHE_DIR, exist_ok=True)

def create_placeholder_image():
    if not os.path.exists(PLACEHOLDER_ICON):
        try:
            Image.new('RGB', (64, 64), color=(200, 200, 200)).save(PLACEHOLDER_ICON)
        except Exception as e: print(f"Could not create placeholder image: {e}")

def find_header_and_separator(lines):
    header_line, header_index = None, -1
    for i, line in enumerate(lines):
        if line.strip().startswith("---"):
            if i > 0: header_line, header_index = lines[i-1], i-1
            break
    return header_line, header_index

def parse_winget_search_output(output):
    results, lines = [], output.strip().split('\n')
    header_line, header_index = find_header_and_separator(lines)
    if not header_line: return []
    try:
        name_pos, id_pos = header_line.index("Name"), header_line.index("Id")
        next_col_pos = header_line.find("Version", id_pos); next_col_pos = next_col_pos if next_col_pos != -1 else len(header_line)
    except ValueError: return []
    for line in lines[header_index + 2:]:
        name, package_id = line[name_pos:id_pos].strip(), line[id_pos:next_col_pos].strip()
        if name and package_id: results.append({"name": name, "id": package_id})
    return results

def parse_winget_list_output(output):
    results, lines = [], output.strip().split('\n')
    header_line, header_index = find_header_and_separator(lines)
    if not header_line: return []
    try:
        name_pos, id_pos, version_pos, available_pos = (header_line.index("Name"), header_line.index("Id"), header_line.index("Version"), header_line.index("Available"))
    except ValueError: return []
    for line in lines[header_index + 2:]:
        name, package_id = line[name_pos:id_pos].strip(), line[id_pos:version_pos].strip()
        if name and package_id:
            results.append({"name": name, "id": package_id, "version": line[version_pos:available_pos].strip(), "update_available": bool(line[available_pos:].strip())})
    return results

def parse_winget_show_output(output):
    versions = {}
    for line in output.strip().split('\n'):
        if ":" in line:
            key, value = line.split(":", 1)
            key = key.strip()
            if key == "Version": versions['latest'] = value.strip()
            elif key == "Installed Version": versions['installed'] = value.strip()
    return versions

def parse_choco_search_output(output):
    results = []
    for line in output.strip().split('\n'):
        line = line.strip()
        if line and "packages found" not in line.lower(): results.append({"name": line, "id": line})
    return results
    
def parse_choco_list_output(output):
    results = []
    for line in output.strip().split('\n'):
        parts = line.split()
        if len(parts) == 2: results.append({"name": parts[0].strip(), "id": parts[0].strip(), "version": parts[1].strip(), "update_available": False})
    return results

def parse_scoop_search_output(output):
    results, in_results_section = [], False
    for line in output.strip().split('\n'):
        line = line.strip()
        if not line: continue
        if line.endswith("bucket:"): in_results_section = True; continue
        if in_results_section:
            if not line or not line[0].isalnum(): in_results_section = False; continue
            if parts := line.split(): results.append({"name": parts[0], "id": parts[0]})
    return results

def parse_scoop_list_output(output):
    results = []
    for line in output.strip().split('\n')[2:]:
        if line.strip() and not line.startswith('-'):
            if parts := line.split():
                if len(parts) >= 2: results.append({"name": parts[0], "id": parts[0], "version": parts[1], "update_available": False})
    return results

PARSER_MAPPING = {"winget_search": parse_winget_search_output, "winget_list": parse_winget_list_output, "choco_search": parse_choco_search_output, "choco_list": parse_choco_list_output, "scoop_search": parse_scoop_search_output, "scoop_list": parse_scoop_list_output}

class AppStore(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Tiwut Win AppStore")
        self.geometry("1000x800")
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        self.all_installed_apps = []
        self.package_managers = self.load_settings()
        ensure_dirs()
        create_placeholder_image()
        self.logo_cache, self.source_checkbox_vars = {}, {}
        self.thread_pool = ThreadPoolExecutor(max_workers=10)
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        self.grid_rowconfigure(0, weight=1); self.grid_columnconfigure(0, weight=1)
        self.tab_view = ctk.CTkTabview(self)
        self.tab_view.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.tab_view.add("Search & Install"); self.tab_view.add("Installed Apps")
        self.tab_view.tab("Installed Apps").bind("<Visibility>", lambda e: self.populate_installed_apps_tab())
        
        self.setup_search_tab()
        self.setup_installed_tab()
        
        bottom_frame = ctk.CTkFrame(self, height=50)
        bottom_frame.grid(row=1, column=0, padx=10, pady=10, sticky="ew")
        bottom_frame.grid_columnconfigure(0, weight=1)
        self.status_label = ctk.CTkLabel(bottom_frame, text="Ready.")
        self.status_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.progress_bar = ctk.CTkProgressBar(bottom_frame, mode="indeterminate")

    def on_closing(self):
        self.thread_pool.shutdown(wait=False, cancel_futures=True)
        self.destroy()

    def setup_search_tab(self):
        tab = self.tab_view.tab("Search & Install")
        tab.grid_rowconfigure(2, weight=1); tab.grid_columnconfigure(0, weight=1)
        top_frame = ctk.CTkFrame(tab); top_frame.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        top_frame.grid_columnconfigure(0, weight=1)
        self.search_entry = ctk.CTkEntry(top_frame, placeholder_text="Search for apps...")
        self.search_entry.grid(row=0, column=0, padx=5, pady=10, sticky="ew")
        self.search_entry.bind("<Return>", self.start_search_thread)
        self.search_button = ctk.CTkButton(top_frame, text="Search", width=100, command=self.start_search_thread)
        self.search_button.grid(row=0, column=1, padx=5, pady=10)
        source_frame = ctk.CTkFrame(tab, fg_color="transparent")
        source_frame.grid(row=1, column=0, padx=5, pady=(0, 10), sticky="w")
        ctk.CTkLabel(source_frame, text="Search using:", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=(0, 10))
        for name in self.package_managers:
            var = ctk.BooleanVar(value=True)
            cb = ctk.CTkCheckBox(source_frame, text=name.capitalize(), variable=var)
            cb.pack(side="left", padx=5)
            self.source_checkbox_vars[name] = var
        self.search_results_frame = ctk.CTkScrollableFrame(tab, label_text="Search Results")
        self.search_results_frame.grid(row=2, column=0, padx=5, pady=5, sticky="nsew")

    def setup_installed_tab(self):
        tab = self.tab_view.tab("Installed Apps")
        tab.grid_rowconfigure(1, weight=1); tab.grid_columnconfigure(0, weight=1)
        actions_frame = ctk.CTkFrame(tab, fg_color="transparent")
        actions_frame.grid(row=0, column=0, padx=5, pady=10, sticky="ew")
        self.refresh_button = ctk.CTkButton(actions_frame, text="Refresh List", command=self.populate_installed_apps_tab)
        self.refresh_button.pack(side="left", padx=(0, 10))
        self.update_all_button = ctk.CTkButton(actions_frame, text="Update All", command=self.start_update_all_thread)
        self.update_all_button.pack(side="left")
        self.installed_apps_frame = ctk.CTkScrollableFrame(tab, label_text="All Installed Applications (Updates are listed first)")
        self.installed_apps_frame.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")

    def load_settings(self):
        try:
            with open(SETTINGS_FILE, 'r') as f: return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return { "winget": { "list_command": 'powershell -Command "winget list"', "show_command": 'powershell -Command "winget show --id \\"{package_id}\\""', "search_command": 'powershell -Command "winget search --query \\"{query}\\" --accept-source-agreements"', "install_command": 'powershell -Command "winget install --id \\"{package_id}\\" --accept-source-agreements"', "update_command": 'powershell -Command "winget upgrade --id \\"{package_id}\\" --accept-source-agreements"', "uninstall_command": 'powershell -Command "winget uninstall --id \\"{package_id}\\" --accept-source-agreements"', "search_parser": "winget_search", "list_parser": "winget_list" }, "chocolatey": { "list_command": 'powershell -Command "choco list --local-only"', "search_command": 'powershell -Command "choco search {query} --limit-output --exact"', "install_command": 'powershell -Command "choco install {package_id} -y"', "update_command": 'powershell -Command "choco upgrade {package_id} -y"', "uninstall_command": 'powershell -Command "choco uninstall {package_id} -y"', "search_parser": "choco_search", "list_parser": "choco_list" }, "scoop": { "list_command": 'powershell -Command "scoop list"', "search_command": 'powershell -Command "scoop search {query}"', "install_command": 'powershell -Command "scoop install {package_id}"', "update_command": 'powershell -Command "scoop update {package_id}"', "uninstall_command": 'powershell -Command "scoop uninstall {package_id}"', "search_parser": "scoop_search", "list_parser": "scoop_list" } }
    
    def start_task(self, calling_button=None):
        self.progress_bar.grid(row=0, column=0, padx=(200, 5), pady=5, sticky="ew")
        self.progress_bar.start()
        if calling_button: calling_button.configure(state="disabled")
        if calling_button == self.refresh_button: self.update_all_button.configure(state="disabled")

    def stop_task(self, calling_button=None):
        self.progress_bar.stop()
        self.progress_bar.grid_forget()
        if calling_button and ctk.CTk.winfo_exists(calling_button):
             calling_button.configure(state="normal")
        if calling_button == self.refresh_button and ctk.CTk.winfo_exists(self.update_all_button):
            self.update_all_button.configure(state="normal")

    # --- Search ---
    def start_search_thread(self, event=None):
        query = self.search_entry.get().strip()
        selected_sources = [name for name, var in self.source_checkbox_vars.items() if var.get()]
        if not query: self.update_status("Please enter a search term.", "orange"); return
        if not selected_sources: self.update_status("Please select at least one source.", "orange"); return
        self.update_status(f"Searching for '{query}'...")
        self.start_task(self.search_button)
        for widget in self.search_results_frame.winfo_children(): widget.destroy()
        threading.Thread(target=self.search_worker, args=(query, selected_sources), daemon=True).start()

    def search_worker(self, query, sources):
        # FIX: RESTORED THE LOGIC THAT WAS ACCIDENTALLY DELETED
        all_results = []
        for name in sources:
            config = self.package_managers.get(name, {})
            if "search_command" not in config: continue
            try:
                command = config["search_command"].format(query=query)
                process = subprocess.run(command, shell=True, capture_output=True, text=True, encoding='utf-8', errors='ignore', startupinfo=self.get_startupinfo())
                if process.returncode == 0:
                    parser_name = config.get("search_parser")
                    parser = PARSER_MAPPING.get(parser_name)
                    if parser:
                        parsed = parser(process.stdout)
                        for res in parsed: res['manager'] = name
                        all_results.extend(parsed)
                else: print(f"Error searching with {name}: {process.stderr or process.stdout}")
            except Exception as e: print(f"Exception with {name}: {e}")
        self.after(0, self.display_search_results, all_results)

    def display_search_results(self, results):
        # FIX: RESTORED THE LOGIC THAT WAS ACCIDENTALLY DELETED
        self.stop_task(self.search_button)
        if not results:
            self.update_status("No applications found.", "orange")
            ctk.CTkLabel(self.search_results_frame, text="No results found.").pack(pady=20)
            return
        self.update_status(f"Found {len(results)} results.", "green")
        for result in sorted(results, key=lambda x: x['name'].lower()):
            self.create_app_entry(self.search_results_frame, result, "install")

    # --- Installed Apps ---
    def populate_installed_apps_tab(self):
        self.update_status("Fetching list of installed apps...")
        self.start_task(self.refresh_button)
        for widget in self.installed_apps_frame.winfo_children(): widget.destroy()
        threading.Thread(target=self.list_and_verify_worker, daemon=True).start()

    def list_and_verify_worker(self):
        self.all_installed_apps = []
        for name, config in self.package_managers.items():
            if "list_command" not in config: continue
            try:
                command = config["list_command"]
                process = subprocess.run(command, shell=True, capture_output=True, text=True, encoding='utf-8', errors='ignore', startupinfo=self.get_startupinfo())
                if process.returncode == 0:
                    parser = PARSER_MAPPING.get(config.get("list_parser"))
                    if parser:
                        parsed = parser(process.stdout)
                        for app in parsed: app['manager'] = name
                        self.all_installed_apps.extend(parsed)
            except Exception as e: print(f"Exception listing {name}: {e}")
        
        self.after(0, self.update_status, "Verifying updates...")
        apps_to_verify = [app for app in self.all_installed_apps if app.get('update_available') and app.get('manager') == 'winget']
        with ThreadPoolExecutor(max_workers=8) as executor:
            executor.map(self.check_single_app_update, apps_to_verify)
        
        self.after(0, self.display_installed_apps, self.all_installed_apps)

    def check_single_app_update(self, app):
        config = self.package_managers.get("winget", {})
        if "show_command" not in config: app['update_available'] = False; return
        command = config["show_command"].format(package_id=app['id'])
        try:
            process = subprocess.run(command, shell=True, capture_output=True, text=True, encoding='utf-8', errors='ignore', startupinfo=self.get_startupinfo())
            if process.returncode == 0:
                versions = parse_winget_show_output(process.stdout)
                installed_v, latest_v = versions.get('installed'), versions.get('latest')
                app['update_available'] = bool(installed_v and latest_v and version.parse(latest_v) > version.parse(installed_v))
            else: app['update_available'] = False
        except Exception as e:
            print(f"Could not verify update for {app['name']}: {e}")
            app['update_available'] = False

    def display_installed_apps(self, results):
        self.stop_task(self.refresh_button)
        for widget in self.installed_apps_frame.winfo_children(): widget.destroy()
        if not results:
            self.update_status("Could not find any installed apps.", "orange")
            ctk.CTkLabel(self.installed_apps_frame, text="No apps found.").pack(pady=20); return
        updates_found = sum(1 for app in results if app.get('update_available'))
        self.update_status(f"Showing {len(results)} apps. {updates_found} verified updates found.", "green")
        sorted_apps = sorted(results, key=lambda x: (not x.get('update_available', False), x['name'].lower()))
        for app in sorted_apps: self.create_app_entry(self.installed_apps_frame, app, "manage")
    
    # --- Package Actions ---
    def start_package_action_thread(self, app_data, action_type, button_widget):
        self.update_status(f"Starting {action_type} for {app_data['name']}...", "yellow")
        self.start_task(button_widget)
        threading.Thread(target=self.package_action_worker, args=(app_data, action_type, button_widget), daemon=True).start()

    def package_action_worker(self, app_data, action_type, button_widget):
        package_id, manager, name = app_data['id'], app_data['manager'], app_data['name']
        config = self.package_managers.get(manager)
        command_key, success, message = f"{action_type}_command", False, ""
        if not config or command_key not in config:
            self.after(0, self.on_action_complete, button_widget, name, action_type, False, "Command not configured.")
            return
        command = config[command_key].format(package_id=package_id)
        try:
            process = subprocess.run(command, shell=True, capture_output=True, text=True, encoding='utf-8', errors='ignore')
            output = process.stdout + process.stderr
            if process.returncode == 0:
                if "No applicable upgrade found" in output or "no packages found to upgrade" in output.lower():
                    message, success = f"No update was found for {name}.", False
                else: success = True
            else:
                message = output.strip().split('\n')[-1]
                print(f"Error during {action_type} of {name}: {output}")
        except Exception as e: message = str(e); print(f"Exception during {action_type} of {name}: {e}")
        self.after(0, self.on_action_complete, button_widget, name, action_type, success, message)

    def on_action_complete(self, button_widget, app_name, action_type, success, message):
        self.stop_task(button_widget)
        if success:
            self.update_status(f"Successfully completed {action_type} for {app_name}!", "green")
            if self.tab_view.get() == "Installed Apps": self.populate_installed_apps_tab()
        else:
            self.update_status(message if message else f"Failed to {action_type} {app_name}.", "red")

    def start_update_all_thread(self):
        apps_to_update = [app for app in self.all_installed_apps if app.get('update_available')]
        if not apps_to_update:
            messagebox.showinfo("Update All", "No verified updates available.")
            return
        self.update_status(f"Preparing to update {len(apps_to_update)} applications...")
        self.start_task(self.update_all_button)
        threading.Thread(target=self.update_all_worker, args=(apps_to_update,), daemon=True).start()

    def update_all_worker(self, apps_to_update):
        total = len(apps_to_update)
        for i, app in enumerate(apps_to_update):
            self.after(0, self.update_status, f"Updating {i+1}/{total}: {app['name']}...")
            config = self.package_managers.get(app['manager'])
            command = config["update_command"].format(package_id=app['id'])
            try:
                subprocess.run(command, shell=True, check=True, capture_output=True, text=True, encoding='utf-8', errors='ignore', startupinfo=self.get_startupinfo())
            except subprocess.CalledProcessError as e:
                self.after(0, self.update_status, f"Failed to update {app['name']}. Continuing...", "orange")
                print(f"Update failed for {app['name']}:\n{e.stdout}\n{e.stderr}")
        self.after(0, self.on_update_all_complete)

    def on_update_all_complete(self):
        messagebox.showinfo("Update All", "Update process finished. Refreshing list.")
        self.stop_task(self.update_all_button)
        self.populate_installed_apps_tab()

    def create_app_entry(self, parent_frame, app_data, mode):
        frame = ctk.CTkFrame(parent_frame); frame.pack(fill="x", padx=5, pady=5)
        frame.grid_columnconfigure(1, weight=1)
        logo_label = ctk.CTkLabel(frame, text="", width=48, height=48)
        logo_label.grid(row=0, column=0, rowspan=2, padx=10, pady=5)
        self.fetch_logo_thread(app_data['name'], logo_label)
        info_frame = ctk.CTkFrame(frame, fg_color="transparent")
        info_frame.grid(row=0, column=1, rowspan=2, sticky="w", padx=5)
        name_label = ctk.CTkLabel(info_frame, text=app_data['name'], anchor="w", font=ctk.CTkFont(size=14, weight="bold"))
        name_label.pack(anchor="w")
        id_text = f"ID: {app_data['id']} (via {app_data['manager']})"
        if 'version' in app_data: id_text += f" | v{app_data['version']}"
        id_label = ctk.CTkLabel(info_frame, text=id_text, anchor="w", text_color="gray")
        id_label.pack(anchor="w")
        button_frame = ctk.CTkFrame(frame, fg_color="transparent")
        button_frame.grid(row=0, column=2, rowspan=2, padx=10, pady=5)
        if mode == "install":
            install_btn = ctk.CTkButton(button_frame, text="Install", width=90)
            install_btn.pack()
            install_btn.configure(command=lambda d=app_data, b=install_btn: self.start_package_action_thread(d, 'install', b))
        elif mode == "manage":
            if app_data.get('update_available'):
                update_btn = ctk.CTkButton(button_frame, text="Update", width=90, fg_color="#E67E22", hover_color="#D35400")
                update_btn.pack(side="left", padx=(0, 5))
                update_btn.configure(command=lambda d=app_data, b=update_btn: self.start_package_action_thread(d, 'update', b))
            uninstall_btn = ctk.CTkButton(button_frame, text="Uninstall", width=90, fg_color="#c0392b", hover_color="#e74c3c")
            uninstall_btn.pack(side="left")
            uninstall_btn.configure(command=lambda d=app_data, b=uninstall_btn: self.start_package_action_thread(d, 'uninstall', b))

    def get_startupinfo(self):
        startupinfo = subprocess.STARTUPINFO(); startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        return startupinfo

    def update_status(self, text, color="white"):
        self.status_label.configure(text=text, text_color=color)

    def fetch_logo_thread(self, app_name, image_label):
        self.thread_pool.submit(self.logo_worker, app_name, image_label)

    def logo_worker(self, app_name, image_label):
        if app_name in self.logo_cache: self.update_logo_safely(image_label, self.logo_cache[app_name]); return
        img_path = os.path.join(IMAGE_CACHE_DIR, f"{re.sub('[^a-zA-Z0-9]', '', app_name)}.png")
        if os.path.exists(img_path):
            if img := self.load_image_from_path(img_path, app_name): self.update_logo_safely(image_label, img); return
        try:
            with DDGS() as ddgs:
                results = list(ddgs.images(f"{app_name} logo icon filetype:png", max_results=1))
                if results and (image_url := results[0].get('image')):
                    response = requests.get(image_url, stream=True, timeout=10)
                    response.raise_for_status()
                    with open(img_path, 'wb') as f: f.write(response.content)
                    if img := self.load_image_from_path(img_path, app_name): self.update_logo_safely(image_label, img); return
        except Exception as e:
            if "time" not in str(e).lower(): print(f"Could not fetch logo for {app_name}: {e}")
        if "placeholder" not in self.logo_cache: self.load_image_from_path(PLACEHOLDER_ICON, "placeholder")
        if "placeholder" in self.logo_cache: self.update_logo_safely(image_label, self.logo_cache["placeholder"])
    
    def update_logo_safely(self, label, image):
        if ctk.CTk.winfo_exists(label): self.after(0, label.configure, {"image": image})

    def load_image_from_path(self, path, cache_key):
        try:
            image = Image.open(path).convert("RGBA"); image.thumbnail((48, 48), Image.Resampling.LANCZOS)
            ctk_image = ctk.CTkImage(light_image=image, dark_image=image, size=(48, 48))
            self.logo_cache[cache_key] = ctk_image
            return ctk_image
        except Exception as e: print(f"Failed to load image from {path}: {e}"); return None

if __name__ == "__main__":
    app = AppStore()
    app.mainloop()