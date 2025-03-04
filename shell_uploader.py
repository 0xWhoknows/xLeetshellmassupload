# Author: Who Knows
import requests
import brotli
import logging
import tkinter as tk
from tkinter import scrolledtext, filedialog
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import queue
import time
import json
import os

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class ShellUploader:
    def __init__(self):
        self.url = "https://xleet.su/seller/shells/postmassadd"
        self.source = "hacked"
        self.running = False
        self.result_queue = queue.Queue()
        self.max_retries = 3
        self.retry_delay = 2  # Base delay for exponential backoff
        self.total_shells = 0
        self.shells_left = 0
        self.success_file = "successful_shells.txt"
        self.other_file = "other_shells.txt"
        self.headers_template = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:135.0) Gecko/20100101 Firefox/135.0",
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Referer": "https://xleet.su/seller/shells/massadd",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "X-Requested-With": "XMLHttpRequest",
            "Origin": "https://xleet.su",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "Priority": "u=0",
            "Te": "trailers"
        }
        # Initialize session with connection pool
        self.session = requests.Session()
        adapter = requests.adapters.HTTPAdapter(pool_connections=10, pool_maxsize=10)
        self.session.mount("https://", adapter)

    def set_credentials(self, xsrf_token, session_cookie, csrf_token, shells_file, min_price, max_price):
        """Set dynamic credentials and parameters from GUI inputs."""
        self.cookies = {
            "XSRF-TOKEN": xsrf_token,
            "xleet_session": session_cookie
        }
        self.session.cookies.update(self.cookies)
        self.headers = self.headers_template.copy()
        self.headers["X-Csrf-Token"] = csrf_token
        self.shells_file = shells_file
        self.min_price = float(min_price) if min_price else 5.0
        self.max_price = float(max_price) if max_price else 14.0

    def load_shells(self):
        """Load shell URLs from the selected file."""
        if not self.shells_file:
            return []
        with open(self.shells_file, 'r') as f:
            shells = [line.strip() for line in f if line.strip()]  # Load all shells
            self.total_shells = len(shells)
            self.shells_left = self.total_shells
            return shells

    def generate_price_range(self, num_shells):
        """Generate price range based on min_price and max_price."""
        if self.min_price.is_integer() and self.max_price.is_integer():
            step = 1.0
        else:
            step = 1.0

        price_range = []
        if num_shells == 1:
            price_range = [self.min_price]
        else:
            step_size = (self.max_price - self.min_price) / (num_shells - 1) if num_shells > 1 else 0
            price_range = [self.min_price + i * step_size for i in range(num_shells)]
            price_range = [round(p / step) * step for p in price_range]

        return price_range

    def save_shell(self, shell_url, response_text):
        """Save shell to appropriate file based on response."""
        shell_entry = f"{shell_url}\n"
        if "added successfully" in response_text.lower():
            with open(self.success_file, 'a') as f:
                f.write(shell_entry)
        else:
            with open(self.other_file, 'a') as f:
                f.write(shell_entry)

    def upload_shell(self, shell_url, price):
        """Upload a single shell with retries and improved Brotli handling."""
        attempt = 0
        while attempt < self.max_retries:
            try:
                data = {
                    "shells": shell_url,
                    "source": self.source,
                    "price": str(price)
                }
                response = self.session.post(self.url, headers=self.headers, data=data, timeout=30)
                response.raise_for_status()

                content = response.content
                logging.info(f"Raw response bytes for {shell_url}: {content[:100]}")
                if "Content-Encoding" in response.headers and response.headers["Content-Encoding"] == "br":
                    try:
                        content = brotli.decompress(content)
                        decoded_text = content.decode("utf-8")
                    except brotli.error as e:
                        logging.error(f"Brotli decompression failed for {shell_url}: {e}")
                        try:
                            decoded_text = content.decode("utf-8")
                            logging.info(f"Fallback to UTF-8 decoding succeeded for {shell_url}")
                        except UnicodeDecodeError:
                            decoded_text = f"[Brotli decompression failed: {e}, raw content not UTF-8 decodable]"
                else:
                    decoded_text = response.text

                color = "green" if "added successfully" in decoded_text.lower() else "red" if "failed" in decoded_text.lower() else "white"
                result = f"URL: {shell_url:<50} | Price: {price:>5.1f} | Status: {response.status_code:<3} | Response: {decoded_text}\n{'-'*80}\n"
                logging.info(result)
                self.save_shell(shell_url, decoded_text)
                return (result, color)

            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                attempt += 1
                error_msg = f"Shell: {shell_url} - Attempt {attempt}/{self.max_retries} failed: {e}"
                logging.error(error_msg)
                if attempt == self.max_retries:
                    result = f"URL: {shell_url:<50} | Price: {price:>5.1f} | Failed after {self.max_retries} attempts: {e}\n{'-'*80}\n"
                    self.save_shell(shell_url, result)
                    return (result, "red")
                delay = self.retry_delay * (2 ** (attempt - 1))  # Exponential backoff: 2s, 4s, 8s
                logging.info(f"Retrying after {delay} seconds...")
                time.sleep(delay)
            except requests.exceptions.HTTPError as e:
                attempt += 1
                if e.response.status_code == 419:
                    error_msg = f"Shell: {shell_url} - Attempt {attempt}/{self.max_retries} failed: 419 CSRF Token Mismatch"
                    logging.error(error_msg)
                    if attempt == self.max_retries:
                        result = f"URL: {shell_url:<50} | Price: {price:>5.1f} | Failed after {self.max_retries} attempts: 419 CSRF Token Mismatch (Check X-Csrf-Token and cookies)\n{'-'*80}\n"
                        self.save_shell(shell_url, result)
                        return (result, "red")
                else:
                    error_msg = f"Shell: {shell_url} - Attempt {attempt}/{self.max_retries} failed: {e}"
                    logging.error(error_msg)
                    if attempt == self.max_retries:
                        result = f"URL: {shell_url:<50} | Price: {price:>5.1f} | Failed after {self.max_retries} attempts: {e}\n{'-'*80}\n"
                        self.save_shell(shell_url, result)
                        return (result, "red")
                time.sleep(self.retry_delay)

    def start_upload(self, text_widget, status_label):
        """Start uploading shells concurrently."""
        if self.running or not hasattr(self, 'shells_file'):
            text_widget.insert(tk.END, "Please set all parameters first!\n", "white")
            return
        self.running = True
        text_widget.delete(1.0, tk.END)
        text_widget.insert(tk.END, "Starting upload...\n", "white")

        # Clear output files at the start
        open(self.success_file, 'w').close()
        open(self.other_file, 'w').close()

        shells = self.load_shells()
        if not shells:
            text_widget.insert(tk.END, "No shells found in file!\n", "white")
            self.running = False
            return

        status_label.config(text=f"Loaded {self.total_shells} shells | {self.shells_left} shells left to process")
        prices = self.generate_price_range(len(shells))

        def worker():
            with ThreadPoolExecutor(max_workers=5) as executor:  # Reduced to 5 workers
                futures = {executor.submit(self.upload_shell, shell, price): shell for shell, price in zip(shells, prices)}
                for future in as_completed(futures):
                    if not self.running:
                        break
                    result, color = future.result()
                    self.shells_left -= 1
                    self.result_queue.put((result, color, self.shells_left))

            self.running = False
            self.result_queue.put((f"Upload complete.\n{'-'*80}\n", "white", 0))

        threading.Thread(target=worker, daemon=True).start()
        self.update_gui(text_widget, status_label)

    def stop_upload(self):
        """Stop the upload process."""
        self.running = False

    def update_gui(self, text_widget, status_label):
        """Update the GUI with results and shell count."""
        try:
            while not self.result_queue.empty():
                result, color, shells_left = self.result_queue.get_nowait()
                text_widget.insert(tk.END, result, color)
                status_label.config(text=f"Loaded {self.total_shells} shells | {shells_left} shells left to process")
                text_widget.see(tk.END)
        except queue.Empty:
            pass
        if self.running:
            text_widget.after(100, self.update_gui, text_widget, status_label)

class ShellUploaderGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("xLeet Shell Uploader # Author: Who Knows")
        self.root.configure(bg="black")
        self.uploader = ShellUploader()

        # Load settings from JSON
        self.settings_file = "settings.json"
        self.load_settings()

        # File Selection
        self.file_label = tk.Label(root, text="Shells File: Not selected", bg="black", fg="white")
        self.file_label.pack(pady=2)
        self.file_button = tk.Button(root, text="Select Shells File", command=self.select_file, bg="gray", fg="white")
        self.file_button.pack(pady=2)

        # Price Inputs (on same line)
        price_frame = tk.Frame(root, bg="black")
        price_frame.pack(pady=2)
        tk.Label(price_frame, text="Min Price:", bg="black", fg="white").pack(side=tk.LEFT, padx=5)
        self.min_price_entry = tk.Entry(price_frame, width=10, bg="gray", fg="white")
        self.min_price_entry.pack(side=tk.LEFT, padx=5)
        tk.Label(price_frame, text="Max Price:", bg="black", fg="white").pack(side=tk.LEFT, padx=5)
        self.max_price_entry = tk.Entry(price_frame, width=10, bg="gray", fg="white")
        self.max_price_entry.pack(side=tk.LEFT, padx=5)

        # CSRF Token Input
        tk.Label(root, text="X-Csrf-Token:", bg="black", fg="white").pack(pady=2)
        self.csrf_entry = tk.Entry(root, width=50, bg="gray", fg="white")
        self.csrf_entry.insert(0, self.settings.get("X-Csrf-Token", ""))
        self.csrf_entry.pack(pady=2)

        # Cookies Inputs
        tk.Label(root, text="XSRF-TOKEN:", bg="black", fg="white").pack(pady=2)
        self.xsrf_entry = tk.Entry(root, width=50, bg="gray", fg="white")
        self.xsrf_entry.insert(0, self.settings.get("XSRF-TOKEN", ""))
        self.xsrf_entry.pack(pady=2)
        tk.Label(root, text="xleet_session:", bg="black", fg="white").pack(pady=2)
        self.session_entry = tk.Entry(root, width=50, bg="gray", fg="white")
        self.session_entry.insert(0, self.settings.get("xleet_session", ""))
        self.session_entry.pack(pady=2)

        # Status Label
        self.status_label = tk.Label(root, text="Loaded 0 shells | 0 shells left to process", bg="black", fg="white")
        self.status_label.pack(pady=5)

        # Buttons
        self.start_button = tk.Button(root, text="Start Upload", command=self.start, bg="gray", fg="white")
        self.start_button.pack(pady=5)
        self.stop_button = tk.Button(root, text="Stop Upload", command=self.uploader.stop_upload, bg="gray", fg="white")
        self.stop_button.pack(pady=5)

        # Result Text Area (resizable)
        self.result_text = scrolledtext.ScrolledText(root, width=80, height=20, bg="black", fg="white")
        self.result_text.pack(pady=5, expand=True, fill="both")
        self.result_text.tag_config("green", foreground="green")
        self.result_text.tag_config("red", foreground="red")
        self.result_text.tag_config("white", foreground="white")

    def load_settings(self):
        """Load settings from settings.json."""
        self.settings = {}
        if os.path.exists(self.settings_file):
            with open(self.settings_file, 'r') as f:
                self.settings = json.load(f)

    def save_settings(self):
        """Save settings to settings.json."""
        self.settings["X-Csrf-Token"] = self.csrf_entry.get()
        self.settings["XSRF-TOKEN"] = self.xsrf_entry.get()
        self.settings["xleet_session"] = self.session_entry.get()
        with open(self.settings_file, 'w') as f:
            json.dump(self.settings, f, indent=4)

    def select_file(self):
        """Open file dialog to select a shells file."""
        file_path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
        if file_path:
            self.file_label.config(text=f"Shells File: {file_path}")
            self.shells_file = file_path

    def start(self):
        """Start the upload process with user inputs."""
        xsrf_token = self.xsrf_entry.get()
        session_cookie = self.session_entry.get()
        csrf_token = self.csrf_entry.get()
        min_price = self.min_price_entry.get()
        max_price = self.max_price_entry.get()

        if not all([xsrf_token, session_cookie, csrf_token, hasattr(self, 'shells_file')]):
            self.result_text.insert(tk.END, "Please fill all fields and select a file!\n", "white")
            return

        self.save_settings()
        self.uploader.set_credentials(xsrf_token, session_cookie, csrf_token, self.shells_file, min_price, max_price)
        self.uploader.start_upload(self.result_text, self.status_label)

if __name__ == "__main__":
    root = tk.Tk()
    app = ShellUploaderGUI(root)
    root.mainloop()