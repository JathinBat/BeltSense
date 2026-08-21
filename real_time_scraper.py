#!/usr/bin/env python3
"""
Real-Time Seatbelt Image Scraper and Annotator
==============================================

Scrapes images and displays them immediately for annotation.
No temporary storage - images are classified as they are downloaded.

Author: AI Assistant  
Date: September 20, 2025
"""

import os
import sys
import json
import time
import hashlib
import requests
import io
import threading
from pathlib import Path
from urllib.parse import urlparse, quote_plus
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import ttk, messagebox
from bs4 import BeautifulSoup
import warnings
warnings.filterwarnings("ignore")

class RealTimeSeatbeltScraper:
    def __init__(self):
        # New folder structure
        self.base_dir = Path("Manually classified")
        self.categories = {
            "wearing_seatbelt": self.base_dir / "Wearing Seatbelt",
            "not_wearing_seatbelt": self.base_dir / "Not Wearing Seatbelt", 
            "unclassified": self.base_dir / "Unclassified",
            "invalid": self.base_dir / "Invalid-Unclear"
        }
        
        # Create directories
        for category_path in self.categories.values():
            category_path.mkdir(parents=True, exist_ok=True)
        
        # Configuration - More seatbelt-specific search terms
        self.search_terms = [
            "person in car backseat",
            "passenger in car wearing seatbelt",
            "person in car without seatbelt", 
            "car passenger safety belt",
            "backseat passenger seatbelt",
            "person sitting in car rear seat",
            "car interior passenger seatbelt",
            "child in car seat",
            "car safety belt",
            "automobile passenger",
            "seatbelt safety car",
            "driver wearing seatbelt",
            "car passenger buckled",
            "automobile safety harness",
            "vehicle occupant seatbelt",
            "car seat safety belt",
            "passenger restraint system",
            "automotive safety belt",
            "car interior safety",
            "vehicle passenger safety",
            "seatbelt compliance car",
            "automobile occupant protection",
            "car passenger secured",
            "vehicle safety restraint",
            "seatbelt usage automobile",
            "car occupant protection",
            "passenger vehicle safety",
            "automobile interior safety",
            "car seat belt system",
            "vehicle passenger restraint"
        ]
        
        self.downloaded_hashes = set()
        self.current_images = []
        self.current_index = 0
        self.scraping_active = False
        self.scraping_thread = None
        
        # Session for downloads
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        
        # Load existing hashes
        self.load_existing_hashes()
        
    def load_existing_hashes(self):
        """Load hashes of already downloaded images to avoid duplicates"""
        hash_file = self.base_dir / "downloaded_hashes.json"
        if hash_file.exists():
            with open(hash_file, 'r') as f:
                self.downloaded_hashes = set(json.load(f))
        
        # Scan existing files
        for category_path in self.categories.values():
            for img_file in category_path.glob("*.jpg"):
                try:
                    with open(img_file, 'rb') as f:
                        file_hash = hashlib.md5(f.read()).hexdigest()
                        self.downloaded_hashes.add(file_hash)
                except:
                    pass
                    
    def save_hashes(self):
        """Save downloaded hashes"""
        hash_file = self.base_dir / "downloaded_hashes.json"
        with open(hash_file, 'w') as f:
            json.dump(list(self.downloaded_hashes), f)
    
    def get_image_hash(self, image_data):
        """Calculate MD5 hash of image data"""
        return hashlib.md5(image_data).hexdigest()
    
    def is_valid_image_url(self, url):
        """Check if URL points to a valid image"""
        if not url or not url.startswith(('http://', 'https://')):
            return False
        
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
        parsed = urlparse(url.lower())
        path = parsed.path
        return any(path.endswith(ext) for ext in image_extensions) or 'image' in url.lower()
    
    def download_and_validate_image(self, url):
        """Download and validate image, return PIL Image object or None"""
        try:
            response = self.session.get(url, timeout=15, stream=True)
            if response.status_code != 200:
                return None
                
            content_type = response.headers.get('Content-Type', '').lower()
            if not content_type.startswith('image/'):
                return None
                
            image_data = response.content
            if len(image_data) < 1000:
                return None
            
            # Check for duplicates
            image_hash = self.get_image_hash(image_data)
            if image_hash in self.downloaded_hashes:
                return None
                
            # Validate and process image
            img = Image.open(io.BytesIO(image_data))
            if img.width < 100 or img.height < 100:
                return None
                
            if img.mode != 'RGB':
                img = img.convert('RGB')
                
            # Add to hash set
            self.downloaded_hashes.add(image_hash)
            
            return img, url, image_hash
                
        except Exception as e:
            print(f"Download error for {url}: {e}")
            return None
    
    def scrape_google_images(self, search_term, callback, max_images=20):
        """Scrape from Google Images and call callback for each image"""
        try:
            import random
            import re
            import json
            
            print(f"🔍 Searching Google Images for: '{search_term}'")
            
            # Use a more direct approach with Google's image search
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Referer': 'https://www.google.com/',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
            
            # Build search URL with different parameters for variety
            safe_search = random.choice(['active', 'off'])
            image_size = random.choice(['l', 'm', 'i'])  # large, medium, icon
            search_url = f"https://www.google.com/search?q={quote_plus(search_term)}&tbm=isch&safe={safe_search}&tbs=isz:{image_size}"
            
            print(f"📡 URL: {search_url}")
            
            # Make request with proper headers
            response = self.session.get(search_url, headers=headers, timeout=20)
            print(f"📊 Response status: {response.status_code}")
            
            if response.status_code != 200:
                print(f"❌ Google search failed with status {response.status_code}")
                # Fallback to a simpler search
                search_url = f"https://www.google.com/search?q={quote_plus(search_term)}&tbm=isch"
                response = self.session.get(search_url, headers=headers, timeout=20)
                if response.status_code != 200:
                    return 0
            
            html_content = response.text
            print(f"📄 Received HTML content: {len(html_content)} characters")
            
            # Multiple methods to extract image URLs
            img_urls = set()
            
            # Method 1: Find JSON data containing image information
            json_pattern = r'"ou":"([^"]+)"'
            json_matches = re.findall(json_pattern, html_content)
            for url in json_matches:
                if self.is_valid_image_url(url):
                    img_urls.add(url)
            
            # Method 2: Find direct image URLs in the HTML
            url_patterns = [
                r'https://[^"\s]+\.(jpg|jpeg|png|gif|webp)',
                r'"(https://[^"]*\.(jpg|jpeg|png|gif|webp))"',
                r'src="([^"]*\.(jpg|jpeg|png|gif|webp))"'
            ]
            
            for pattern in url_patterns:
                matches = re.findall(pattern, html_content, re.IGNORECASE)
                for match in matches:
                    url = match[0] if isinstance(match, tuple) else match
                    if self.is_valid_image_url(url) and 'gstatic' not in url and 'logo' not in url.lower():
                        img_urls.add(url)
            
            # Method 3: Parse with BeautifulSoup as backup
            try:
                soup = BeautifulSoup(html_content, 'html.parser')
                for img in soup.find_all('img'):
                    for attr in ['src', 'data-src', 'data-original']:
                        url = img.get(attr)
                        if url and self.is_valid_image_url(url) and 'gstatic' not in url:
                            img_urls.add(url)
            except Exception as e:
                print(f"⚠️  BeautifulSoup parsing failed: {e}")
            
            # Convert to list and filter
            valid_urls = [url for url in img_urls if self.is_valid_image_url(url)]
            valid_urls = valid_urls[:max_images * 2]  # Get more URLs to account for failures
            
            print(f"🎯 Found {len(valid_urls)} potential image URLs")
            
            if len(valid_urls) == 0:
                print("⚠️  No image URLs found. This might be due to:")
                print("   - Google blocking automated requests")
                print("   - Changes in Google's HTML structure")
                print("   - Network issues")
                return 0
            
            # Download and validate images
            count = 0
            successful_downloads = 0
            
            for i, img_url in enumerate(valid_urls):
                if not self.scraping_active or successful_downloads >= max_images:
                    break
                    
                print(f"📥 Downloading {i+1}/{len(valid_urls)}: {img_url[:60]}...")
                
                try:
                    result = self.download_and_validate_image(img_url)
                    if result:
                        img, url, img_hash = result
                        callback(img, f"{search_term}_{count:03d}", url, img_hash)
                        count += 1
                        successful_downloads += 1
                        print(f"✅ Successfully downloaded image {successful_downloads}")
                        time.sleep(0.5)  # Delay between downloads
                        
                except Exception as e:
                    print(f"❌ Error downloading {img_url}: {e}")
                    continue
                    
            print(f"📊 Downloaded {successful_downloads} valid images for '{search_term}'")
            return successful_downloads
            
        except Exception as e:
            print(f"💥 Google Images scraping error: {e}")
            import traceback
            traceback.print_exc()
            return 0

