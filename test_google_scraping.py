#!/usr/bin/env python3
"""
Quick test script to verify Google Images scraping functionality
"""

import sys
import time
from real_time_scraper import RealTimeSeatbeltScraper

def test_callback(image, filename, url, hash_val):
    """Test callback function"""
    print(f"✅ Found image: {filename} ({image.width}x{image.height}) - {url[:60]}...")

def main():
    """Test Google Images scraping"""
    print("🧪 Testing Google Images Scraping")
    print("=" * 50)
    
    # Create scraper instance
    scraper = RealTimeSeatbeltScraper()
    scraper.scraping_active = True
    
    # Test search term
    test_term = "person in car backseat"
    print(f"🔍 Searching for: '{test_term}'")
    print("⏳ This may take a few seconds...")
    
    start_time = time.time()
    
    try:
        # Test the scraping
        count = scraper.scrape_google_images(test_term, test_callback, max_images=5)
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"\n📊 Results:")
        print(f"🖼️  Images found: {count}")
        print(f"⏱️  Time taken: {duration:.2f} seconds")
        print(f"🔗 Total unique hashes: {len(scraper.downloaded_hashes)}")
        
        if count > 0:
            print("\n✅ Google Images scraping is working!")
            print("💡 You can now use the real-time scraper with Google Images.")
        else:
            print("\n⚠️  No images found. This might be due to:")
            print("   - Google blocking automated requests")
            print("   - Network issues")
            print("   - Changes in Google's HTML structure")
        
    except Exception as e:
        print(f"\n❌ Error during scraping: {e}")
        print("🔧 Check your internet connection and try again.")
    
    finally:
        scraper.scraping_active = False

if __name__ == "__main__":
    main()