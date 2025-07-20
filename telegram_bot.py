import asyncio
import aiohttp
from typing import List, Dict

class TelegramBot:
    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
    
    async def send_message(self, text: str, parse_mode: str = "HTML"):
        """Envia uma mensagem de texto para o canal"""
        url = f"{self.base_url}/sendMessage"
        
        data = {
            'chat_id': self.chat_id,
            'text': text,
            'parse_mode': parse_mode,
            'disable_web_page_preview': False
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(url, json=data) as response:
                    result = await response.json()
                    if response.status == 200 and result.get('ok'):
                        print("Mensagem enviada com sucesso!")
                        return True
                    else:
                        print(f"Erro ao enviar mensagem: {result}")
                        return False
            except Exception as e:
                print(f"Erro na requisição: {e}")
                return False
    
    async def send_photo(self, photo_url: str, caption: str = "", parse_mode: str = "HTML"):
        """Envia uma foto com legenda para o canal"""
        url = f"{self.base_url}/sendPhoto"
        
        data = {
            'chat_id': self.chat_id,
            'photo': photo_url,
            'caption': caption,
            'parse_mode': parse_mode
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(url, json=data) as response:
                    result = await response.json()
                    if response.status == 200 and result.get('ok'):
                        print("Foto enviada com sucesso!")
                        return True
                    else:
                        print(f"Erro ao enviar foto: {result}")
                        return False
            except Exception as e:
                print(f"Erro na requisição: {e}")
                return False
    
    def format_offer_message(self, offer: Dict) -> str:
        """Formata uma oferta para envio no Telegram"""
        message = f"""🔥 <b>{offer['title']}</b>

💰 <b>Preço:</b> {offer['price']}
🏪 <b>Loja:</b> {offer['store']}
🌡️ <b>Temperatura:</b> {offer['temperature']}
⏰ <b>Postado:</b> {offer['timestamp']}

🔗 <a href="{offer['link']}">Ver oferta completa</a>

#oferta #promocao #{offer['store'].lower().replace(' ', '')}"""
        
        return message
    
    async def send_offer(self, offer: Dict):
        """Envia uma oferta formatada para o canal"""
        message = self.format_offer_message(offer)
        
        # Se há imagem, envia como foto com legenda
        if offer.get('image_url'):
            return await self.send_photo(offer['image_url'], message)
        else:
            # Senão, envia apenas como mensagem de texto
            return await self.send_message(message)
    
    async def send_offers_batch(self, offers: List[Dict], delay: int = 2):
        """Envia múltiplas ofertas com delay entre elas"""
        sent_count = 0
        
        for offer in offers:
            success = await self.send_offer(offer)
            if success:
                sent_count += 1
            
            # Delay entre mensagens para evitar rate limiting
            if delay > 0:
                await asyncio.sleep(delay)
        
        print(f"Enviadas {sent_count} de {len(offers)} ofertas")
        return sent_count

# Teste da funcionalidade
async def test_telegram_bot():
    # Configurações do bot (substitua pelos seus valores)
    BOT_TOKEN = "7548666335:AAHqCk11jsqhUtUbb79NYtCint-9cCLt7ws"
    CHAT_ID = "-1002593394513"
    
    bot = TelegramBot(BOT_TOKEN, CHAT_ID)
    
    # Teste com uma oferta de exemplo
    test_offer = {
        'title': 'Teste - Oferta de Exemplo',
        'price': 'R$ 99,90',
        'store': 'Loja Teste',
        'temperature': '25°',
        'timestamp': '5 min',
        'link': 'https://www.pelando.com.br/',
        'image_url': 'https://via.placeholder.com/300x200.png?text=Teste'
    }
    
    await bot.send_offer(test_offer)

if __name__ == '__main__':
    asyncio.run(test_telegram_bot())