class RealTimeAnnotator:
    def __init__(self):
        self.scraper = RealTimeSeatbeltScraper()
        self.current_image = None
        self.current_filename = ""
        self.current_url = ""
        self.current_hash = ""
        self.waiting_for_classification = False
        self.image_queue = []
        self.image_processed = False  # Flag to prevent auto-skipping
        self.custom_only_mode = False  # Flag to use only custom search terms
        self.custom_search_terms = []  # Store custom search terms
        
        self.stats = {
            "wearing_seatbelt": 0,
            "not_wearing_seatbelt": 0,
            "unclassified": 0,
            "invalid": 0,
            "total_processed": 0
        }
        
        # Create GUI
        self.root = tk.Tk()
        self.root.title("Real-Time Seatbelt Image Scraper & Annotator")
        self.root.geometry("1200x900")
        self.root.configure(bg='#f0f0f0')
        
        self.create_gui()
        
    def create_gui(self):
        """Create the main GUI"""
        # Main container
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title
        title_label = tk.Label(main_frame, text="🚗 Real-Time Seatbelt Image Scraper & Annotator", 
                              font=("Arial", 16, "bold"), bg='#f0f0f0')
        title_label.grid(row=0, column=0, columnspan=4, pady=10)
        
        # Control panel
        control_frame = ttk.LabelFrame(main_frame, text="Controls", padding="10")
        control_frame.grid(row=1, column=0, columnspan=4, pady=10, sticky=(tk.W, tk.E))
        
        # Start/Stop buttons
        self.start_button = ttk.Button(control_frame, text="🚀 Start Scraping", 
                                      command=self.start_scraping, style="Success.TButton")
        self.start_button.grid(row=0, column=0, padx=5)
        
        self.stop_button = ttk.Button(control_frame, text="⏹️ Stop Scraping", 
                                     command=self.stop_scraping, state="disabled", 
                                     style="Danger.TButton")
        self.stop_button.grid(row=0, column=1, padx=5)
        
        # Status label
        self.status_var = tk.StringVar(value="Ready to start scraping...")
        self.status_label = ttk.Label(control_frame, textvariable=self.status_var)
        self.status_label.grid(row=0, column=2, padx=20)
        
        # Next image button (initially hidden)
        self.next_button = ttk.Button(control_frame, text="➡️ Next Image", 
                                     command=self.manual_next_image, state="disabled")
        self.next_button.grid(row=0, column=3, padx=5)
        
        # Current search term display
        search_info_frame = ttk.LabelFrame(main_frame, text="Search Information", padding="10")
        search_info_frame.grid(row=2, column=0, columnspan=4, pady=5, sticky=(tk.W, tk.E))
        
        # Current search term display
        self.current_search_var = tk.StringVar(value="No search active")
        current_search_label = ttk.Label(search_info_frame, text="Current Search Term:")
        current_search_label.grid(row=0, column=0, padx=(0, 10), sticky=tk.W)
        
        self.current_search_display = ttk.Label(search_info_frame, textvariable=self.current_search_var, 
                                               font=("Arial", 10, "bold"), foreground="blue")
        self.current_search_display.grid(row=0, column=1, sticky=tk.W)
        
        # Custom search term input
        custom_search_label = ttk.Label(search_info_frame, text="Custom Search Term:")
        custom_search_label.grid(row=1, column=0, padx=(0, 10), pady=(10, 0), sticky=tk.W)
        
        self.custom_search_var = tk.StringVar()
        self.custom_search_entry = ttk.Entry(search_info_frame, textvariable=self.custom_search_var, 
                                           width=30, font=("Arial", 10))
        self.custom_search_entry.grid(row=1, column=1, padx=(0, 10), pady=(10, 0), sticky=tk.W)
        
        # Use custom search button
        self.use_custom_btn = ttk.Button(search_info_frame, text="🔍 Use Only This Term", 
                                        command=self.use_custom_search_only, state="normal")
        self.use_custom_btn.grid(row=1, column=2, padx=5, pady=(10, 0))
        
        # Add to search terms button
        self.add_custom_btn = ttk.Button(search_info_frame, text="➕ Add to Search Terms", 
                                        command=self.add_custom_search, state="normal")
        self.add_custom_btn.grid(row=1, column=3, padx=5, pady=(10, 0))
        
        # Back to all terms button
        self.back_to_all_btn = ttk.Button(search_info_frame, text="🔄 Use All Terms", 
                                         command=self.use_all_search_terms, state="disabled")
        self.back_to_all_btn.grid(row=1, column=4, padx=5, pady=(10, 0))
        
        # Image display area
        image_frame = ttk.LabelFrame(main_frame, text="Current Image", padding="10")
        image_frame.grid(row=3, column=0, columnspan=4, pady=10, sticky=(tk.W, tk.E))
        
        self.image_label = ttk.Label(image_frame, text="No image loaded.\nClick 'Start Scraping' to begin.", 
                                    font=("Arial", 12), anchor="center")
        self.image_label.grid(row=0, column=0, columnspan=4, pady=20)
        
        # Classification buttons
        classify_frame = ttk.LabelFrame(main_frame, text="Classify Image", padding="10")
        classify_frame.grid(row=4, column=0, columnspan=4, pady=10, sticky=(tk.W, tk.E))
        
        # Configure button styles
        style = ttk.Style()
        style.configure("Success.TButton", foreground="green")
        style.configure("Danger.TButton", foreground="red") 
        style.configure("Warning.TButton", foreground="orange")
        style.configure("Info.TButton", foreground="blue")
        
        # Buttons with keyboard shortcuts
        self.wearing_btn = ttk.Button(classify_frame, text="✅ WEARING SEATBELT (1)", 
                                     command=lambda: self.classify_image("wearing_seatbelt"),
                                     style="Success.TButton", width=25, state="disabled")
        self.wearing_btn.grid(row=0, column=0, padx=5, pady=5)
        
        self.not_wearing_btn = ttk.Button(classify_frame, text="❌ NOT WEARING SEATBELT (2)", 
                                         command=lambda: self.classify_image("not_wearing_seatbelt"),
                                         style="Danger.TButton", width=25, state="disabled")
        self.not_wearing_btn.grid(row=0, column=1, padx=5, pady=5)
        
        self.unclassified_btn = ttk.Button(classify_frame, text="❓ UNCLASSIFIED (3)", 
                                          command=lambda: self.classify_image("unclassified"),
                                          style="Info.TButton", width=25, state="disabled")
        self.unclassified_btn.grid(row=0, column=2, padx=5, pady=5)
        
        self.invalid_btn = ttk.Button(classify_frame, text="🚫 INVALID/UNCLEAR (4)", 
                                     command=lambda: self.classify_image("invalid"),
                                     style="Warning.TButton", width=25, state="disabled")
        self.invalid_btn.grid(row=0, column=3, padx=5, pady=5)
        
        # Statistics display
        stats_frame = ttk.LabelFrame(main_frame, text="Statistics", padding="10")
        stats_frame.grid(row=5, column=0, columnspan=4, pady=10, sticky=(tk.W, tk.E))
        
        self.stats_var = tk.StringVar()
        self.update_stats_display()
        self.stats_label = ttk.Label(stats_frame, textvariable=self.stats_var, font=("Arial", 11))
        self.stats_label.grid(row=0, column=0)
        
        # Instructions
        instructions = """
        🔹 Click "Start Scraping" to begin downloading images
        🔹 After classifying an image, it will AUTO-ADVANCE to the next if available
        🔹 Keyboard shortcuts: 1=Wearing, 2=Not Wearing, 3=Unclassified, 4=Invalid
        🔹 Use "Next Image" button or Space/Enter to skip without classifying
        🔹 Images are automatically saved to folders as you classify them
        🔹 "Use Only This Term": Search ONLY your custom term (ignores all others)
        🔹 "Add to Search Terms": Add your term to the rotation with existing terms
        🔹 "Use All Terms": Return to using all predefined search terms
        """
        inst_label = ttk.Label(main_frame, text=instructions, font=("Arial", 10), 
                              foreground="gray")
        inst_label.grid(row=6, column=0, columnspan=4, pady=15)
        
        # Keyboard bindings
        self.root.bind('1', lambda e: self.classify_image("wearing_seatbelt"))
        self.root.bind('2', lambda e: self.classify_image("not_wearing_seatbelt"))
        self.root.bind('3', lambda e: self.classify_image("unclassified"))
        self.root.bind('4', lambda e: self.classify_image("invalid"))
        self.root.bind('<space>', lambda e: self.manual_next_image())
        self.root.bind('<Return>', lambda e: self.manual_next_image())
        self.root.bind('<Escape>', lambda e: self.stop_scraping())
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.columnconfigure(2, weight=1)
        main_frame.columnconfigure(3, weight=1)
        
        # Focus to receive keyboard events
        self.root.focus_set()
    
    def update_stats_display(self):
        """Update statistics display"""
        stats_text = (f"✅ Wearing Seatbelt: {self.stats['wearing_seatbelt']}  |  "
                     f"❌ Not Wearing: {self.stats['not_wearing_seatbelt']}  |  "
                     f"❓ Unclassified: {self.stats['unclassified']}  |  "
                     f"🚫 Invalid: {self.stats['invalid']}  |  "
                     f"📊 Total: {self.stats['total_processed']}")
        self.stats_var.set(stats_text)
    
    def use_custom_search_only(self):
        """Use ONLY the custom search term entered by user"""
        custom_term = self.custom_search_var.get().strip()
        if not custom_term:
            messagebox.showwarning("Empty Search Term", "Please enter a search term first.")
            return
        
        # Set to use only custom terms
        self.custom_only_mode = True
        self.custom_search_terms = [custom_term]
        
        # Update display
        self.current_search_var.set(f"Custom Only: {custom_term}")
        
        # Clear the input field
        self.custom_search_var.set("")
        
        # Update button states
        self.back_to_all_btn.config(state="normal")
        
        messagebox.showinfo("Custom Search Only", f"Now using ONLY '{custom_term}' for searches!\nClick 'Use All Terms' to return to all search terms.")
    
    def add_custom_search(self):
        """Add custom search term to the existing terms"""
        custom_term = self.custom_search_var.get().strip()
        if not custom_term:
            messagebox.showwarning("Empty Search Term", "Please enter a search term first.")
            return
        
        # Add custom term to the beginning of search terms list
        if custom_term not in self.scraper.search_terms:
            self.scraper.search_terms.insert(0, custom_term)
        
        # Update display
        self.current_search_var.set(f"Added: {custom_term}")
        
        # Clear the input field
        self.custom_search_var.set("")
        
        messagebox.showinfo("Added to Search Terms", f"Added '{custom_term}' to the search rotation!\nIt will be used along with all other terms.")
    
    def use_all_search_terms(self):
        """Return to using all predefined search terms"""
        self.custom_only_mode = False
        self.custom_search_terms = []
        
        # Update display
        self.current_search_var.set("Using all predefined terms")
        
        # Update button states
        self.back_to_all_btn.config(state="disabled")
        
        messagebox.showinfo("All Search Terms", "Now using all predefined search terms again!")
    
    def start_scraping(self):
        """Start the scraping process"""
        self.scraper.scraping_active = True
        self.waiting_for_classification = False
        self.image_queue = []
        self.start_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        self.next_button.configure(state="disabled")
        self.status_var.set("🔄 Scraping images...")
        
        # Enable classification buttons
        self.wearing_btn.configure(state="disabled")  # Will enable when image is ready
        self.not_wearing_btn.configure(state="disabled")
        self.unclassified_btn.configure(state="disabled")
        self.invalid_btn.configure(state="disabled")
        
        # Start scraping in background thread
        self.scraper.scraping_thread = threading.Thread(target=self.scraping_worker)
        self.scraper.scraping_thread.daemon = True
        self.scraper.scraping_thread.start()
    
    def stop_scraping(self):
        """Stop the scraping process"""
        self.scraper.scraping_active = False
        self.waiting_for_classification = False
        self.start_button.configure(state="normal")
        self.stop_button.configure(state="disabled")
        self.next_button.configure(state="disabled")
        self.status_var.set("⏹️ Scraping stopped")
        
        # Disable classification buttons
        self.wearing_btn.configure(state="disabled")
        self.not_wearing_btn.configure(state="disabled")
        self.unclassified_btn.configure(state="disabled")
        self.invalid_btn.configure(state="disabled")
        
        # Save hashes
        self.scraper.save_hashes()
        
        print(f"Scraping stopped. Total images processed: {self.stats['total_processed']}")
    
    def scraping_worker(self):
        """Background scraping worker - continuous loop"""
        search_round = 1
        
        while self.scraper.scraping_active:
            print(f"\n=== Scraping Round {search_round} ===")
            
            # Choose which search terms to use
            if self.custom_only_mode and self.custom_search_terms:
                search_terms = self.custom_search_terms
                print(f"Using CUSTOM ONLY search terms: {search_terms}")
            else:
                search_terms = self.scraper.search_terms
                print(f"Using ALL predefined search terms ({len(search_terms)} terms)")
            
            for search_term in search_terms:
                if not self.scraper.scraping_active:
                    break
                    
                print(f"Searching Google Images for: {search_term} (Round {search_round})")
                
                # Update UI to show current search term
                mode_text = "CUSTOM ONLY" if self.custom_only_mode else "ALL TERMS"
                self.root.after(0, lambda t=search_term, r=search_round, m=mode_text: [
                    self.status_var.set(f"🔍 Round {r}: Searching Google Images... ({m})"),
                    self.current_search_var.set(f"{t}")
                ])
                
                # Scrape with callback using Google Images
                images_found = self.scraper.scrape_google_images(search_term, self.on_image_found, max_images=15)
                print(f"Found {images_found} new images for '{search_term}'")
                
                if self.scraper.scraping_active:
                    time.sleep(3)  # Longer delay between search terms for Google
            
            # Completed one full round
            if self.scraper.scraping_active:
                search_round += 1
                print(f"Completed round {search_round - 1}, starting round {search_round}")
                time.sleep(5)  # Longer delay between rounds
        
        print("Scraping worker stopped")
    
    def on_image_found(self, pil_image, filename, url, img_hash):
        """Called when a new image is found - add to queue"""
        image_data = {
            'image': pil_image,
            'filename': filename,
            'url': url,
            'hash': img_hash
        }
        
        self.image_queue.append(image_data)
        print(f"Added image to queue: {filename} (Queue size: {len(self.image_queue)})")
        
        # Only load image if we're not currently showing one and waiting for classification
        if not self.waiting_for_classification and not self.current_image:
            self.root.after(0, self.load_next_image)
    
    def load_next_image(self):
        """Load the next image from the queue"""
        # Don't load if we're already waiting for classification
        if self.waiting_for_classification and self.current_image:
            print("Already waiting for classification, not loading next image")
            return
            
        if not self.image_queue:
            if not self.scraper.scraping_active:
                self.status_var.set("✅ Scraping finished - No more images available")
            else:
                self.status_var.set("⏳ Searching for more images...")
                # Check again in 3 seconds if scraping is still active
                self.root.after(3000, self.check_for_more_images)
            return
            
        # Get next image from queue
        image_data = self.image_queue.pop(0)
        
        print(f"Loading image: {image_data['filename']} (Queue remaining: {len(self.image_queue)})")
        
        # Store current image data
        self.current_image = image_data['image']
        self.current_filename = image_data['filename']
        self.current_url = image_data['url']
        self.current_hash = image_data['hash']
        self.waiting_for_classification = True
        self.image_processed = False  # Reset processing flag
        
        # Update UI on main thread
        self.display_current_image()
        
        # Enable classification buttons
        self.wearing_btn.configure(state="normal")
        self.not_wearing_btn.configure(state="normal")
        self.unclassified_btn.configure(state="normal")
        self.invalid_btn.configure(state="normal")
        self.next_button.configure(state="normal")
    
    def check_for_more_images(self):
        """Check if more images are available and load if found"""
        if self.scraper.scraping_active and not self.waiting_for_classification and not self.current_image:
            if self.image_queue:
                print("Found images in queue, loading next")
                self.load_next_image()
            else:
                # Still searching, check again later
                print("Still waiting for more images...")
                self.root.after(3000, self.check_for_more_images)
    
    def display_current_image(self):
        """Display the current image in the UI"""
        if self.current_image:
            try:
                # Resize for display
                img_copy = self.current_image.copy()
                img_copy.thumbnail((600, 400), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img_copy)
                
                self.image_label.configure(image=photo, text="")
                self.image_label.image = photo  # Keep reference
                
                # Update status
                queue_count = len(self.image_queue)
                queue_text = f" ({queue_count} more in queue)" if queue_count > 0 else ""
                self.status_var.set(f"🖼️ Image ready for classification: {self.current_filename}{queue_text}")
                
                # Update window title
                self.root.title(f"Real-Time Annotator - {self.current_filename}")
                
            except Exception as e:
                print(f"Error displaying image: {e}")
                self.status_var.set("❌ Error displaying image")
    
    def classify_image(self, category):
        """Classify current image and save it"""
        if not self.current_image or self.image_processed:
            print("No current image or already processed")
            return
            
        # Mark as processed to prevent double-processing
        self.image_processed = True
        
        try:
            # Generate filename with timestamp
            timestamp = int(time.time())
            filename = f"{category}_{timestamp}_{self.current_filename}.jpg"
            
            # Save to appropriate folder
            folder_path = self.scraper.categories[category]
            file_path = folder_path / filename
            
            self.current_image.save(file_path, 'JPEG', quality=85, optimize=True)
            
            # Update statistics
            self.stats[category] += 1
            self.stats["total_processed"] += 1
            self.update_stats_display()
            
            print(f"Classified: {filename} -> {category}")
            
            # Clear current image and reset state completely
            self.clear_current_image()
            
            self.status_var.set(f"✅ Classified as: {category.replace('_', ' ').title()}")
            
            # Schedule next image load after a brief pause
            self.root.after(800, self.try_load_next_image)
            
        except Exception as e:
            self.image_processed = False  # Reset flag on error
            messagebox.showerror("Error", f"Failed to save image: {e}")
    
    def clear_current_image(self):
        """Clear current image and reset all states"""
        self.current_image = None
        self.current_filename = ""
        self.current_url = ""
        self.current_hash = ""
        self.waiting_for_classification = False
        self.image_processed = False
        
        # Disable all classification buttons
        self.wearing_btn.configure(state="disabled")
        self.not_wearing_btn.configure(state="disabled")
        self.unclassified_btn.configure(state="disabled")
        self.invalid_btn.configure(state="disabled")
        self.next_button.configure(state="disabled")
        
        # Clear image display
        self.image_label.configure(image="", text="Loading next image...")
        self.image_label.image = None
    
    def try_load_next_image(self):
        """Try to load next image only if conditions are right"""
        print(f"Trying to load next image. Queue size: {len(self.image_queue)}, Current image: {self.current_image is not None}, Waiting: {self.waiting_for_classification}")
        
        if not self.current_image and not self.waiting_for_classification:
            if self.image_queue:
                self.load_next_image()
            else:
                # Enable next button for manual control
                self.next_button.configure(state="normal")
                self.image_label.configure(text="Waiting for more images...\nClick 'Next Image' to check for more")
                self.status_var.set("⏳ Waiting for more images...")
        else:
            print("Conditions not met for loading next image")
    
    def manual_next_image(self):
        """Manually advance to next image or check for more images"""
        print("Manual next image requested")
        
        # Clear current state
        self.clear_current_image()
        
        # Try to load next image
        if self.image_queue:
            self.load_next_image()
        else:
            # Check if scraping is still running
            if self.scraper.scraping_active:
                self.image_label.configure(text="Checking for more images...")
                self.status_var.set("🔍 Checking for more images...")
                self.root.after(1000, self.try_load_next_image)  # Try again in 1 second
            else:
                self.image_label.configure(text="No more images available.\nStart scraping to get more images.")
                self.status_var.set("📭 No more images")
    
    def run(self):
        """Start the application"""
        print("🚗 Real-Time Seatbelt Image Scraper & Annotator")
        print("=" * 60)
        print("📁 Images will be saved to: Manually classified/")
        print("🎯 Click 'Start Scraping' to begin!")
        
        self.root.mainloop()

def main():
    """Main function"""
    app = RealTimeAnnotator()
    app.run()

if __name__ == "__main__":
    main()