# Website Cloner Tool v3.1 by FatMatt28 (Anti-Bot Protection)

# ---------------------------------------------------------------------------------
# Required Libraries:
# pip install requests beautifulsoup4 lxml selenium
# ---------------------------------------------------------------------------------

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import requests
from bs4 import BeautifulSoup
import os
import re
from urllib.parse import urljoin, urlparse, unquote
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import webbrowser
import time
import random

# Try to import Selenium for browser mode
SELENIUM_AVAILABLE = False
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options as ChromeOptions
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    SELENIUM_AVAILABLE = True
except ImportError:
    pass


def get_realistic_headers(referer=None):
    """Generate realistic browser headers to bypass bot detection."""
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    ]
    
    headers = {
        "User-Agent": random.choice(user_agents),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Cache-Control": "max-age=0",
        "sec-ch-ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
    }
    
    if referer:
        headers["Referer"] = referer
        headers["Sec-Fetch-Site"] = "same-origin"
    
    return headers


class ModernStyle:
    """Modern dark theme color palette and styling."""
    BG_DARK = "#0f0f1a"
    BG_CARD = "#1a1a2e"
    BG_INPUT = "#252540"
    ACCENT = "#6366f1"
    ACCENT_HOVER = "#818cf8"
    ACCENT_GLOW = "#4f46e5"
    TEXT_PRIMARY = "#ffffff"
    TEXT_SECONDARY = "#94a3b8"
    TEXT_MUTED = "#64748b"
    SUCCESS = "#10b981"
    WARNING = "#f59e0b"
    ERROR = "#ef4444"
    BORDER = "#334155"
    
    @staticmethod
    def configure_styles():
        """Configure ttk styles for modern appearance."""
        style = ttk.Style()
        style.theme_use('clam')
        
        style.configure("Dark.TFrame", background=ModernStyle.BG_DARK)
        style.configure("Card.TFrame", background=ModernStyle.BG_CARD)
        
        style.configure("Title.TLabel", 
                       background=ModernStyle.BG_DARK, 
                       foreground=ModernStyle.TEXT_PRIMARY,
                       font=("Segoe UI", 18, "bold"))
        
        style.configure("Subtitle.TLabel", 
                       background=ModernStyle.BG_DARK, 
                       foreground=ModernStyle.TEXT_SECONDARY,
                       font=("Segoe UI", 10))
        
        style.configure("Card.TLabel", 
                       background=ModernStyle.BG_CARD, 
                       foreground=ModernStyle.TEXT_PRIMARY,
                       font=("Segoe UI", 10))
        
        style.configure("Status.TLabel", 
                       background=ModernStyle.BG_DARK, 
                       foreground=ModernStyle.TEXT_MUTED,
                       font=("Segoe UI", 9))
        
        style.configure("Accent.TButton",
                       background=ModernStyle.ACCENT,
                       foreground=ModernStyle.TEXT_PRIMARY,
                       font=("Segoe UI", 11, "bold"),
                       padding=(20, 12),
                       borderwidth=0)
        style.map("Accent.TButton",
                 background=[("active", ModernStyle.ACCENT_HOVER), ("disabled", ModernStyle.BG_INPUT)])
        
        style.configure("Secondary.TButton",
                       background=ModernStyle.BG_INPUT,
                       foreground=ModernStyle.TEXT_PRIMARY,
                       font=("Segoe UI", 10),
                       padding=(15, 10),
                       borderwidth=0)
        style.map("Secondary.TButton",
                 background=[("active", ModernStyle.BORDER), ("disabled", ModernStyle.BG_DARK)])
        
        style.configure("Custom.Horizontal.TProgressbar",
                       background=ModernStyle.ACCENT,
                       troughcolor=ModernStyle.BG_INPUT,
                       borderwidth=0,
                       lightcolor=ModernStyle.ACCENT,
                       darkcolor=ModernStyle.ACCENT)
        
        return style


