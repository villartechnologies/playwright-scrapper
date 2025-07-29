from playwright.sync_api import sync_playwright
import pandas as pd
from multiprocessing import Pool, cpu_count, Manager
import time
import json
from io import BytesIO

BASE_URL = 'https://books.toscrape.com/'
CATALOGUE_URL = BASE_URL + 'catalogue/'
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
        except Exception:
            pass
        browser.close()
    return [f'{BASE_URL}catalogue/page-{i}.html' if i > 1 else f'{BASE_URL}catalogue/page-1.html' for i in range(1, last_page+1)]

def update_progress(current, total, progress_file='progress.json'):
    """Update progress more frequently"""
    percent = int(100 * current / total)
    try:
        with open(progress_file, 'w') as f:
            json.dump({'progress': percent, 'current': current, 'total': total}, f)
    except Exception as e:
        print(f"Error updating progress: {e}")

def scrape_pages(page_urls, max_books, progress_dict, worker_id):
    all_books = []
    total_books = 0
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        detail_page = browser.new_page()
        
        for idx, page_url in enumerate(page_urls):
            if total_books >= max_books:
                break
                
            page.goto(page_url)
            books = page.query_selector_all('article.product_pod')
            print(f"Worker {worker_id}: Libros encontrados en {page_url}: {len(books)}")
            
            for book in books:
                if total_books >= max_books:
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
                
                # Update shared progress
                progress_dict['current'] += 1
                if progress_dict['current'] % 5 == 0:
                    update_progress(progress_dict['current'], progress_dict['total'])
                    print(f"Progreso global: {progress_dict['current']}/{progress_dict['total']} libros procesados")
        
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
    page_urls = get_all_page_urls()
    print(f"Procesando {len(page_urls)} páginas")
    
    # Calculate needed pages
    books_per_page = 20
    needed_pages = (MAX_BOOKS + books_per_page - 1) // books_per_page
    page_urls = page_urls[:needed_pages]
    
    # Setup multiprocessing
    num_workers = min(4, cpu_count(), len(page_urls))
    chunks = chunkify(page_urls, num_workers)
    
    # Initialize progress
    update_progress(0, MAX_BOOKS)
    
    # Use Manager for shared progress
    with Manager() as manager:
        progress_dict = manager.dict()
        progress_dict['current'] = 0
        progress_dict['total'] = MAX_BOOKS
        
        # Prepare arguments for workers
        args = [(chunk, MAX_BOOKS // num_workers, progress_dict, i) for i, chunk in enumerate(chunks)]
        
        # Run workers
        with Pool(processes=num_workers) as pool:
            results = pool.map(worker, args)
    
    # Combine results
    all_books = [book for sublist in results for book in sublist][:MAX_BOOKS]
    
    print(f"Total libros recolectados: {len(all_books)}")
    
    elapsed = time.time() - start_time
    
    # Final progress update
    update_progress(len(all_books), MAX_BOOKS)
    
    return {'books': len(all_books), 'time': elapsed, 'data': all_books}

if __name__ == '__main__':
    result = main()
    import json
    print(json.dumps(result)) 