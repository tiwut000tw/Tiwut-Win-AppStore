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

# --- Constants and Configuration ---
SETTINGS_FILE = "settings.json"
CACHE_DIR = "cache"
IMAGE_CACHE_DIR = os.path.join(CACHE_DIR, "images")
PLACEHOLDER_ICON = "placeholder.png"

# --- Helper Functions ---
def ensure_dirs():
    os.makedirs(IMAGE_CACHE_DIR, exist_ok=True)

def create_placeholder_image():
    if not os.path.exists(PLACEHOLDER_ICON):
        try:
            Image.new('RGB', (64, 64), color=(200, 200, 200)).save(PLACEHOLDER_ICON)
        except Exception as e:
            print(f"Could not create placeholder image: {e}")

# --- ROBUST PARSER FUNCTIONS ---
def find_header_and_separator(lines):
    header_line, header_index = None, -1
    for i, line in enumerate(lines):
        if line.strip().startswith("---"):
            if i > 0:
                header_line, header_index = lines[i-1], i-1
            break
    return header_line, header_index

def parse_winget_search_output(output):
    results, lines = [], output.strip().split('\n')
    header_line, header_index = find_header_and_separator(lines)
    if not header_line: return []
    try:
        name_pos, id_pos = header_line.index("Name"), header_line.index("Id")
        next_col_pos = header_line.find("Version", id_pos)
        if next_col_pos == -1: next_col_pos = len(header_line)
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
        self.title("Python App Store v6 (Stable)")
        self.geometry("950x750")
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        self.package_managers = self.load_settings()
        ensure_dirs()
        create_placeholder_image()
        self.logo_cache, self.source_checkbox_vars = {}, {}
        
        # Thread pool to limit concurrent logo fetches
        self.thread_pool = ThreadPoolExecutor(max_workers=10)
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        # UI Setup
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.tab_view = ctk.CTkTabview(self)
        self.tab_view.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.tab_view.add("Search & Install")
        self.tab_view.add("Installed Apps")
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
        """Shutdown the thread pool gracefully before closing."""
        self.thread_pool.shutdown(wait=False, cancel_futures=True)
        self.destroy()

    def setup_search_tab(self):
        tab = self.tab_view.tab("Search & Install")
        tab.grid_rowconfigure(2, weight=1)
        tab.grid_columnconfigure(0, weight=1)
        top_frame = ctk.CTkFrame(tab)
        top_frame.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
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
        tab.grid_rowconfigure(1, weight=1)
        tab.grid_columnconfigure(0, weight=1)
        self.refresh_button = ctk.CTkButton(tab, text="Refresh List", command=self.populate_installed_apps_tab)
        self.refresh_button.grid(row=0, column=0, padx=5, pady=10, sticky="w")
        self.installed_apps_frame = ctk.CTkScrollableFrame(tab, label_text="All Installed Applications (Updates are listed first)")
        self.installed_apps_frame.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")

    def load_settings(self):
        try:
            with open(SETTINGS_FILE, 'r') as f: return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            # Default settings WITHOUT -NoExit for proper process handling
            return {"winget": {"search_command": 'powershell -Command "winget search --query \\"{query}\\" --accept-source-agreements"',"install_command": 'powershell -Command "winget install --id \\"{package_id}\\" --accept-source-agreements"',"update_command": 'powershell -Command "winget upgrade --id \\"{package_id}\\" --accept-source-agreements"',"list_command": 'powershell -Command "winget list"',"search_parser": "winget_search", "list_parser": "winget_list"}, "chocolatey": {"search_command": 'powershell -Command "choco search {query} --limit-output --exact"',"install_command": 'powershell -Command "choco install {package_id} -y"',"update_command": 'powershell -Command "choco upgrade {package_id} -y"',"list_command": 'powershell -Command "choco list --local-only"',"search_parser": "choco_search", "list_parser": "choco_list"},"scoop": {"search_command": 'powershell -Command "scoop search {query}"',"install_command": 'powershell -Command "scoop install {package_id}"',"update_command": 'powershell -Command "scoop update {package_id}"',"list_command": 'powershell -Command "scoop list"',"search_parser": "scoop_search", "list_parser": "scoop_list"}}

    def start_task(self, calling_button=None):
        self.progress_bar.grid(row=0, column=0, padx=(200, 5), pady=5, sticky="ew")
        self.progress_bar.start()
        if calling_button: calling_button.configure(state="disabled")

    def stop_task(self, calling_button=None):
        self.progress_bar.stop()
        self.progress_bar.grid_forget()
        if calling_button and calling_button.winfo_exists():
             calling_button.configure(state="normal")

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
        all_results = []
        for name in sources:
            config = self.package_managers.get(name, {})
            if "search_command" not in config: continue
            try:
                command = config["search_command"].format(query=query)
                process = subprocess.run(command, shell=True, capture_output=True, text=True, encoding='utf-8', errors='ignore', startupinfo=self.get_startupinfo())
                if process.returncode == 0:
                    parser = PARSER_MAPPING.get(config.get("search_parser"))
                    if parser:
                        parsed = parser(process.stdout)
                        for res in parsed: res['manager'] = name
                        all_results.extend(parsed)
                else: print(f"Error searching with {name}: {process.stderr or process.stdout}")
            except Exception as e: print(f"Exception with {name}: {e}")
        self.after(0, self.display_search_results, all_results)

    def display_search_results(self, results):
        self.stop_task(self.search_button)
        if not results:
            self.update_status("No applications found.", "orange")
            ctk.CTkLabel(self.search_results_frame, text="No results found.").pack(pady=20); return
        self.update_status(f"Found {len(results)} results.", "green")
        for result in sorted(results, key=lambda x: x['name'].lower()):
            self.create_app_entry(self.search_results_frame, result, "install")

    def populate_installed_apps_tab(self, event=None):
        self.update_status("Fetching all installed apps...")
        self.start_task(self.refresh_button)
        for widget in self.installed_apps_frame.winfo_children(): widget.destroy()
        threading.Thread(target=self.list_installed_worker, daemon=True).start()

    def list_installed_worker(self):
        all_apps = []
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
                        all_apps.extend(parsed)
            except Exception as e: print(f"Exception listing {name}: {e}")
        self.after(0, self.display_installed_apps, all_apps)
        
    def display_installed_apps(self, results):
        self.stop_task(self.refresh_button)
        if not results:
            self.update_status("Could not find any installed apps.", "orange")
            ctk.CTkLabel(self.installed_apps_frame, text="No apps found.").pack(pady=20); return
        sorted_apps = sorted(results, key=lambda x: (not x.get('update_available', False), x['name'].lower()))
        self.update_status(f"Showing {len(results)} installed applications.", "green")
        for app in sorted_apps: self.create_app_entry(self.installed_apps_frame, app, "manage")
            
    def start_install_or_update_thread(self, app_data, action_type, button_widget):
        self.update_status(f"Starting {action_type} for {app_data['name']}...", "yellow")
        self.start_task(button_widget)
        threading.Thread(target=self.install_or_update_worker, args=(app_data, action_type, button_widget), daemon=True).start()

    def install_or_update_worker(self, app_data, action_type, button_widget):
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
                    message = f"No update was found for {name}."
                    success = False # It's not an error, but not a successful update either.
                else:
                    success = True
            else:
                message = output.strip().split('\n')[-1] # Get the last line of error
                print(f"Error during {action_type} of {name}: {output}")
        except Exception as e:
            message = str(e)
            print(f"Exception during {action_type} of {name}: {e}")
        self.after(0, self.on_action_complete, button_widget, name, action_type, success, message)

    def on_action_complete(self, button_widget, app_name, action_type, success, message):
        self.stop_task(button_widget)
        if success:
            self.update_status(f"Successfully completed {action_type} for {app_name}!", "green")
            if self.tab_view.get() == "Installed Apps": self.populate_installed_apps_tab()
        else:
            final_message = message if message else f"Failed to {action_type} {app_name}."
            self.update_status(final_message, "red")

    def create_app_entry(self, parent_frame, app_data, mode):
        frame = ctk.CTkFrame(parent_frame)
        frame.pack(fill="x", padx=5, pady=5)
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
        
        action_button = None
        if mode == "install":
            action_button = ctk.CTkButton(frame, text="Install", width=90)
            action_button.grid(row=0, column=2, rowspan=2, padx=10, pady=5)
            action_button.configure(command=lambda d=app_data, b=action_button: self.start_install_or_update_thread(d, 'install', b))
        elif mode == "manage" and app_data.get('update_available'):
            action_button = ctk.CTkButton(frame, text="Update", width=90, fg_color="#E67E22", hover_color="#D35400")
            action_button.grid(row=0, column=2, rowspan=2, padx=10, pady=5)
            action_button.configure(command=lambda d=app_data, b=action_button: self.start_install_or_update_thread(d, 'update', b))

    def get_startupinfo(self):
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        return startupinfo

    def update_status(self, text, color="white"):
        self.status_label.configure(text=text, text_color=color)

    def fetch_logo_thread(self, app_name, image_label):
        self.thread_pool.submit(self.logo_worker, app_name, image_label)

    def logo_worker(self, app_name, image_label):
        if app_name in self.logo_cache:
            self.update_logo_safely(image_label, self.logo_cache[app_name]); return
        
        img_path = os.path.join(IMAGE_CACHE_DIR, f"{re.sub('[^a-zA-Z0-9]', '', app_name)}.png")
        if os.path.exists(img_path):
            if img := self.load_image_from_path(img_path, app_name):
                self.update_logo_safely(image_label, img); return
        
        try:
            with DDGS() as ddgs:
                results = list(ddgs.images(f"{app_name} logo icon filetype:png", max_results=1))
                if results and (image_url := results[0].get('image')):
                    response = requests.get(image_url, stream=True, timeout=10)
                    response.raise_for_status()
                    with open(img_path, 'wb') as f: f.write(response.content)
                    if img := self.load_image_from_path(img_path, app_name):
                        self.update_logo_safely(image_label, img); return
        except Exception as e:
            # We don't print timeout errors anymore to keep the console clean
            if "time" not in str(e).lower():
                print(f"Could not fetch logo for {app_name}: {e}")

        # Fallback to placeholder
        if "placeholder" not in self.logo_cache: self.load_image_from_path(PLACEHOLDER_ICON, "placeholder")
        if "placeholder" in self.logo_cache:
            self.update_logo_safely(image_label, self.logo_cache["placeholder"])
    
    def update_logo_safely(self, label, image):
        """Schedules the logo update on the main thread only if the label widget still exists."""
        if label.winfo_exists():
            self.after(0, label.configure, {"image": image})

    def load_image_from_path(self, path, cache_key):
        try:
            image = Image.open(path).convert("RGBA")
            image.thumbnail((48, 48), Image.Resampling.LANCZOS)
            ctk_image = ctk.CTkImage(light_image=image, dark_image=image, size=(48, 48))
            self.logo_cache[cache_key] = ctk_image
            return ctk_image
        except Exception as e: print(f"Failed to load image from {path}: {e}"); return None

if __name__ == "__main__":
    app = AppStore()
    app.mainloop()