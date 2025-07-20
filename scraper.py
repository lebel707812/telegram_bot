import asyncio
import json
from playwright.async_api import async_playwright
from datetime import datetime
import re
import os
import urllib.parse
import aiohttp

class PelandoScraper:
    def __init__(self):
        self.base_url = "https://www.pelando.com.br/"
        self.affiliate_id_amazon = "SEU_ID_AFILIADO_AMAZON"
        self.affiliate_id_aliexpress = "SEU_ID_AFILIADO_ALIEXPRESS"
        self.affiliate_id_mercadolivre = "SEU_ID_AFILIADO_MERCADOLIVRE"

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
                slow_mo=1000 if is_first_run else 0
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
            clean_title = self._clean_title(title)

            link_element = await card.query_selector("._title_mszsg_31")
            original_link = await link_element.get_attribute("href") if link_element else ""
            if original_link and not original_link.startswith("http"):
                original_link = f"https://www.pelando.com.br{original_link}"

            # Gerar link de afiliado
            store_element = await card.query_selector("._container_13qz9_31 a")
            store = await store_element.inner_text() if store_element else ""
            affiliate_link = await self._generate_affiliate_link(
                original_link, 
                store, 
                clean_title,
                browser
            )

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

    def _clean_title(self, title):
        """Remove caracteres especiais e palavras irrelevantes"""
        clean_title = re.sub(r'[^\w\s]', ' ', title)
        stopwords = ['OFF', 'Desconto', 'Promoção', 'Oferta', 'cupom', 'R\$', 'reais']
        words = [word for word in clean_title.split() 
                 if word.lower() not in stopwords and len(word) > 2]
        return ' '.join(words[:10])

    async def _generate_affiliate_link(self, original_url, store_name, title, browser):
        """Gera link de afiliado com base na loja"""
        store_name_lower = (store_name or "").lower()
        
        if "mercado livre" in store_name_lower or "mercadolivre" in store_name_lower:
            return await self._generate_mercado_livre_affiliate_link(title, browser)
        return original_url

    async def _generate_mercado_livre_affiliate_link(self, title, browser):
        """Solução unificada para produtos com API + Google"""
        try:
            # Tentativa 1: API Mercado Livre
            api_url = f"https://api.mercadolibre.com/sites/MLB/search?q={urllib.parse.quote(title)}&limit=1"
            async with aiohttp.ClientSession() as session:
                async with session.get(api_url) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('results') and len(data['results']) > 0:
                            product_url = data['results'][0]['permalink']
                            print(f"✅ Link via API: {product_url[:60]}...")
                            return self._add_affiliate_param(product_url)
            
            # Tentativa 2: Busca no Google
            print(f"🔍 Buscando no Google: '{title}'")
            page = await browser.new_page()
            try:
                search_query = urllib.parse.quote(f"{title} site:mercadolivre.com.br")
                await page.goto(f"https://www.google.com/search?q={search_query}", 
                               wait_until="networkidle", 
                               timeout=30000)
                
                # Localizar todos os links do Mercado Livre
                results = await page.query_selector_all('a[href*="mercadolivre.com.br"]')
                for link in results:
                    href = await link.get_attribute('href')
                    if href and ('/p/' in href or 'MLB-' in href):
                        # Limpar URL do Google
                        match = re.search(r'url\?q=([^&]+)', href)
                        if match:
                            clean_url = urllib.parse.unquote(match.group(1))
                            print(f"✅ Link via Google: {clean_url[:60]}...")
                            return self._add_affiliate_param(clean_url)
            finally:
                await page.close()
            
            print("⚠️ Nenhum link encontrado")
            return ""
            
        except Exception as e:
            print(f"❌ Erro na busca: {str(e)}")
            return ""

    def _add_affiliate_param(self, url):
        """Adiciona parâmetro de afiliado mantendo query existente"""
        if not self.affiliate_id_mercadolivre or not url:
            return url
            
        parsed = urllib.parse.urlparse(url)
        query = urllib.parse.parse_qs(parsed.query)
        query['afiliado'] = [self.affiliate_id_mercadolivre]
        new_query = urllib.parse.urlencode(query, doseq=True)
        
        return urllib.parse.urlunparse((
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            new_query,
            parsed.fragment
        ))

async def main():
    scraper = PelandoScraper()
    offers = await scraper.scrape_offers(max_offers=5)

    print("\n=== RESULTADOS ===")
    for i, offer in enumerate(offers, 1):
        print(f"\n{i}. {offer['title']}")
        print(f"   Preço: {offer['price']}")
        print(f"   Loja: {offer['store']}")
        print(f"   Temperatura: {offer['temperature']}")
        print(f"   Link Original: {offer['original_link']}")
        print(f"   Link Afiliado: {offer['link'][:70]}{'...' if len(offer['link']) > 70 else ''}")

if __name__ == '__main__':
    asyncio.run(main())