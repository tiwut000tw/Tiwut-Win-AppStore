import customtkinter as ctk
import subprocess
import threading
import re
from tkinter import messagebox

# --- Configuration for Package Managers ---
# This dictionary holds the command templates for each package manager.
# It's designed to be easily extensible.
# {query} will be replaced by the search term.
# {package_id} will be replaced by the package's unique ID.
PACKAGE_MANAGERS = {
    "winget": {
        "search_command": 'powershell -Command "winget search --query \\"{query}\\" --accept-source-agreements"',
        "install_command": 'powershell -Command "winget install --id \\"{package_id}\\" --accept-source-agreements --silent"',
        "parser": "parse_winget_output" # The name of the function used to parse the output
    }
    # Example for another manager (you would add this via the UI)
    # "scoop": {
    #     "search_command": 'scoop search "{query}"',
    #     "install_command": 'scoop install "{package_id}"',
    #     "parser": "parse_generic_output"
    # }
}

# --- Parser Functions ---

def parse_winget_output(output):
    """
    Parses the structured output from the 'winget search' command.
    """
    results = []
    lines = output.strip().split('\n')
    
    if len(lines) < 3:
        return []

    # Find the separator line to determine column widths
    separator_line = ""
    header_line_index = -1
    for i, line in enumerate(lines):
        if '---' in line:
            separator_line = line
            header_line_index = i - 1
            break
            
    if not separator_line or header_line_index < 0:
        return []

    header_line = lines[header_line_index]
    
    # Use regex to find the start positions of the headers
    try:
        name_pos = header_line.index("Name")
        id_pos = header_line.index("Id")
        version_pos = header_line.index("Version")
    except ValueError:
        # If headers aren't found, we can't parse
        return []

    # Process each result line
    for line in lines[header_line_index + 2:]: # Skip header and separator
        if not line.strip():
            continue
            
        # Slice the string based on header positions
        # The last column (Version) goes to the end of the line
        name = line[name_pos:id_pos].strip()
        package_id = line[id_pos:version_pos].strip()
        
        if name and package_id:
            results.append({"name": name, "id": package_id})
            
    return results

def parse_generic_output(output):
    """
    A simple parser for other package managers that might just list package names.
    Assumes the first word on each line is the package ID.
    """
    results = []
    lines = output.strip().split('\n')
    for line in lines:
        parts = line.strip().split()
        if parts:
            package_id = parts[0]
            # For this generic parser, we assume the name is the same as the ID
            results.append({"name": package_id, "id": package_id})
    return results

# A dictionary to map parser names from the config to actual functions
PARSER_MAPPING = {
    "parse_winget_output": parse_winget_output,
    "parse_generic_output": parse_generic_output,
}


class AddManagerDialog(ctk.CTkToplevel):
    """A dialog window to add a new package manager."""
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("Add New Package Manager")
        self.geometry("450x300")
        self.transient(parent) # Keep on top of the main window
        self.grab_set() # Modal dialog

        self.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(self, text="Manager Name:").grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.name_entry = ctk.CTkEntry(self, placeholder_text="e.g., scoop")
        self.name_entry.grid(row=0, column=1, padx=10, pady=10, sticky="ew")

        ctk.CTkLabel(self, text="Search Command:").grid(row=1, column=0, padx=10, pady=10, sticky="w")
        self.search_entry = ctk.CTkEntry(self, placeholder_text='e.g., scoop search "{query}"')
        self.search_entry.grid(row=1, column=1, padx=10, pady=10, sticky="ew")

        ctk.CTkLabel(self, text="Install Command:").grid(row=2, column=0, padx=10, pady=10, sticky="w")
        self.install_entry = ctk.CTkEntry(self, placeholder_text='e.g., scoop install "{package_id}"')
        self.install_entry.grid(row=2, column=1, padx=10, pady=10, sticky="ew")
        
        info_label = ctk.CTkLabel(self, text='Use "{query}" for search term and "{package_id}" for install ID.', text_color="gray")
        info_label.grid(row=3, column=0, columnspan=2, padx=10, pady=(0, 10))

        # For this simple implementation, we use a generic parser for new managers.
        self.parser_name = "parse_generic_output"

        save_button = ctk.CTkButton(self, text="Save", command=self.save_manager)
        save_button.grid(row=4, column=0, columnspan=2, padx=10, pady=20)
        
    def save_manager(self):
        name = self.name_entry.get().strip().lower()
        search_cmd = self.search_entry.get().strip()
        install_cmd = self.install_entry.get().strip()

        if not all([name, search_cmd, install_cmd]):
            messagebox.showerror("Error", "All fields are required.")
            return
        
        if "{query}" not in search_cmd:
            messagebox.showerror("Error", "Search command must contain '{query}'.")
            return

        if "{package_id}" not in install_cmd:
            messagebox.showerror("Error", "Install command must contain '{package_id}'.")
            return

        new_manager = {
            "search_command": search_cmd,
            "install_command": install_cmd,
            "parser": self.parser_name
        }
        
        self.parent.add_package_manager(name, new_manager)
        self.destroy()


