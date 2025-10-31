import os
import requests
from firecrawl import FirecrawlApp

class ScrapingService:
    def __init__(self):
        self.api_key = os.getenv("FIRECRAWL_API_KEY")

        self.app = FirecrawlApp(api_key=self.api_key)
    
    def scrape_website(self, url, collection_name):
        """Scraping completo em uma função"""
        try:
            # 1. Mapear URLs
            map_result = self.app.map(url)

            # Extrair links
            if hasattr(map_result, 'links'):
                links = map_result.links
            elif hasattr(map_result, 'data') and hasattr(map_result.data, 'links'):
                links = map_result.data.links
            else:
                links = getattr(map_result, 'links', [])

            if not links:
                raise Exception("Nenhum link encontrado!")

            urls = []
            for item in links:
                if isinstance(item, str):
                    urls.append(item)
                elif isinstance(item, dict) and "url" in item:
                    urls.append(item["url"])
                elif hasattr(item, "url"):
                    urls.append(item.url)
                elif hasattr(item, "__dict__") and "url" in item.__dict__:
                    urls.append(item.__dict__["url"])

            # Remove duplicados e URLs inválidas
            urls = list({u for u in urls if isinstance(u, str) and u.startswith("http")})

            if not urls:
                raise Exception("Nenhuma URL válida encontrada após mapeamento!")

            print(f"{len(urls)} URLs prontas para scraping.")

            # 2. Fazer scraping
            scrape_result = self.app.batch_scrape(urls)

            # 3. Extrair dados
            if hasattr(scrape_result, 'data'):
                scraped_data = scrape_result.data
            else:
                scraped_data = scrape_result.get("data", []) if hasattr(scrape_result, 'get') else []

            # 4. Salvar arquivos
            collection_path = f"data/collections/{collection_name}"
            os.makedirs(collection_path, exist_ok=True)

            saved_count = 0
            for i, page in enumerate(scraped_data, 1):
                if hasattr(page, 'markdown') and page.markdown:
                    markdown_content = page.markdown
                elif hasattr(page, 'data') and hasattr(page.data, 'markdown'):
                    markdown_content = page.data.markdown
                elif isinstance(page, dict) and page.get("markdown"):
                    markdown_content = page["markdown"]
                else:
                    continue

                with open(f"{collection_path}/{i}.md", "w", encoding="utf-8") as f:
                    f.write(markdown_content)
                saved_count += 1

            return {"success": True, "files": saved_count}

        except Exception as e:
            print(f"Erro no scraping: {str(e)}")
            return {"success": False, "error": str(e)}
