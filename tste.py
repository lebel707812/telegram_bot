import asyncio
import json
from playwright.async_api import async_playwright
from datetime import datetime
import re
import os
import urllib.parse
import aiohttp
import random

class PelandoScraper:
    def __init__(self):
        self.base_url = "https://www.pelando.com.br/recentes"
        self.affiliate_id_amazon = "SEU_ID_AFILIADO_AMAZON"
        self.affiliate_id_aliexpress = "SEU_ID_AFILIADO_ALIEXPRESS"
        self.affiliate_id_mercadolivre = "SEU_ID_AFILIADO_MERCADOLIVRE"
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0"
        ]

    async def scrape_offers(self, max_offers=10):
        """Extrai ofertas do site Pelando"""
        async with async_playwright() as p:
            user_data_dir = "./playwright_user_data"
            is_first_run = not os.path.exists(user_data_dir) or not os.listdir(user_data_dir)
            headless_mode = not is_first_run
            
            if is_first_run:
                print("PRIMEIRA EXECUÇÃO: Faça login no Mercado Livre e feche o navegador")
                
            browser = await p.chromium.launch_persistent_context(
                user_data_dir, 
                headless=headless_mode,
                slow_mo=1000 if is_first_run else 0,
                user_agent=random.choice(self.user_agents)
            )
            try:
                if is_first_run:
                    page = await browser.new_page()
                    await page.goto("https://www.mercadolivre.com.br/afiliados/linkbuilder#hub")
                    print("Faça login manualmente e feche o navegador")
                    await page.wait_for_timeout(300000)
                    await browser.close()
                    print("Login concluído. Execute novamente.")
                    return []
                
                print("Acessando o site Pelando...")
                page = await browser.new_page()
                await page.goto(self.base_url, wait_until="networkidle")
                await page.wait_for_selector("._deal-card_1jdb6_25", timeout=20000)
                offers = await self._extract_offers(page, max_offers, browser)
                print(f"Encontradas {len(offers)} ofertas")
                return offers

            except Exception as e:
                print(f"Erro ao fazer scraping: {e}")
                return []
            finally:
                await browser.close()

    async def _extract_offers(self, page, max_offers, browser):
        """Extrai informações das ofertas da página"""
        offers = []
        deal_cards = await page.query_selector_all("._deal-card_1jdb6_25")
        
        for i, card in enumerate(deal_cards[:max_offers]):
            try:
                # Extrair título básico
                title_element = await card.query_selector("._title_mszsg_31")
                title = await title_element.inner_text() if title_element else ""
                
                # Ignorar cupons
                if "cupom" in title.lower():
                    print(f"\n⚠️ Oferta de cupom ignorada: '{title}'")
                    continue
                    
                offer = await self._extract_offer_data(card, browser)
                if offer:
                    offers.append(offer)
            except Exception as e:
                print(f"Erro ao extrair oferta {i}: {e}")
                continue
                
        return offers

    async def _extract_offer_data(self, card, browser):
        """Extrai dados de uma oferta específica"""
        try:
            # Extração básica de dados
            title_element = await card.query_selector("._title_mszsg_31")
            title = await title_element.inner_text() if title_element else ""

            link_element = await card.query_selector("._title_mszsg_31")
            original_link = await link_element.get_attribute("href") if link_element else ""
            if original_link and not original_link.startswith("http"):
                original_link = f"https://www.pelando.com.br{original_link}"

            # Gerar link de afiliado
            store_element = await card.query_selector("._container_13qz9_31 a")
            store = await store_element.inner_text() if store_element else ""
            
            affiliate_link = original_link  # Default
            
            # Apenas para Mercado Livre e Amazon
            if "mercado livre" in store.lower() or "mercadolivre" in store.lower():
                affiliate_link = await self._simple_mercado_livre_search(title, store, browser)
            elif "amazon" in store.lower():
                affiliate_link = await self._simple_amazon_search(title, store, browser)

            # Extrair outros dados
            price_element = await card.query_selector("._deal-card-stamp_15l5n_25")
            price = await price_element.inner_text() if price_element else "Preço não informado"
            
            temp_element = await card.query_selector("._deal-card-temperature_1o9of_29 span")
            temperature = await temp_element.inner_text() if temp_element else "0°"
            
            time_element = await card.query_selector("._timestamp_1s0as_25")
            timestamp = await time_element.inner_text() if time_element else "Tempo não informado"
            
            img_element = await card.query_selector("._deal-card-image_1glvo_31")
            image_url = await img_element.get_attribute("src") if img_element else ""

            return {
                'title': title.strip(),
                'price': price.strip(),
                'store': store.strip(),
                'temperature': temperature.strip(),
                'timestamp': timestamp.strip(),
                'link': affiliate_link,
                'original_link': original_link,
                'image_url': image_url,
                'scraped_at': datetime.now().isoformat()
            }

        except Exception as e:
            print(f"Erro ao extrair dados: {e}")
            return None

    async def _simple_mercado_livre_search(self, title, store, browser):
        """Busca direta no Google para encontrar produto no Mercado Livre"""
        try:
            # Criar query de busca
            search_query = urllib.parse.quote(f"{title} {store}")
            print(f"\n🔍 [Mercado Livre] Buscando: '{title}'")
            
            # Abrir nova página
            page = await browser.new_page()
            await page.set_extra_http_headers({"User-Agent": random.choice(self.user_agents)})
            await page.goto(f"https://www.google.com/search?q={search_query}", 
                           wait_until="networkidle", 
                           timeout=30000)
            
            # Localizar o primeiro link do Mercado Livre
            ml_links = await page.query_selector_all('a[href*="mercadolivre.com.br"]')
            
            for link in ml_links:
                href = await link.get_attribute('href')
                if href and ('/p/' in href or 'MLB-' in href or 'produto' in href):
                    # Limpar URL do Google
                    if 'url?q=' in href:
                        match = re.search(r'url\?q=([^&]+)', href)
                        if match:
                            clean_url = urllib.parse.unquote(match.group(1))
                    else:
                        clean_url = href
                    
                    print(f"✅ Link encontrado: {clean_url[:70]}...")
                    
                    # Adicionar parâmetro de afiliado
                    if self.affiliate_id_mercadolivre:
                        return f"{clean_url}?afiliado={self.affiliate_id_mercadolivre}"
                    return clean_url
            
            print("⚠️ Nenhum link encontrado, usando link original")
            return ""
            
        except Exception as e:
            print(f"❌ Erro na busca: {str(e)}")
            return ""
        finally:
            await page.close()

    async def _simple_amazon_search(self, title, store, browser):
        """Busca direta no Google para encontrar produto na Amazon"""
        try:
            # Criar query de busca
            search_query = urllib.parse.quote(f"{title} {store}")
            print(f"\n🔍 [Amazon] Buscando: '{title}'")
            
            # Abrir nova página
            page = await browser.new_page()
            await page.set_extra_http_headers({"User-Agent": random.choice(self.user_agents)})
            await page.goto(f"https://www.google.com/search?q={search_query}", 
                           wait_until="networkidle", 
                           timeout=30000)
            
            # Localizar o primeiro link da Amazon
            amazon_links = await page.query_selector_all('a[href*="amazon."]')
            
            for link in amazon_links:
                href = await link.get_attribute('href')
                if href and '/dp/' in href:  # Padrão de URL de produto na Amazon
                    # Limpar URL do Google
                    if 'url?q=' in href:
                        match = re.search(r'url\?q=([^&]+)', href)
                        if match:
                            clean_url = urllib.parse.unquote(match.group(1))
                    else:
                        clean_url = href
                    
                    # Remover parâmetros de tracking
                    clean_url = re.sub(r'\/ref=[^?]+', '', clean_url)
                    clean_url = clean_url.split('?')[0]
                    
                    print(f"✅ Link encontrado: {clean_url[:70]}...")
                    
                    # Adicionar parâmetro de afiliado
                    if self.affiliate_id_amazon:
                        return f"{clean_url}?tag={self.affiliate_id_amazon}"
                    return clean_url
            
            print("⚠️ Nenhum link encontrado, usando link original")
            return ""
            
        except Exception as e:
            print(f"❌ Erro na busca: {str(e)}")
            return ""
        finally:
            await page.close()

async def main():
    scraper = PelandoScraper()
    offers = await scraper.scrape_offers(max_offers=5)

    print("\n=== RESULTADOS ===")
    for i, offer in enumerate(offers, 1):
        print(f"\n{i}. {offer['title']}")
        print(f"   Preço: {offer['price']}")
        print(f"   Loja: {offer['store']}")
        print(f"   Temperatura: {offer['temperature']}")
        print(f"   Link Afiliado: {offer['link'][:70]}{'...' if len(offer['link']) > 70 else ''}")

if __name__ == '__main__':
    asyncio.run(main())
            
