#!/usr/bin/env python3
import os
import requests
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from urllib.parse import urljoin, urlparse
import json

def setup_driver():
    """Set up Chrome driver with options"""
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    driver = webdriver.Chrome(options=chrome_options)
    return driver

def download_image(url, folder, filename):
    """Download an image from URL to specified folder"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        response = requests.get(url, headers=headers, stream=True)
        response.raise_for_status()
        
        os.makedirs(folder, exist_ok=True)
        filepath = os.path.join(folder, filename)
        
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print(f"Downloaded: {filename}")
        return filepath
    except Exception as e:
        print(f"Error downloading {url}: {e}")
        return None

def scrape_page(url, output_folder):
    """Scrape content and images from a page"""
    driver = setup_driver()
    
    try:
        print(f"Scraping: {url}")
        driver.get(url)
        
        # Wait for page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        time.sleep(3)  # Additional wait for dynamic content
        
        # Get page title and description
        title = driver.title
        
        # Try to find meta description
        description = ""
        try:
            meta_desc = driver.find_element(By.CSS_SELECTOR, 'meta[name="description"]')
            description = meta_desc.get_attribute('content')
        except:
            pass
        
        # Get main content
        page_content = {
            'url': url,
            'title': title,
            'description': description,
            'images': [],
            'products': []
        }
        
        # Find product images
        img_elements = driver.find_elements(By.CSS_SELECTOR, 'img')
        image_folder = os.path.join(output_folder, 'images')
        
        for i, img in enumerate(img_elements):
            try:
                src = img.get_attribute('src')
                alt = img.get_attribute('alt') or f"image_{i}"
                
                if src and ('product' in src.lower() or 'custom' in src.lower() or len(src) > 50):
                    # Get the file extension
                    parsed_url = urlparse(src)
                    path = parsed_url.path
                    ext = os.path.splitext(path)[1] or '.jpg'
                    
                    # Create filename
                    safe_alt = "".join(c for c in alt if c.isalnum() or c in (' ', '-', '_')).rstrip()
                    filename = f"{safe_alt}_{i}{ext}"[:100]  # Limit filename length
                    
                    # Download image
                    filepath = download_image(src, image_folder, filename)
                    if filepath:
                        page_content['images'].append({
                            'src': src,
                            'alt': alt,
                            'local_path': filepath,
                            'filename': filename
                        })
            except Exception as e:
                print(f"Error processing image {i}: {e}")
        
        # Find product information
        try:
            # Look for product cards or containers
            product_elements = driver.find_elements(By.CSS_SELECTOR, '.product, .product-item, .card, [data-product]')
            
            for product in product_elements:
                try:
                    product_data = {}
                    
                    # Get product title
                    title_elem = product.find_elements(By.CSS_SELECTOR, 'h1, h2, h3, h4, .product-title, .title')
                    if title_elem:
                        product_data['title'] = title_elem[0].text.strip()
                    
                    # Get product description
                    desc_elem = product.find_elements(By.CSS_SELECTOR, '.description, .product-description, p')
                    if desc_elem:
                        product_data['description'] = desc_elem[0].text.strip()
                    
                    # Get price
                    price_elem = product.find_elements(By.CSS_SELECTOR, '.price, .product-price, [data-price]')
                    if price_elem:
                        product_data['price'] = price_elem[0].text.strip()
                    
                    if product_data:
                        page_content['products'].append(product_data)
                        
                except Exception as e:
                    print(f"Error processing product: {e}")
                    
        except Exception as e:
            print(f"Error finding products: {e}")
        
        # Get full page HTML
        page_html = driver.page_source
        
        # Save HTML content
        os.makedirs(output_folder, exist_ok=True)
        with open(os.path.join(output_folder, 'page.html'), 'w', encoding='utf-8') as f:
            f.write(page_html)
        
        # Save JSON data
        with open(os.path.join(output_folder, 'content.json'), 'w', encoding='utf-8') as f:
            json.dump(page_content, f, indent=2, ensure_ascii=False)
        
        print(f"Scraped {len(page_content['images'])} images and {len(page_content['products'])} products")
        return page_content
        
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return None
        
    finally:
        driver.quit()

def main():
    urls = [
        'https://munchmakers.com/product-category/custom-rolling-trays/',
        'https://munchmakers.com/product-category/custom-rolling-papers/'
    ]
    
    base_folder = 'scraped_content'
    
    for url in urls:
        # Create folder name from URL
        if 'rolling-trays' in url:
            folder_name = 'rolling_trays'
        elif 'rolling-papers' in url:
            folder_name = 'rolling_papers'
        else:
            folder_name = 'unknown'
        
        output_folder = os.path.join(base_folder, folder_name)
        
        print(f"\n=== Scraping {folder_name.replace('_', ' ').title()} ===")
        scrape_page(url, output_folder)
        
        # Wait between requests
        time.sleep(2)

if __name__ == '__main__':
    main()