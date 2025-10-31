import os
from dontenv import load_dotenv


load_dotenv()

class ScrapingService:
    def __init__(self):
        self.api_key = os.getenv("FIRECRAWL_API_KEY")
        self.api_url = None

        self.app = FirecrawlApp(api_key=self.api_key)
 
    def scrape_website(self, url, collection_name):
        try:
            map_result = self.app.map(url)

            if hasattr(map_result, 'links'):
                links = map_result.links
            elif hasattr(map_result, 'data') and hasattr(map_result.data, 'links'):
                links = map_result.data.links
            else:
                links = getattr(map_result, 'links', [])
            if not links:
                raise Exception("Nenhum link encontrado na página.")
            
            print(f"Links encontrados na página: {links}")

            scrape_result = self.app.batch_scrape_urls(links)

            if hasattr(scrape_result, 'data'):
                scraped_data = scrape_result.data
            else:
                scraped_data = getattr("data", []) if hasattr(scrape_result, 'get') else []

            collection_path = f"data/collections/{collection_name}"
            if not os.path.exists(collection_path):
                os.makedirs(collection_path)

            saved_count = 0
            for i, page in enumerate(scraped_data, 1):
                if hasattr(page, 'markedown') and page.markdown:
                    markdown_content = page.markdown
                elif hasattr(page, 'data') and hasattr(page.data, 'markdown'):
                    markdown_content = page.data.markdown
                elif isinstance(page, dict) and page.get('markdown'):
                    markdown_content = page['markdown']
                else:
                    continue

                with open(f"{collection_path}/{i}.md", "w", encoding="utf-8") as file:
                    file.write(markdown_content)

                    saved_count += 1
        except Exception as e:
            print(f"Erro no scraping: {str(e)}")
            return {"sucess" : False, "error": str(e)}


