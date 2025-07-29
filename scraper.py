from playwright.sync_api import sync_playwright
import pandas as pd
from multiprocessing import Pool, cpu_count
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

def scrape_pages(page_urls, progress_file=None, total_pages=None, pages_done=None, max_books=MAX_BOOKS, global_count=None, progress_step=5):
    all_books = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        detail_page = browser.new_page()
        for idx, page_url in enumerate(page_urls):
            if global_count and global_count[0] >= max_books:
                break
            page.goto(page_url)
            books = page.query_selector_all('article.product_pod')
            print(f"Libros encontrados en {page_url}: {len(books)}")
            for book in books:
                if global_count and global_count[0] >= max_books:
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
                if global_count:
                    global_count[0] += 1
            if progress_file and total_pages and pages_done is not None:
                pages_done[0] += 1
                if pages_done[0] % progress_step == 0 or pages_done[0] == total_pages:
                    percent = int(100 * pages_done[0] / total_pages)
                    with open(progress_file, 'w') as f:
                        json.dump({'progress': percent}, f)
        detail_page.close()
        browser.close()
    print(f"Total libros recolectados en este proceso: {len(all_books)}")
    return all_books

def chunkify(lst, n):
    return [lst[i::n] for i in range(n)]

def worker(args):
    return scrape_pages(*args)

def main():
    start_time = time.time()
    page_urls = get_all_page_urls()
    print(f"Procesando {len(page_urls)} páginas")
    max_books = MAX_BOOKS
    # Calcula el número de páginas necesarias para max_books
    books_per_page = 20  # books.toscrape.com tiene 20 libros por página
    needed_pages = (max_books + books_per_page - 1) // books_per_page
    page_urls = page_urls[:needed_pages]
    num_workers = min(4, cpu_count(), len(page_urls))
    chunks = chunkify(page_urls, num_workers)
    progress_file = 'progress.json'
    total_pages = len(page_urls)
    pages_done = [0]
    global_count = [0]
    # Inicializa progreso
    with open(progress_file, 'w') as f:
        json.dump({'progress': 0}, f)
    args = [(chunk, progress_file, total_pages, pages_done, max_books, global_count) for chunk in chunks]
    with Pool(processes=num_workers) as pool:
        results = pool.map(worker, args)
    all_books = [book for sublist in results for book in sublist][:max_books]
    print(f"Total libros recolectados en todos los procesos: {len(all_books)}")
    df = pd.DataFrame(all_books)
    print(df.head())
    print(df.shape)
    df.to_excel('books.xlsx', index=False)
    elapsed = time.time() - start_time
    with open(progress_file, 'w') as f:
        json.dump({'progress': 100}, f)
    return {'books': len(all_books), 'time': elapsed}

if __name__ == '__main__':
    result = main()
    import json
    print(json.dumps(result)) 