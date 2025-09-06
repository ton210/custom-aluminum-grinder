#!/usr/bin/env python3

import os
import time
import requests
from urllib.parse import urljoin, urlparse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import re

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    return webdriver.Chrome(options=chrome_options)

def download_image(url, folder, filename):
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        if not os.path.exists(folder):
            os.makedirs(folder)
        
        filepath = os.path.join(folder, filename)
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print(f"Downloaded: {filename}")
        return filepath
    except Exception as e:
        print(f"Error downloading {url}: {e}")
        return None

def scrape_product_page(url):
    driver = setup_driver()
    
    try:
        print(f"Loading page: {url}")
        driver.get(url)
        
        # Wait for page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Additional wait for dynamic content
        time.sleep(3)
        
        # Create downloads folder
        downloads_folder = "downloaded_content"
        images_folder = os.path.join(downloads_folder, "images")
        
        if not os.path.exists(downloads_folder):
            os.makedirs(downloads_folder)
        
        # Get page HTML
        page_html = driver.page_source
        
        # Save HTML
        with open(os.path.join(downloads_folder, "page.html"), 'w', encoding='utf-8') as f:
            f.write(page_html)
        
        # Find and download images
        images = driver.find_elements(By.TAG_NAME, "img")
        downloaded_images = []
        
        for i, img in enumerate(images):
            src = img.get_attribute("src")
            if src:
                # Convert relative URLs to absolute
                absolute_url = urljoin(url, src)
                
                # Get filename
                parsed_url = urlparse(absolute_url)
                filename = os.path.basename(parsed_url.path)
                if not filename or '.' not in filename:
                    filename = f"image_{i}.jpg"
                
                # Clean filename
                filename = re.sub(r'[^\w\-_\.]', '_', filename)
                
                downloaded_path = download_image(absolute_url, images_folder, filename)
                if downloaded_path:
                    downloaded_images.append({
                        'original_src': src,
                        'absolute_url': absolute_url,
                        'local_path': downloaded_path,
                        'filename': filename,
                        'alt': img.get_attribute("alt") or ""
                    })
        
        # Get product info
        product_info = {}
        
        try:
            title = driver.find_element(By.TAG_NAME, "h1").text
            product_info['title'] = title
        except:
            product_info['title'] = "Custom 4-Piece Aluminum Grinder"
        
        try:
            price_element = driver.find_element(By.CSS_SELECTOR, ".price, .woocommerce-Price-amount")
            product_info['price'] = price_element.text
        except:
            product_info['price'] = ""
        
        try:
            description_element = driver.find_element(By.CSS_SELECTOR, ".product-description, .woocommerce-product-details__short-description")
            product_info['description'] = description_element.text
        except:
            product_info['description'] = ""
        
        return {
            'html': page_html,
            'images': downloaded_images,
            'product_info': product_info,
            'downloads_folder': downloads_folder
        }
        
    finally:
        driver.quit()

if __name__ == "__main__":
    url = "https://munchmakers.com/product/custom-4-piece-aluminum-grinder/"
    result = scrape_product_page(url)
    
    print(f"\nScraping completed!")
    print(f"Downloaded {len(result['images'])} images")
    print(f"Product title: {result['product_info']['title']}")
    print(f"Files saved to: {result['downloads_folder']}")