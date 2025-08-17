import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import subprocess
import sys
import os
from pathlib import Path

class CKANToolsUI:
    def __init__(self, root):
        self.root = root
        self.root.title("CKAN Tools - Excel Import & File Monitor")
        self.root.geometry("800x600")
        
        # Get the directory where this script is located
        self.script_dir = Path(__file__).parent
        
        # Create main notebook for tabs
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create tabs
        self.create_excel_import_tab()
        self.create_file_monitor_tab()
        
    def create_excel_import_tab(self):
        """Create tab for Excel import functionality (create_cat.py)"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Excel Import to CKAN")
        
        # Title
        title_label = ttk.Label(frame, text="Import Excel Data to CKAN", font=("Arial", 16, "bold"))
        title_label.pack(pady=10)
        
        # Description
        desc_text = (
            "This tool reads Excel files with schema sheets (dataset, device, digitaltwin, etc.) "
            "and creates or updates CKAN datasets accordingly."
        )
        desc_label = ttk.Label(frame, text=desc_text, wraplength=700, justify=tk.LEFT)
        desc_label.pack(pady=5, padx=20)
        
        # Configuration section
        config_frame = ttk.LabelFrame(frame, text="Configuration", padding=10)
        config_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # Excel file selection
        ttk.Label(config_frame, text="Excel File:").grid(row=0, column=0, sticky=tk.W, pady=5)
        # Set default Excel file path
        default_excel_path = self.script_dir / "SDDI-Metadata.xlsx"
        self.excel_file_var = tk.StringVar(value=str(default_excel_path))
        excel_entry = ttk.Entry(config_frame, textvariable=self.excel_file_var, width=50)
        excel_entry.grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(config_frame, text="Browse", command=self.browse_excel_file).grid(row=0, column=2, padx=5)
        
        # Config file selection
        ttk.Label(config_frame, text="Config File:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.config_file_var = tk.StringVar(value="config.ini")
        config_entry = ttk.Entry(config_frame, textvariable=self.config_file_var, width=50)
        config_entry.grid(row=1, column=1, padx=5, pady=5)
        ttk.Button(config_frame, text="Browse", command=self.browse_config_file).grid(row=1, column=2, padx=5)
        
        # Control buttons
        button_frame = ttk.Frame(frame)
        button_frame.pack(pady=20)
        
        self.import_button = ttk.Button(button_frame, text="Start Import", command=self.run_excel_import)
        self.import_button.pack(side=tk.LEFT, padx=10)
        
        ttk.Button(button_frame, text="Clear Log", command=lambda: self.clear_log(self.import_log)).pack(side=tk.LEFT, padx=10)
        
        # Output log
        log_frame = ttk.LabelFrame(frame, text="Import Log", padding=5)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        self.import_log = scrolledtext.ScrolledText(log_frame, height=15, wrap=tk.WORD)
        self.import_log.pack(fill=tk.BOTH, expand=True)
        
    def create_file_monitor_tab(self):
        """Create tab for file monitoring functionality (detect_outdated_files.py)"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="File Monitor")
        
        # Title
        title_label = ttk.Label(frame, text="CKAN File Monitor", font=("Arial", 16, "bold"))
        title_label.pack(pady=10)
        
        # Description
        desc_text = (
            "This tool monitors local files and compares them with CKAN resources "
            "to detect outdated files that need synchronization."
        )
        desc_label = ttk.Label(frame, text=desc_text, wraplength=700, justify=tk.LEFT)
        desc_label.pack(pady=5, padx=20)
        
        # Configuration section
        config_frame = ttk.LabelFrame(frame, text="Monitor Settings", padding=10)
        config_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # Monitor directory selection
        ttk.Label(config_frame, text="Monitor Directory:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.monitor_dir_var = tk.StringVar()
        monitor_entry = ttk.Entry(config_frame, textvariable=self.monitor_dir_var, width=50)
        monitor_entry.grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(config_frame, text="Browse", command=self.browse_monitor_dir).grid(row=0, column=2, padx=5)
        
        # Debug mode checkbox
        self.debug_var = tk.BooleanVar()
        ttk.Checkbutton(config_frame, text="Enable Debug Mode", variable=self.debug_var).grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        # Control buttons
        button_frame = ttk.Frame(frame)
        button_frame.pack(pady=20)
        
        self.monitor_button = ttk.Button(button_frame, text="Start Monitor", command=self.run_file_monitor)
        self.monitor_button.pack(side=tk.LEFT, padx=10)
        
        ttk.Button(button_frame, text="Clear Log", command=lambda: self.clear_log(self.monitor_log)).pack(side=tk.LEFT, padx=10)
        
        # Output log
        log_frame = ttk.LabelFrame(frame, text="Monitor Log", padding=5)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        self.monitor_log = scrolledtext.ScrolledText(log_frame, height=15, wrap=tk.WORD)
        self.monitor_log.pack(fill=tk.BOTH, expand=True)
        
    def browse_excel_file(self):
        """Browse for Excel file"""
        filename = filedialog.askopenfilename(
            title="Select Excel File",
            filetypes=[("Excel files", "*.xlsx *.xls"), ("All files", "*.*")],
            initialdir=self.script_dir
        )
        if filename:
            self.excel_file_var.set(filename)
            
    def browse_config_file(self):
        """Browse for config file"""
        filename = filedialog.askopenfilename(
            title="Select Config File",
            filetypes=[("INI files", "*.ini"), ("All files", "*.*")],
            initialdir=self.script_dir
        )
        if filename:
            self.config_file_var.set(filename)
            
    def browse_monitor_dir(self):
        """Browse for monitor directory"""
        dirname = filedialog.askdirectory(
            title="Select Directory to Monitor",
            initialdir=self.script_dir
        )
        if dirname:
            self.monitor_dir_var.set(dirname)
            
    def clear_log(self, log_widget):
        """Clear the specified log widget"""
        log_widget.delete(1.0, tk.END)
        
    def log_message(self, log_widget, message):
        """Add message to log widget with Unicode handling"""
        try:
            # Handle Unicode characters properly
            if isinstance(message, bytes):
                message = message.decode('utf-8', errors='replace')
            
            # Remove all non-ASCII characters and replace with spaces
            safe_message = ''.join(char if ord(char) < 128 else ' ' for char in message)
            
            log_widget.insert(tk.END, safe_message + "\n")
            log_widget.see(tk.END)
            self.root.update_idletasks()
        except Exception as e:
            # Fallback: log the error instead of crashing
            fallback_msg = f"[Unicode Error: {str(e)}]"
            log_widget.insert(tk.END, fallback_msg + "\n")
            log_widget.see(tk.END)
            self.root.update_idletasks()
        
    def run_excel_import(self):
        """Run the Excel import tool in a separate thread"""
        if not self.excel_file_var.get():
            messagebox.showerror("Error", "Please select an Excel file")
            return
            
        if not os.path.exists(self.excel_file_var.get()):
            messagebox.showerror("Error", "Excel file does not exist")
            return
            
        # Disable button during execution
        self.import_button.config(state="disabled")
        
        # Run in separate thread to prevent UI freezing
        thread = threading.Thread(target=self._execute_excel_import)
        thread.daemon = True
        thread.start()
        
    def _execute_excel_import(self):
        """Execute the Excel import script"""
        try:
            self.log_message(self.import_log, "Starting Excel import...")
            
            # Set environment variables to force UTF-8 encoding
            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'
            env['PYTHONUTF8'] = '1'
            
            # Execute the script
            script_path = self.script_dir / "create_cat.py"
            result = subprocess.run(
                [sys.executable, str(script_path)],
                cwd=self.script_dir,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                env=env,  # Use modified environment
                timeout=300
            )
            
            # Log output with additional safety
            if result.stdout:
                self.log_message(self.import_log, "STDOUT:")
                for line in result.stdout.splitlines():
                    self.log_message(self.import_log, line)
                
            if result.stderr:
                self.log_message(self.import_log, "STDERR:")
                for line in result.stderr.splitlines():
                    self.log_message(self.import_log, line)
                
            if result.returncode == 0:
                self.log_message(self.import_log, "✅ Excel import completed successfully!")
            else:
                self.log_message(self.import_log, f"❌ Excel import failed with return code: {result.returncode}")
                
        except subprocess.TimeoutExpired:
            self.log_message(self.import_log, "❌ Excel import timed out after 5 minutes")
        except Exception as e:
            self.log_message(self.import_log, f"❌ Error running Excel import: {str(e)}")
        finally:
            # Re-enable button
            self.root.after(0, lambda: self.import_button.config(state="normal"))
            
    def run_file_monitor(self):
        """Run the file monitor tool in a separate thread"""
        # Disable button during execution
        self.monitor_button.config(state="disabled")
        
        # Run in separate thread to prevent UI freezing
        thread = threading.Thread(target=self._execute_file_monitor)
        thread.daemon = True
        thread.start()
        
    def _execute_file_monitor(self):
        """Execute the file monitor script"""
        try:
            self.log_message(self.monitor_log, "Starting file monitor...")
            
            # Prepare command arguments
            script_path = self.script_dir / "detect_outdated_files.py"
            cmd = [sys.executable, str(script_path)]
            
            if self.debug_var.get():
                cmd.append("--debug")
            
            # Set environment variables to force UTF-8 encoding
            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'
            env['PYTHONUTF8'] = '1'
                
            # Execute the script with proper encoding handling
            result = subprocess.run(
                cmd,
                cwd=self.script_dir,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                env=env,  # Use modified environment
                timeout=300
            )
            
            # Log output with additional safety
            if result.stdout:
                self.log_message(self.monitor_log, "STDOUT:")
                # Split output into lines and process each separately
                for line in result.stdout.splitlines():
                    self.log_message(self.monitor_log, line)
                
            if result.stderr:
                self.log_message(self.monitor_log, "STDERR:")
                # Split stderr into lines and process each separately
                for line in result.stderr.splitlines():
                    self.log_message(self.monitor_log, line)
                
            if result.returncode == 0:
                self.log_message(self.monitor_log, "✅ File monitoring completed successfully!")
            else:
                self.log_message(self.monitor_log, f"❌ File monitoring failed with return code: {result.returncode}")
                
        except subprocess.TimeoutExpired:
            self.log_message(self.monitor_log, "❌ File monitoring timed out after 5 minutes")
        except Exception as e:
            self.log_message(self.monitor_log, f"❌ Error running file monitor: {str(e)}")
        finally:
            # Re-enable button
            self.root.after(0, lambda: self.monitor_button.config(state="normal"))

def main():
    root = tk.Tk()
    app = CKANToolsUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()