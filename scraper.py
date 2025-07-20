import requests
from bs4 import BeautifulSoup
import urllib.parse
import re
import time
import random

class PelandoScraper:
    def __init__(self):
        self.base_url = "https://www.pelando.com.br/recentes"
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0"
        ]
        self.affiliate_ids = {
            "amazon": "SEU_ID_AMAZON",
            "mercado livre": "SEU_ID_MERCADOLIVRE",
            "mercadolivre": "SEU_ID_MERCADOLIVRE",
            "aliexpress": "SEU_ID_ALIEXPRESS"
        }

    def get_random_headers(self):
        return {
            "User-Agent": random.choice(self.user_agents),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "pt-BR,pt;q=0.8,en-US;q=0.5,en;q=0.3",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }

    def scrape_offers(self, max_offers=10):
        """Extrai ofertas do site Pelando"""
        try:
            print("Acessando o site Pelando...")
            headers = self.get_random_headers()
            response = requests.get(self.base_url, headers=headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            deal_cards = soup.select('article._deal-card_1jdb6_25')
            
            offers = []
            for card in deal_cards[:max_offers]:
                try:
                    title_element = card.select_one('span._title_mszsg_31')
                    title = title_element.get_text(strip=True) if title_element else ""
                    
                    # Ignorar cupons
                    if "cupom" in title.lower():
                        print(f"\n⚠️ Oferta de cupom ignorada: '{title}'")
                        continue
                    
                    store_element = card.select_one('span._container_13qz9_31 a')
                    store = store_element.get_text(strip=True) if store_element else ""
                    
                    link_element = card.select_one('a._title_mszsg_31')
                    original_link = link_element['href'] if link_element and 'href' in link_element.attrs else ""
                    if original_link and not original_link.startswith("http"):
                        original_link = f"https://www.pelando.com.br{original_link}"
                    
                    # Gerar link de afiliado
                    affiliate_link = self.generate_affiliate_link(title, store)
                    
                    # Extrair preço
                    price_element = card.select_one('span._deal-card-stamp_15l5n_25')
                    price = price_element.get_text(strip=True) if price_element else ""
                    
                    # Extrair temperatura
                    temp_element = card.select_one('span._deal-card-temperature_1o9of_29 span')
                    temperature = temp_element.get_text(strip=True) if temp_element else ""
                    
                    # Extrair timestamp
                    time_element = card.select_one('span._timestamp_1s0as_25')
                    timestamp = time_element.get_text(strip=True) if time_element else ""
                    
                    # Extrair imagem
                    img_element = card.select_one('img._deal-card-image_1glvo_31')
                    image_url = img_element['src'] if img_element and 'src' in img_element.attrs else ""
                    
                    offers.append({
                        'title': title,
                        'price': price,
                        'store': store,
                        'temperature': temperature,
                        'timestamp': timestamp,
                        'link': affiliate_link,
                        'original_link': original_link,
                        'image_url': image_url
                    })
                    
                    # Pausa aleatória para evitar bloqueio
                    time.sleep(random.uniform(1.0, 3.0))
                    
                except Exception as e:
                    print(f"Erro ao processar oferta: {e}")
                    continue
                
            print(f"Encontradas {len(offers)} ofertas")
            return offers

        except Exception as e:
            print(f"Erro ao acessar Pelando: {e}")
            return []

    def generate_affiliate_link(self, title, store):
        """Gera link de afiliado buscando no Google"""
        if not title or not store:
            return ""
        
        try:
            # Criar query de busca
            search_query = f"{title} {store}"
            print(f"\n🔍 Buscando: '{search_query}'")
            
            # Buscar no Google
            google_url = f"https://www.google.com/search?q={urllib.parse.quote_plus(search_query)}"
            headers = self.get_random_headers()
            response = requests.get(google_url, headers=headers)
            response.raise_for_status()
            
            # Parsear resultados
            soup = BeautifulSoup(response.text, 'html.parser')
            links = soup.select('a')
            
            # Procurar link relevante
            for link in links:
                href = link.get('href')
                if href and href.startswith('/url?q='):
                    # Extrair URL real
                    clean_url = re.search(r'/url\?q=([^&]+)', href)
                    if clean_url:
                        product_url = urllib.parse.unquote(clean_url.group(1))
                        
                        # Verificar se é URL de produto
                        if self.is_product_url(product_url, store):
                            # Adicionar parâmetro de afiliado
                            return self.add_affiliate_param(product_url, store)
            
            print("⚠️ Nenhum link de produto encontrado")
            return ""
            
        except Exception as e:
            print(f"❌ Erro na busca do Google: {e}")
            return ""

    def is_product_url(self, url, store):
        """Verifica se a URL é de um produto válido"""
        store_lower = store.lower()
        
        if "amazon" in store_lower:
            return "amazon." in url and "/dp/" in url
        elif "mercado livre" in store_lower or "mercadolivre" in store_lower:
            return "mercadolivre." in url and ("/p/" in url or "MLB-" in url)
        elif "aliexpress" in store_lower:
            return "aliexpress." in url and "/item/" in url
        
        return True  # Para outras lojas, aceita qualquer URL

    def add_affiliate_param(self, url, store):
        """Adiciona parâmetro de afiliado à URL"""
        store_lower = store.lower()
        
        # Determinar parâmetro correto para cada loja
        if "amazon" in store_lower:
            param = "tag"
            affiliate_id = self.affiliate_ids.get("amazon", "")
        elif "mercado livre" in store_lower or "mercadolivre" in store_lower:
            param = "afiliado"
            affiliate_id = self.affiliate_ids.get("mercado livre", "")
        elif "aliexpress" in store_lower:
            # AliExpress usa URL especial
            return f"https://s.click.aliexpress.com/e/{self.affiliate_ids.get('aliexpress', '')}?product_url={urllib.parse.quote(url)}"
        else:
            return url  # Sem afiliado para outras lojas
        
        if not affiliate_id:
            return url
        
        # Adicionar parâmetro à query string
        parsed = urllib.parse.urlparse(url)
        query = urllib.parse.parse_qs(parsed.query)
        query[param] = [affiliate_id]
        new_query = urllib.parse.urlencode(query, doseq=True)
        
        return urllib.parse.urlunparse((
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            new_query,
            parsed.fragment
        ))

def main():
    scraper = PelandoScraper()
    offers = scraper.scrape_offers(max_offers=5)

    print("\n=== RESULTADOS ===")
    for i, offer in enumerate(offers, 1):
        print(f"\n{i}. {offer['title']}")
        print(f"   Loja: {offer['store']}")
        print(f"   Preço: {offer['price']}")
        print(f"   Temperatura: {offer['temperature']}")
        print(f"   Link Original: {offer['original_link']}")
        print(f"   Link Afiliado: {offer['link'][:70]}{'...' if len(offer['link']) > 70 else ''}")

if __name__ == '__main__':
    main()