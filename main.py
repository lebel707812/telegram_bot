import asyncio
import json
import os
from datetime import datetime
from scraper import PelandoScraper
from telegram_bot import TelegramBot

class OfferBot:
    def __init__(self, bot_token: str, chat_id: str):
        self.scraper = PelandoScraper()
        self.telegram_bot = TelegramBot(bot_token, chat_id)
        self.sent_offers_file = "sent_offers.json"
        self.sent_offers = self.load_sent_offers()
    
    def load_sent_offers(self):
        """Carrega a lista de ofertas já enviadas"""
        if os.path.exists(self.sent_offers_file):
            try:
                with open(self.sent_offers_file, 'r', encoding='utf-8') as f:
                    return set(json.load(f))
            except:
                return set()
        return set()
    
    def save_sent_offers(self):
        """Salva a lista de ofertas já enviadas"""
        try:
            with open(self.sent_offers_file, 'w', encoding='utf-8') as f:
                json.dump(list(self.sent_offers), f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Erro ao salvar ofertas enviadas: {e}")
    
    def generate_offer_id(self, offer):
        """Gera um ID único para a oferta baseado no título e preço"""
        return f"{offer['title']}_{offer['price']}".replace(' ', '_').lower()
    
    async def check_and_send_new_offers(self, max_offers=10):
        """Verifica novas ofertas e envia as que ainda não foram enviadas"""
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Iniciando verificação de ofertas...")
        
        # Faz o scraping das ofertas
        offers = await self.scraper.scrape_offers(max_offers)
        
        if not offers:
            print("Nenhuma oferta encontrada.")
            return
        
        # Filtra ofertas novas
        new_offers = []
        for offer in offers:
            offer_id = self.generate_offer_id(offer)
            if offer_id not in self.sent_offers:
                new_offers.append(offer)
                self.sent_offers.add(offer_id)
        
        if not new_offers:
            print("Nenhuma oferta nova encontrada.")
            return
        
        print(f"Encontradas {len(new_offers)} ofertas novas. Enviando para o Telegram...")
        
        # Envia as ofertas novas
        sent_count = await self.telegram_bot.send_offers_batch(new_offers, delay=3)
        
        # Salva a lista atualizada
        self.save_sent_offers()
        
        print(f"Processo concluído. {sent_count} ofertas enviadas.")
    
    async def run_continuous(self, interval_minutes=30):
        """Executa o bot continuamente com intervalo especificado"""
        print(f"Bot iniciado. Verificando ofertas a cada {interval_minutes} minutos...")
        
        while True:
            try:
                await self.check_and_send_new_offers()
            except Exception as e:
                print(f"Erro durante execução: {e}")
            
            # Aguarda o intervalo especificado
            print(f"Aguardando {interval_minutes} minutos até a próxima verificação...")
            await asyncio.sleep(interval_minutes * 60)

async def main():
    # Configurações do bot
    BOT_TOKEN = "7548666335:AAHqCk11jsqhUtUbb79NYtCint-9cCLt7ws"
    CHAT_ID = "-1002593394513"
    
    # Cria o bot
    bot = OfferBot(BOT_TOKEN, CHAT_ID)
    
    # Execução única para teste
    print("=== EXECUÇÃO DE TESTE ===")
    await bot.check_and_send_new_offers(max_offers=5)
    
    # Para execução contínua, descomente a linha abaixo:
    # await bot.run_continuous(interval_minutes=30)

if __name__ == '__main__':
    asyncio.run(main())