class AppStore(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Python App Store")
        self.geometry("800x600")
        ctk.set_appearance_mode("System")  # Can be "Light", "Dark", "System"
        ctk.set_default_color_theme("blue")

        # --- Main Layout ---
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # --- Top Frame for Search and Controls ---
        top_frame = ctk.CTkFrame(self, height=50)
        top_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        top_frame.grid_columnconfigure(0, weight=1)

        self.search_entry = ctk.CTkEntry(top_frame, placeholder_text="Search for an application...")
        self.search_entry.grid(row=0, column=0, padx=(10, 5), pady=10, sticky="ew")
        self.search_entry.bind("<Return>", self.start_search_thread) # Allow searching with Enter key

        self.search_button = ctk.CTkButton(top_frame, text="Search", width=100, command=self.start_search_thread)
        self.search_button.grid(row=0, column=1, padx=(5, 10), pady=10)

        # --- Scrollable Frame for Results ---
        self.results_frame = ctk.CTkScrollableFrame(self, label_text="Search Results")
        self.results_frame.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nsew")

        # --- Bottom Frame for Status and Actions ---
        bottom_frame = ctk.CTkFrame(self, height=40)
        bottom_frame.grid(row=2, column=0, padx=10, pady=10, sticky="ew")
        bottom_frame.grid_columnconfigure(0, weight=1)

        self.status_label = ctk.CTkLabel(bottom_frame, text="Ready. Enter a search term to begin.")
        self.status_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")
        
        self.add_manager_button = ctk.CTkButton(bottom_frame, text="Add Package Manager", command=self.open_add_manager_dialog)
        self.add_manager_button.grid(row=0, column=1, padx=10, pady=5, sticky="e")

    def add_package_manager(self, name, config):
        """Callback to add a new manager from the dialog."""
        if name in PACKAGE_MANAGERS:
            messagebox.showwarning("Warning", f"Package manager '{name}' already exists. It will be overwritten.")
        
        PACKAGE_MANAGERS[name] = config
        self.update_status(f"Successfully added/updated package manager: {name}", "green")

    def open_add_manager_dialog(self):
        """Opens the dialog to add a new manager."""
        dialog = AddManagerDialog(self)

    def update_status(self, text, color="white"):
        """Updates the status label text and color."""
        self.status_label.configure(text=text, text_color=color)

    def clear_results(self):
        """Removes all previous search results from the frame."""
        for widget in self.results_frame.winfo_children():
            widget.destroy()

    def start_search_thread(self, event=None):
        """Starts the search process in a new thread to avoid freezing the GUI."""
        query = self.search_entry.get()
        if not query:
            self.update_status("Please enter a search term.", "orange")
            return
        
        self.search_button.configure(state="disabled")
        self.update_status(f"Searching for '{query}'...")
        self.clear_results()

        # Run the actual search in a separate thread
        thread = threading.Thread(target=self.search_worker, args=(query,))
        thread.daemon = True # Allows the app to exit even if the thread is running
        thread.start()

    def search_worker(self, query):
        """The actual search logic that runs in the background."""
        all_results = []
        for manager_name, config in PACKAGE_MANAGERS.items():
            try:
                command = config["search_command"].format(query=query)
                # Using CREATE_NO_WINDOW flag to prevent console windows from popping up
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                
                process = subprocess.run(
                    command, 
                    shell=True, 
                    capture_output=True, 
                    text=True, 
                    encoding='utf-8',
                    errors='ignore',
                    startupinfo=startupinfo
                )
                
                if process.returncode == 0:
                    parser_func = PARSER_MAPPING.get(config["parser"], parse_generic_output)
                    parsed_results = parser_func(process.stdout)
                    for result in parsed_results:
                        result['manager'] = manager_name # Add source manager to the result
                    all_results.extend(parsed_results)
                else:
                    print(f"Error searching with {manager_name}: {process.stderr}")

            except Exception as e:
                print(f"An exception occurred with {manager_name}: {e}")
        
        # Schedule the UI update on the main thread
        self.after(0, self.display_results, all_results)

    def display_results(self, results):
        """Updates the GUI with the search results. Runs on the main thread."""
        self.search_button.configure(state="normal")
        if not results:
            self.update_status("No applications found.", "orange")
            no_results_label = ctk.CTkLabel(self.results_frame, text="No results found.")
            no_results_label.pack(pady=20)
            return

        self.update_status(f"Found {len(results)} results.", "green")

        for result in results:
            result_frame = ctk.CTkFrame(self.results_frame)
            result_frame.pack(fill="x", padx=5, pady=5)
            result_frame.grid_columnconfigure(0, weight=1)

            name_label = ctk.CTkLabel(result_frame, text=result['name'], anchor="w", font=ctk.CTkFont(weight="bold"))
            name_label.grid(row=0, column=0, padx=10, pady=(5,0), sticky="w")
            
            id_label = ctk.CTkLabel(result_frame, text=f"ID: {result['id']} (via {result['manager']})", anchor="w", text_color="gray")
            id_label.grid(row=1, column=0, padx=10, pady=(0,5), sticky="w")

            install_button = ctk.CTkButton(
                result_frame, 
                text="Install", 
                width=80,
                command=lambda r=result: self.start_install_thread(r['id'], r['manager'], r['name'])
            )
            install_button.grid(row=0, column=1, rowspan=2, padx=10, pady=5, sticky="e")

    def start_install_thread(self, package_id, manager_name, package_name):
        """Starts the installation process in a new thread."""
        self.update_status(f"Preparing to install {package_name}...", "yellow")
        
        thread = threading.Thread(target=self.install_worker, args=(package_id, manager_name, package_name))
        thread.daemon = True
        thread.start()
        
    def install_worker(self, package_id, manager_name, package_name):
        """The actual installation logic that runs in the background."""
        self.after(0, self.update_status, f"Installing {package_name} using {manager_name}...", "yellow")
        
        try:
            config = PACKAGE_MANAGERS[manager_name]
            command = config["install_command"].format(package_id=package_id)
            
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

            process = subprocess.run(
                command, 
                shell=True, 
                capture_output=True, 
                text=True, 
                encoding='utf-8', 
                errors='ignore',
                startupinfo=startupinfo
            )
            
            if process.returncode == 0:
                self.after(0, self.update_status, f"Successfully installed {package_name}!", "green")
            else:
                print(f"Install Error for {package_name}: {process.stderr}")
                self.after(0, self.update_status, f"Failed to install {package_name}. Check console for errors.", "red")
                
        except Exception as e:
            print(f"An exception occurred during installation: {e}")
            self.after(0, self.update_status, f"An error occurred while installing {package_name}.", "red")


if __name__ == "__main__":
    app = AppStore()
    app.mainloop()