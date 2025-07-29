from playwright.sync_api import sync_playwright
import pandas as pd
from multiprocessing import Pool, cpu_count, Manager
import time
import json
from io import BytesIO

BASE_URL = 'https://books.toscrape.com/'
CATALOGUE_URL = BASE_URL + 'catalogue/'
MAX_BOOKS = 100

# Ensure MAX_BOOKS is always 100
if __name__ == '__main__':
    MAX_BOOKS = 100  

def get_all_page_urls():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(BASE_URL)
        last_page = 1
        try:
            pager = page.query_selector('.current')
            if pager:
                text = pager.inner_text()
                last_page = int(text.strip().split()[-1])
                print(f"Found {last_page} total pages")
        except Exception as e:
            print(f"Error getting page count: {e}")
        browser.close()
    
    urls = [f'{BASE_URL}catalogue/page-{i}.html' if i > 1 else f'{BASE_URL}catalogue/page-1.html' for i in range(1, last_page+1)]
    print(f"Generated {len(urls)} URLs")
    return urls

def update_progress(current, total, progress_file='progress.json'):
    """Update progress more frequently"""
    percent = int(100 * current / total)
    try:
        with open(progress_file, 'w') as f:
            json.dump({'progress': percent, 'current': current, 'total': total}, f)
    except Exception as e:
        print(f"Error updating progress: {e}")

def scrape_pages(page_urls, max_books, progress_dict=None, worker_id=0):
    all_books = []
    total_books = 0
    print(f"Starting to scrape {max_books} books from {len(page_urls)} pages")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        detail_page = browser.new_page()
        
        for idx, page_url in enumerate(page_urls):
            if total_books >= max_books:
                print(f"Reached max books limit: {total_books}")
                break
                
            page.goto(page_url)
            books = page.query_selector_all('article.product_pod')
            print(f"Worker {worker_id}: Libros encontrados en {page_url}: {len(books)}")
            
            for book in books:
                if total_books >= max_books:
                    print(f"Reached max books limit in inner loop: {total_books}")
                    break
                    
                detail_href = book.query_selector('.image_container a').get_attribute('href')
                detail_full_url = CATALOGUE_URL + detail_href.replace('../../../', '')
                detail_page.goto(detail_full_url)
                
                try:
                    title = detail_page.query_selector('h1').inner_text()
                except Exception:
                    title = ''
                try:
                    price = detail_page.query_selector('.price_color').inner_text()
                except Exception:
                    price = ''
                try:
                    availability = detail_page.query_selector('.availability').inner_text().strip()
                except Exception:
                    availability = ''
                try:
                    description = detail_page.query_selector('#product_description ~ p').inner_text()
                except Exception:
                    description = ''
                info = {}
                try:
                    rows = detail_page.query_selector_all('table.table.table-striped tr')
                    for row in rows:
                        key = row.query_selector('th').inner_text()
                        value = row.query_selector('td').inner_text()
                        info[key] = value
                except Exception:
                    pass
                    
                all_books.append({
                    'title': title,
                    'price': price,
                    'availability': availability,
                    'description': description,
                    'upc': info.get('UPC', ''),
                    'product_type': info.get('Product Type', ''),
                    'price_excl_tax': info.get('Price (excl. tax)', ''),
                    'price_incl_tax': info.get('Price (incl. tax)', ''),
                    'tax': info.get('Tax', ''),
                    'num_reviews': info.get('Number of reviews', ''),
                    'url': detail_full_url
                })
                
                total_books += 1
                
                # Update progress
                if total_books % 5 == 0:
                    update_progress(total_books, max_books)
                    print(f"Progreso: {total_books}/{max_books} libros procesados")
        
        detail_page.close()
        browser.close()
    
    print(f"Worker {worker_id}: Total libros recolectados: {len(all_books)}")
    return all_books

def chunkify(lst, n):
    return [lst[i::n] for i in range(n)]

def worker(args):
    page_urls, max_books, progress_dict, worker_id = args
    return scrape_pages(page_urls, max_books, progress_dict, worker_id)

def main():
    start_time = time.time()
    print(f"Starting scraper with MAX_BOOKS = {MAX_BOOKS}")
    
    page_urls = get_all_page_urls()
    print(f"Procesando {len(page_urls)} páginas")
    
    # Calculate needed pages - ensure we get exactly MAX_BOOKS
    books_per_page = 20
    needed_pages = (MAX_BOOKS + books_per_page - 1) // books_per_page
    page_urls = page_urls[:needed_pages]
    print(f"Needed pages: {needed_pages}, Total pages available: {len(page_urls)}")
    print(f"Target books: {MAX_BOOKS}")
    
    # Use sequential processing for reliability
    print("Using sequential processing for maximum reliability")
    print(f"MAX_BOOKS: {MAX_BOOKS}")
    all_books = scrape_pages(page_urls, MAX_BOOKS, None, 0)
    
    print(f"Total libros recolectados: {len(all_books)}")
    print(f"First book sample: {all_books[0] if all_books else 'No books'}")
    
    elapsed = time.time() - start_time
    
    # Final progress update
    update_progress(len(all_books), MAX_BOOKS)
    
    # Create a simplified version for the web response
    simplified_books = []
    for book in all_books:
        simplified_books.append({
            'title': book['title'],
            'price': book['price'],
            'availability': book['availability'],
            'upc': book['upc'],
            'url': book['url']
        })
    
    result = {'books': len(all_books), 'time': elapsed, 'data': simplified_books}
    print(f"Returning result with {len(all_books)} books (simplified)")
    return result

if __name__ == '__main__':
    result = main()
    import json
    print(json.dumps(result)) 