class WebsiteCloner:
    def __init__(self, root):
        self.root = root
        self.root.title("Website Cloner v3.1")
        self.root.geometry("720x680")
        self.root.resizable(False, False)
        self.root.configure(bg=ModernStyle.BG_DARK)
        
        ModernStyle.configure_styles()
        
        # State
        self.site_data = {}
        self.css_assets = {}
        self.injected_css = ""  # CSS-in-JS styles captured from browser
        self.is_fetching = False
        self.total_assets = 0
        self.fetched_assets = 0
        self.max_workers = 8
        self.session = None  # Requests session for cookies
        
        self._create_ui()
    
    def _create_ui(self):
        """Creates the modern UI layout."""
        main_frame = ttk.Frame(self.root, style="Dark.TFrame", padding=25)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header
        header_frame = ttk.Frame(main_frame, style="Dark.TFrame")
        header_frame.pack(fill=tk.X, pady=(0, 15))
        
        title_label = ttk.Label(header_frame, text="🌐 Website Cloner", style="Title.TLabel")
        title_label.pack(side=tk.LEFT)
        
        version_label = ttk.Label(header_frame, text="v3.1 (Anti-Bot)", style="Status.TLabel")
        version_label.pack(side=tk.LEFT, padx=(10, 0), pady=(8, 0))
        
        # URL Input Card
        url_card = self._create_card(main_frame, "Enter Website URL")
        
        url_container = tk.Frame(url_card, bg=ModernStyle.BG_INPUT, highlightthickness=1, 
                                 highlightbackground=ModernStyle.BORDER, highlightcolor=ModernStyle.ACCENT)
        url_container.pack(fill=tk.X, pady=(5, 0))
        
        self.url_entry = tk.Entry(url_container, 
                                  font=("Segoe UI", 11),
                                  bg=ModernStyle.BG_INPUT,
                                  fg=ModernStyle.TEXT_PRIMARY,
                                  insertbackground=ModernStyle.TEXT_PRIMARY,
                                  relief=tk.FLAT,
                                  bd=10)
        self.url_entry.pack(fill=tk.X)
        self.url_entry.insert(0, "https://example.com")
        self.url_entry.bind("<FocusIn>", self._on_entry_focus)
        self.url_entry.bind("<FocusOut>", self._on_entry_unfocus)
        self.url_entry.bind("<Return>", lambda e: self.start_fetch_thread())
        
        # Options Card
        options_card = self._create_card(main_frame, "Clone Options")
        
        # Row 1: Concurrent downloads and browser mode
        options_row1 = ttk.Frame(options_card, style="Card.TFrame")
        options_row1.pack(fill=tk.X, pady=5)
        
        tk.Label(options_row1, text="Concurrent Downloads:", 
                bg=ModernStyle.BG_CARD, fg=ModernStyle.TEXT_SECONDARY,
                font=("Segoe UI", 9)).pack(side=tk.LEFT)
        
        self.concurrent_var = tk.IntVar(value=8)
        concurrent_spinbox = tk.Spinbox(options_row1, from_=1, to=16, width=4,
                                        textvariable=self.concurrent_var,
                                        font=("Segoe UI", 10),
                                        bg=ModernStyle.BG_INPUT,
                                        fg=ModernStyle.TEXT_PRIMARY,
                                        buttonbackground=ModernStyle.BG_INPUT,
                                        relief=tk.FLAT, bd=5)
        concurrent_spinbox.pack(side=tk.LEFT, padx=(10, 20))
        
        # Browser mode checkbox (for protected sites)
        self.browser_mode_var = tk.BooleanVar(value=False)
        browser_status = "✓ Available" if SELENIUM_AVAILABLE else "✗ Selenium not installed"
        browser_check = tk.Checkbutton(options_row1, text=f"🔒 Browser Mode ({browser_status})",
                                       variable=self.browser_mode_var,
                                       bg=ModernStyle.BG_CARD,
                                       fg=ModernStyle.SUCCESS if SELENIUM_AVAILABLE else ModernStyle.ERROR,
                                       selectcolor=ModernStyle.BG_INPUT,
                                       activebackground=ModernStyle.BG_CARD,
                                       activeforeground=ModernStyle.TEXT_PRIMARY,
                                       font=("Segoe UI", 9),
                                       state=tk.NORMAL if SELENIUM_AVAILABLE else tk.DISABLED)
        browser_check.pack(side=tk.RIGHT)
        
        # Row 2: Additional options
        options_row2 = ttk.Frame(options_card, style="Card.TFrame")
        options_row2.pack(fill=tk.X, pady=5)
        
        self.inline_styles_var = tk.BooleanVar(value=True)
        inline_check = tk.Checkbutton(options_row2, text="Extract inline style URLs",
                                       variable=self.inline_styles_var,
                                       bg=ModernStyle.BG_CARD,
                                       fg=ModernStyle.TEXT_SECONDARY,
                                       selectcolor=ModernStyle.BG_INPUT,
                                       activebackground=ModernStyle.BG_CARD,
                                       activeforeground=ModernStyle.TEXT_PRIMARY,
                                       font=("Segoe UI", 9))
        inline_check.pack(side=tk.LEFT)
        
        self.wait_js_var = tk.BooleanVar(value=True)
        wait_js_check = tk.Checkbutton(options_row2, text="Wait for JS (Browser mode)",
                                        variable=self.wait_js_var,
                                        bg=ModernStyle.BG_CARD,
                                        fg=ModernStyle.TEXT_SECONDARY,
                                        selectcolor=ModernStyle.BG_INPUT,
                                        activebackground=ModernStyle.BG_CARD,
                                        activeforeground=ModernStyle.TEXT_PRIMARY,
                                        font=("Segoe UI", 9))
        wait_js_check.pack(side=tk.RIGHT)
        
        # Action Buttons
        button_frame = ttk.Frame(main_frame, style="Dark.TFrame")
        button_frame.pack(fill=tk.X, pady=12)
        
        self.go_button = ttk.Button(button_frame, text="⚡ Clone Website", 
                                    command=self.start_fetch_thread, style="Accent.TButton")
        self.go_button.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 8))
        
        self.export_button = ttk.Button(button_frame, text="📁 Export Files", 
                                        command=self.export_files, 
                                        style="Secondary.TButton", state=tk.DISABLED)
        self.export_button.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(8, 8))
        
        self.preview_button = ttk.Button(button_frame, text="👁️ Preview", 
                                         command=self.preview_site,
                                         style="Secondary.TButton", state=tk.DISABLED)
        self.preview_button.pack(side=tk.LEFT, padx=(8, 0))
        
        # Progress Section
        progress_frame = ttk.Frame(main_frame, style="Dark.TFrame")
        progress_frame.pack(fill=tk.X, pady=(5, 8))
        
        self.progress_label = ttk.Label(progress_frame, text="Ready to clone", style="Status.TLabel")
        self.progress_label.pack(side=tk.LEFT)
        
        self.stats_label = ttk.Label(progress_frame, text="", style="Status.TLabel")
        self.stats_label.pack(side=tk.RIGHT)
        
        self.progress_bar = ttk.Progressbar(main_frame, style="Custom.Horizontal.TProgressbar",
                                            mode='determinate', length=400)
        self.progress_bar.pack(fill=tk.X, pady=(0, 8))
        
        # Status Log Card
        log_card = self._create_card(main_frame, "Activity Log", expand=True)
        
        log_container = tk.Frame(log_card, bg=ModernStyle.BG_INPUT)
        log_container.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        
        scrollbar = tk.Scrollbar(log_container, bg=ModernStyle.BG_INPUT, 
                                 troughcolor=ModernStyle.BG_INPUT,
                                 activebackground=ModernStyle.ACCENT)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.status_text = tk.Text(log_container, 
                                   height=10,
                                   wrap=tk.WORD,
                                   font=("Consolas", 9),
                                   bg=ModernStyle.BG_INPUT,
                                   fg=ModernStyle.TEXT_SECONDARY,
                                   insertbackground=ModernStyle.TEXT_PRIMARY,
                                   relief=tk.FLAT,
                                   bd=10,
                                   state=tk.DISABLED,
                                   yscrollcommand=scrollbar.set)
        self.status_text.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.status_text.yview)
        
        self.status_text.tag_configure("success", foreground=ModernStyle.SUCCESS)
        self.status_text.tag_configure("warning", foreground=ModernStyle.WARNING)
        self.status_text.tag_configure("error", foreground=ModernStyle.ERROR)
        self.status_text.tag_configure("info", foreground=ModernStyle.ACCENT)
        self.status_text.tag_configure("muted", foreground=ModernStyle.TEXT_MUTED)
        
        # Footer
        footer = ttk.Label(main_frame, text="Made by FatMatt28 • Enable Browser Mode for protected sites", 
                          style="Status.TLabel")
        footer.pack(pady=(8, 0))
    
    def _create_card(self, parent, title, expand=False):
        """Creates a styled card container."""
        card_outer = tk.Frame(parent, bg=ModernStyle.BG_CARD, 
                             highlightthickness=1, 
                             highlightbackground=ModernStyle.BORDER)
        card_outer.pack(fill=tk.BOTH, expand=expand, pady=6)
        
        card_inner = tk.Frame(card_outer, bg=ModernStyle.BG_CARD, padx=15, pady=10)
        card_inner.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(card_inner, text=title, 
                bg=ModernStyle.BG_CARD, fg=ModernStyle.TEXT_PRIMARY,
                font=("Segoe UI", 11, "bold")).pack(anchor=tk.W)
        
        return card_inner
    
    def _on_entry_focus(self, event):
        if self.url_entry.get() == "https://example.com":
            self.url_entry.delete(0, tk.END)
        event.widget.master.config(highlightbackground=ModernStyle.ACCENT)
    
    def _on_entry_unfocus(self, event):
        if not self.url_entry.get():
            self.url_entry.insert(0, "https://example.com")
        event.widget.master.config(highlightbackground=ModernStyle.BORDER)
    
    def log_status(self, message, tag=None):
        """Thread-safe logging with color support."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        def append_message():
            self.status_text.config(state=tk.NORMAL)
            if tag:
                self.status_text.insert(tk.END, f"[{timestamp}] ", "muted")
                self.status_text.insert(tk.END, message + "\n", tag)
            else:
                self.status_text.insert(tk.END, f"[{timestamp}] {message}\n")
            self.status_text.see(tk.END)
            self.status_text.config(state=tk.DISABLED)
        
        self.root.after(0, append_message)
    
    def update_progress(self, increment=0, text=None):
        """Update progress bar and label."""
        def update():
            if increment:
                self.fetched_assets += increment
                if self.total_assets > 0:
                    progress = (self.fetched_assets / self.total_assets) * 100
                    self.progress_bar['value'] = progress
                    self.stats_label.config(text=f"{self.fetched_assets}/{self.total_assets} assets")
            if text:
                self.progress_label.config(text=text)
        
        self.root.after(0, update)
    
    def sanitize_filename(self, url_path, asset_key, index):
        """Creates a safe, simple filename from a URL path."""
        path = unquote(url_path)
        base_name = os.path.basename(path).split('?')[0].split('#')[0]
        
        if not base_name or base_name == '/':
            ext_map = {'css': '.css', 'js': '.js', 'images': '.jpg', 'fonts': '.woff2', 'favicon': '.ico'}
            ext = ext_map.get(asset_key, '')
            return f"unnamed_{asset_key}_{index}{ext}"
        
        base_name = re.sub(r'[^\w.\-]', '_', base_name)
        return base_name
    
    def fetch_asset(self, url, asset_type='text', retries=3, base_url=None):
        """Fetches a single asset with retry logic and anti-bot headers."""
        headers = get_realistic_headers(referer=base_url)
        
        # Use asset-specific accept headers
        if asset_type == 'binary':
            headers['Accept'] = 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8'
        elif 'css' in url.lower():
            headers['Accept'] = 'text/css,*/*;q=0.1'
        elif 'js' in url.lower():
            headers['Accept'] = '*/*'
        
        # Indicate we can handle compressed content (including Brotli)
        headers['Accept-Encoding'] = 'gzip, deflate, br'
        
        for attempt in range(retries):
            try:
                if self.session:
                    res = self.session.get(url, headers=headers, timeout=15)
                else:
                    res = requests.get(url, headers=headers, timeout=15)
                res.raise_for_status()
                
                # For binary assets, return raw content
                if asset_type == 'binary':
                    return res.content
                
                # For text assets (CSS/JS), try to decode properly
                # First try the encoding from response headers
                encoding = res.encoding or 'utf-8'
                try:
                    # Try with response's detected encoding
                    return res.content.decode(encoding)
                except (UnicodeDecodeError, LookupError):
                    try:
                        # Fallback to UTF-8
                        return res.content.decode('utf-8')
                    except UnicodeDecodeError:
                        try:
                            # Last resort - latin-1 which accepts all bytes
                            return res.content.decode('latin-1')
                        except:
                            # If all else fails, return as text with errors ignored
                            return res.content.decode('utf-8', errors='ignore')
                            
            except requests.exceptions.HTTPError as e:
                status_code = e.response.status_code if e.response else 'Unknown'
                if status_code == 403:
                    self.log_status(f"⚠️ 403 Forbidden - Try Browser Mode: {url[:50]}...", "warning")
                else:
                    self.log_status(f"HTTP {status_code}: {url[:50]}...", "error")
                return None
            except requests.RequestException as e:
                if attempt < retries - 1:
                    time.sleep(0.5 * (attempt + 1))
                    continue
                self.log_status(f"Connection failed: {url[:50]}...", "warning")
        return None
    
    def fetch_with_browser(self, url):
        """Fetch page using Selenium for sites with bot protection and CSS-in-JS."""
        self.log_status("🔒 Using Browser Mode (Selenium)...", "info")
        
        driver = None
        try:
            options = ChromeOptions()
            options.add_argument('--headless=new')
            options.add_argument('--disable-gpu')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_argument('--window-size=1920,1080')
            options.add_experimental_option('excludeSwitches', ['enable-automation'])
            options.add_experimental_option('useAutomationExtension', False)
            options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            
            driver = webdriver.Chrome(options=options)
            driver.execute_cdp_cmd('Network.setUserAgentOverride', {
                "userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            })
            
            self.log_status("Browser launched, navigating...", "info")
            driver.get(url)
            
            # Wait for page to load completely
            if self.wait_js_var.get():
                self.log_status("Waiting for JavaScript & CSS-in-JS to load...", "muted")
                time.sleep(5)  # Wait for JS frameworks to inject styles
                try:
                    WebDriverWait(driver, 15).until(
                        EC.presence_of_element_located((By.TAG_NAME, "body"))
                    )
                    # Additional wait for CSS-in-JS frameworks (styled-components, emotion, etc.)
                    time.sleep(3)
                except:
                    pass
            
            # Use JavaScript to extract ALL CSS from the page
            # This captures dynamically injected styles from styled-components, etc.
            self.log_status("Extracting all CSS from page...", "muted")
            
            all_css_rules = driver.execute_script("""
                let allCSS = [];
                
                // Get CSS from all <style> tags
                const styleTags = document.querySelectorAll('style');
                styleTags.forEach((style, idx) => {
                    if (style.textContent && style.textContent.trim()) {
                        allCSS.push('/* Style Tag ' + (idx + 1) + ' */\\n' + style.textContent);
                    }
                    // Also try to get rules from the stylesheet
                    if (style.sheet) {
                        try {
                            let rules = '';
                            Array.from(style.sheet.cssRules || []).forEach(rule => {
                                rules += rule.cssText + '\\n';
                            });
                            if (rules.trim() && !style.textContent.trim()) {
                                allCSS.push('/* Dynamic Style Tag ' + (idx + 1) + ' */\\n' + rules);
                            }
                        } catch(e) {}
                    }
                });
                
                // Get CSS from all <link rel="stylesheet"> tags
                const linkTags = document.querySelectorAll('link[rel="stylesheet"]');
                linkTags.forEach((link, idx) => {
                    if (link.sheet) {
                        try {
                            let rules = '';
                            Array.from(link.sheet.cssRules || []).forEach(rule => {
                                rules += rule.cssText + '\\n';
                            });
                            if (rules.trim()) {
                                allCSS.push('/* External Stylesheet ' + (idx + 1) + ': ' + link.href + ' */\\n' + rules);
                            }
                        } catch(e) {}
                    }
                });
                
                return allCSS;
            """)
            
            if all_css_rules:
                self.log_status(f"✓ Captured {len(all_css_rules)} CSS sources", "success")
                self.injected_css = "\n\n".join(all_css_rules)
            else:
                # Fallback to original method if JS extraction fails
                style_tags = driver.find_elements(By.TAG_NAME, "style")
                injected_styles = []
                for i, style in enumerate(style_tags):
                    try:
                        css_content = style.get_attribute("innerHTML")
                        if css_content and len(css_content.strip()) > 0:
                            injected_styles.append(f"/* Style Block {i+1} */\n{css_content}")
                    except:
                        pass
                
                if injected_styles:
                    self.log_status(f"✓ Captured {len(injected_styles)} style blocks (fallback)", "success")
                    self.injected_css = "\n\n".join(injected_styles)
                else:
                    self.injected_css = ""
            
            # Get rendered HTML (includes style tags)
            html_content = driver.page_source
            
            # Get cookies from browser session
            cookies = driver.get_cookies()
            
            driver.quit()
            driver = None
            
            # Create session with browser cookies
            self.session = requests.Session()
            for cookie in cookies:
                self.session.cookies.set(cookie['name'], cookie['value'], domain=cookie.get('domain', ''))
            
            self.log_status("✓ Browser fetch successful!", "success")
            return html_content
            
        except Exception as e:
            self.log_status(f"Browser mode failed: {str(e)[:60]}", "error")
            if driver:
                try:
                    driver.quit()
                except:
                    pass
            return None
    
    def extract_and_fetch_css_assets(self, base_url, css_content, css_file_name):
        """Finds url(...) references in CSS content, fetches them, and rewrites the CSS."""
        url_pattern = re.compile(r'url\s*\([\'"]?(?P<url>[^\'")\s]+)[\'"]?\)')
        
        replacements = []
        
        for match in url_pattern.finditer(css_content):
            original_css_url = match.group('url').strip()
            
            if not original_css_url or original_css_url.startswith(('data:', '#', 'mailto:', 'javascript:')):
                continue
            
            full_asset_url = urljoin(base_url, original_css_url)
            
            if full_asset_url in self.css_assets:
                replacements.append((match.group(0), self.css_assets[full_asset_url]['local_path']))
                continue
            
            asset_content = self.fetch_asset(full_asset_url, 'binary', base_url=base_url)
            
            if asset_content:
                path = urlparse(full_asset_url).path
                ext = os.path.splitext(path)[1].lower()
                
                if ext in ['.ttf', '.woff', '.woff2', '.eot', '.svg', '.otf']:
                    asset_key = 'fonts'
                    local_dir = 'fonts'
                else:
                    asset_key = 'images'
                    local_dir = 'images'
                
                index = len([a for a in self.css_assets.values() if a['asset_key'] == asset_key])
                file_name = self.sanitize_filename(path, asset_key, index)
                local_path = f'../{local_dir}/{file_name}'
                
                self.log_status(f"  CSS asset: {file_name}", "info")
                
                self.css_assets[full_asset_url] = {
                    'original_url': original_css_url,
                    'name': file_name,
                    'content': asset_content,
                    'asset_key': asset_key,
                    'local_path': local_path
                }
                
                replacements.append((match.group(0), local_path))
                self.update_progress(increment=1)
        
        modified_css = css_content
        for original, new_path in replacements:
            modified_css = modified_css.replace(original, f"url('{new_path}')")
        
        return modified_css
    
    def extract_inline_style_urls(self, soup, base_url):
        """Extract background-image URLs from inline styles."""
        inline_images = []
        url_pattern = re.compile(r'url\s*\([\'"]?([^\'")\s]+)[\'"]?\)')
        
        for element in soup.find_all(style=True):
            style_content = element.get('style', '')
            for match in url_pattern.finditer(style_content):
                url = match.group(1)
                if url and not url.startswith(('data:', '#')):
                    full_url = urljoin(base_url, url)
                    inline_images.append({
                        'element': element,
                        'original_url': url,
                        'full_url': full_url,
                        'match': match.group(0)
                    })
        
        return inline_images
    
    def start_fetch_thread(self):
        """Initializes and starts the fetching thread."""
        url = self.url_entry.get().strip()
        if not url or url == "https://example.com":
            messagebox.showerror("Error", "Please enter a valid URL.")
            return
        
        if not url.startswith('http'):
            url = 'https://' + url
        
        self.go_button.config(state=tk.DISABLED)
        self.export_button.config(state=tk.DISABLED)
        self.preview_button.config(state=tk.DISABLED)
        
        self.status_text.config(state=tk.NORMAL)
        self.status_text.delete(1.0, tk.END)
        self.status_text.config(state=tk.DISABLED)
        
        self.site_data = {}
        self.css_assets = {}
        self.injected_css = ""
        self.fetched_assets = 0
        self.total_assets = 0
        self.progress_bar['value'] = 0
        self.max_workers = self.concurrent_var.get()
        self.session = None
        
        fetch_thread = threading.Thread(target=self.fetch_website_task, args=(url,), daemon=True)
        fetch_thread.start()
    
    def fetch_website_task(self, url):
        """The main task executed in a separate thread."""
        self.update_progress(text="Connecting...")
        self.log_status(f"Fetching: {url}", "info")
        
        try:
            # Decide fetch method
            if self.browser_mode_var.get() and SELENIUM_AVAILABLE:
                html_content = self.fetch_with_browser(url)
                if not html_content:
                    raise Exception("Browser mode failed to fetch page")
            else:
                # Standard request with anti-bot headers
                headers = get_realistic_headers()
                self.session = requests.Session()
                response = self.session.get(url, headers=headers, timeout=20)
                response.raise_for_status()
                html_content = response.text
            
            self.site_data = {
                'url': url,
                'html': html_content,
                'css': [],
                'js': [],
                'images': [],
                'favicon': []
            }
            soup = BeautifulSoup(html_content, 'html.parser')
            
            self.update_progress(text="Analyzing page...")
            
            css_links = soup.find_all('link', rel='stylesheet', href=True)
            js_scripts = soup.find_all('script', src=True)
            img_tags = soup.find_all('img', src=True)
            favicon_links = soup.find_all('link', rel=lambda x: x and 'icon' in x.lower() if x else False, href=True)
            
            self.total_assets = len(css_links) + len(js_scripts) + len(img_tags) + len(favicon_links)
            self.log_status(f"Found {self.total_assets} assets to download", "success")
            
            assets_to_fetch = []
            
            for idx, element in enumerate(css_links):
                href = element.get('href')
                if href and not href.startswith(('data:', '#')):
                    assets_to_fetch.append({
                        'type': 'css', 'element': element, 'url': href, 'attr': 'href', 'idx': idx
                    })
            
            for idx, element in enumerate(js_scripts):
                src = element.get('src')
                if src and not src.startswith(('data:', '#')):
                    assets_to_fetch.append({
                        'type': 'js', 'element': element, 'url': src, 'attr': 'src', 'idx': idx
                    })
            
            for idx, element in enumerate(img_tags):
                src = element.get('src')
                if src and not src.startswith(('data:', '#')):
                    assets_to_fetch.append({
                        'type': 'images', 'element': element, 'url': src, 'attr': 'src', 'idx': idx
                    })
                    
            for idx, element in enumerate(favicon_links):
                href = element.get('href')
                if href and not href.startswith(('data:', '#')):
                    assets_to_fetch.append({
                        'type': 'favicon', 'element': element, 'url': href, 'attr': 'href', 'idx': idx
                    })
            
            self.update_progress(text="Downloading assets...")
            
            def fetch_single_asset(asset_info):
                asset_type = 'binary' if asset_info['type'] in ['images', 'favicon'] else 'text'
                full_url = urljoin(url, asset_info['url'])
                content = self.fetch_asset(full_url, asset_type, base_url=url)
                
                if content:
                    file_name = self.sanitize_filename(urlparse(full_url).path, 
                                                       asset_info['type'], 
                                                       asset_info['idx'])
                    
                    return {
                        'type': asset_info['type'],
                        'original_url': asset_info['url'],
                        'full_url': full_url,
                        'name': file_name,
                        'content': content
                    }
                return None
            
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                future_to_asset = {executor.submit(fetch_single_asset, asset): asset for asset in assets_to_fetch}
                
                for future in as_completed(future_to_asset):
                    result = future.result()
                    if result:
                        asset_type = result['type']
                        
                        current_names = [a['name'] for a in self.site_data.get(asset_type, [])]
                        if result['name'] in current_names:
                            root_name, ext = os.path.splitext(result['name'])
                            result['name'] = f"{root_name}_{len(current_names)}{ext}"
                        
                        self.log_status(f"✓ {result['name']}", "success")
                        
                        if asset_type == 'css' and isinstance(result['content'], str):
                            self.log_status("  Parsing CSS for embedded assets...", "muted")
                            result['content'] = self.extract_and_fetch_css_assets(
                                result['full_url'], result['content'], result['name']
                            )
                        
                        if asset_type not in self.site_data:
                            self.site_data[asset_type] = []
                        self.site_data[asset_type].append(result)
                    
                    self.update_progress(increment=1)
            
            if self.inline_styles_var.get():
                inline_images = self.extract_inline_style_urls(soup, url)
                if inline_images:
                    self.log_status(f"Found {len(inline_images)} inline style images", "info")
                    for img_info in inline_images:
                        content = self.fetch_asset(img_info['full_url'], 'binary', base_url=url)
                        if content:
                            idx = len(self.site_data.get('images', []))
                            file_name = self.sanitize_filename(
                                urlparse(img_info['full_url']).path, 'images', idx
                            )
                            self.site_data.setdefault('images', []).append({
                                'original_url': img_info['original_url'],
                                'name': file_name,
                                'content': content,
                                'is_inline': True,
                                'element': img_info['element'],
                                'match': img_info['match']
                            })
            
            self.update_progress(text="Clone complete!")
            self.log_status("\n✅ Fetch complete! Ready to export.", "success")
            
            summary = f"Summary: CSS={len(self.site_data.get('css', []))}, "
            summary += f"JS={len(self.site_data.get('js', []))}, "
            summary += f"Images={len(self.site_data.get('images', []))}, "
            summary += f"CSS Assets={len(self.css_assets)}"
            self.log_status(summary, "info")
            
            self.root.after(0, lambda: self.export_button.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.preview_button.config(state=tk.NORMAL))
            
        except requests.exceptions.HTTPError as e:
            self.update_progress(text="Failed!")
            error_msg = str(e)
            if '403' in error_msg:
                self.log_status("❌ 403 Forbidden - Enable 'Browser Mode' for this site!", "error")
            else:
                self.log_status(f"Failed to fetch: {e}", "error")
            self.root.after(0, lambda: messagebox.showerror("Error", f"Could not fetch website.\n{e}\n\nTry enabling 'Browser Mode' for protected sites."))
        except Exception as e:
            self.update_progress(text="Error!")
            self.log_status(f"Unexpected error: {e}", "error")
            self.root.after(0, lambda: messagebox.showerror("Error", f"An error occurred:\n{e}"))
        finally:
            self.root.after(0, lambda: self.go_button.config(state=tk.NORMAL))
    
    def preview_site(self):
        """Preview the cloned HTML in browser."""
        if not self.site_data.get('html'):
            messagebox.showerror("Error", "No site data to preview. Clone a website first.")
            return
        
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
            f.write(self.site_data['html'])
            temp_path = f.name
        
        webbrowser.open(f'file://{temp_path}')
        self.log_status("Opened preview in browser", "info")
    
    def export_files(self):
        """Exports the fetched data to a local directory with robust URL replacement."""
        save_path = filedialog.askdirectory(title="Select Folder to Save Cloned Site")
        if not save_path:
            return
        
        self.log_status(f"\nExporting to: {save_path}", "info")
        self.update_progress(text="Exporting...")
        
        try:
            dir_paths = {
                'css': os.path.join(save_path, 'css'),
                'js': os.path.join(save_path, 'js'),
                'images': os.path.join(save_path, 'images'),
                'fonts': os.path.join(save_path, 'fonts'),
                'favicon': save_path
            }
            
            for path in dir_paths.values():
                os.makedirs(path, exist_ok=True)
            
            # Work with raw HTML string for more reliable replacement
            html_content = self.site_data['html']
            base_url = self.site_data.get('url', '')
            
            # Build a mapping of all URLs to replace
            url_replacements = []  # List of (original_url, full_url, local_path)
            
            asset_export_config = {
                'css': ('w', 'utf-8', 'css'),
                'js': ('w', 'utf-8', 'js'),
                'images': ('wb', None, 'images'),
                'favicon': ('wb', None, '')
            }
            
            for asset_key, (mode, encoding, subdir) in asset_export_config.items():
                for asset_file in self.site_data.get(asset_key, []):
                    file_name = asset_file['name']
                    
                    if asset_key == 'favicon':
                        save_location = os.path.join(dir_paths[asset_key], file_name)
                        relative_path = file_name
                    else:
                        save_location = os.path.join(dir_paths[asset_key], file_name)
                        relative_path = f'{subdir}/{file_name}'
                    
                    content_to_write = asset_file['content']
                    
                    # Write asset file
                    if 'b' in mode:
                        if isinstance(content_to_write, str):
                            content_to_write = content_to_write.encode('utf-8')
                        with open(save_location, 'wb') as f:
                            f.write(content_to_write)
                    else:
                        with open(save_location, 'w', encoding=encoding) as f:
                            f.write(content_to_write)
                    
                    self.log_status(f"  ✓ {file_name}", "success")
                    
                    # Collect URLs for replacement (try both relative and absolute URLs)
                    original_url = asset_file.get('original_url', '')
                    full_url = asset_file.get('full_url', '')
                    
                    if original_url:
                        url_replacements.append((original_url, relative_path))
                    if full_url and full_url != original_url:
                        url_replacements.append((full_url, relative_path))
            
            # Export CSS-embedded assets (fonts and images from CSS)
            for asset_data in self.css_assets.values():
                asset_key = asset_data['asset_key']
                file_name = asset_data['name']
                save_location = os.path.join(dir_paths[asset_key], file_name)
                
                with open(save_location, 'wb') as f:
                    f.write(asset_data['content'])
                self.log_status(f"  ✓ CSS asset: {file_name}", "info")
            
            # Now perform URL replacements in HTML
            # Sort replacements by URL length (longest first) to avoid partial replacements
            url_replacements.sort(key=lambda x: len(x[0]), reverse=True)
            
            self.log_status(f"\n  Updating {len(url_replacements)} URL references...", "muted")
            
            for original_url, local_path in url_replacements:
                if not original_url:
                    continue
                    
                # Escape special regex characters in the URL
                escaped_url = re.escape(original_url)
                
                # Replace in href="..." and src="..." attributes
                # Handle both single and double quotes
                patterns = [
                    (rf'href="{escaped_url}"', f'href="{local_path}"'),
                    (rf"href='{escaped_url}'", f"href='{local_path}'"),
                    (rf'src="{escaped_url}"', f'src="{local_path}"'),
                    (rf"src='{escaped_url}'", f"src='{local_path}'"),
                ]
                
                for pattern, replacement in patterns:
                    html_content = re.sub(pattern, replacement, html_content, flags=re.IGNORECASE)
            
            # Parse and prettify the final HTML
            final_soup = BeautifulSoup(html_content, 'lxml')
            
            # Double-check: Update any remaining asset links using BeautifulSoup
            for asset_key in ['css', 'js', 'images', 'favicon']:
                for asset_file in self.site_data.get(asset_key, []):
                    file_name = asset_file['name']
                    original_url = asset_file.get('original_url', '')
                    full_url = asset_file.get('full_url', '')
                    
                    if asset_key == 'favicon':
                        relative_path = file_name
                    elif asset_key in ['css', 'js', 'images']:
                        relative_path = f'{asset_key}/{file_name}'
                    else:
                        continue
                    
                    # Try to find and update elements
                    if asset_key == 'css':
                        for link in final_soup.find_all('link', rel='stylesheet'):
                            href = link.get('href', '')
                            if href and (href == original_url or href == full_url or href.endswith(file_name)):
                                link['href'] = relative_path
                    elif asset_key == 'js':
                        for script in final_soup.find_all('script', src=True):
                            src = script.get('src', '')
                            if src and (src == original_url or src == full_url or src.endswith(file_name)):
                                script['src'] = relative_path
                    elif asset_key == 'images':
                        for img in final_soup.find_all('img', src=True):
                            src = img.get('src', '')
                            if src and (src == original_url or src == full_url or src.endswith(file_name)):
                                img['src'] = relative_path
                    elif asset_key == 'favicon':
                        for link in final_soup.find_all('link', rel=lambda x: x and 'icon' in str(x).lower()):
                            href = link.get('href', '')
                            if href and (href == original_url or href == full_url):
                                link['href'] = relative_path
            
            # Save injected CSS (CSS-in-JS styles from browser mode)
            if self.injected_css:
                injected_css_path = os.path.join(dir_paths['css'], 'injected_styles.css')
                with open(injected_css_path, 'w', encoding='utf-8') as f:
                    f.write(self.injected_css)
                self.log_status("  ✓ injected_styles.css (CSS-in-JS)", "success")
                
                # Add link to injected CSS in the head
                head = final_soup.find('head')
                if head:
                    new_link = final_soup.new_tag('link', rel='stylesheet', href='css/injected_styles.css')
                    # Insert at the end of head to ensure it overrides other styles
                    head.append(new_link)
                    self.log_status("  → Added link to injected_styles.css in HTML", "muted")
            
            # Save the final HTML
            html_path = os.path.join(save_path, 'index.html')
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(str(final_soup.prettify()))
            self.log_status("  ✓ index.html", "success")
            
            self.update_progress(text="Export complete!")
            self.log_status("\n✅ Export complete!", "success")
            
            if messagebox.askyesno("Success", f"Website cloned successfully!\n\nOpen in browser?"):
                webbrowser.open(f'file://{html_path}')
            
        except Exception as e:
            self.update_progress(text="Export failed!")
            self.log_status(f"Export failed: {e}", "error")
            import traceback
            self.log_status(traceback.format_exc(), "error")
            messagebox.showerror("Export Error", f"An error occurred:\n{e}")


if __name__ == "__main__":
    root = tk.Tk()
    try:
        root.iconbitmap(default='')
    except:
        pass
    
    app = WebsiteCloner(root)
    root.mainloop()