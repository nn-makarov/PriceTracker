import aiohttp
import re

async def parse_yamarket(product_url: str):
    """
    Парсер Яндекс.Маркет
    """
    try:
        print(f"🔍 Реальный парсинг Яндекс.Маркет: {product_url}")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'ru-RU,ru;q=0.9,en;q=0.8',
        }
        
        clean_url = product_url.split('?')[0]
        
        async with aiohttp.ClientSession() as session:
            async with session.get(clean_url, headers=headers, timeout=10) as response:
                print(f"📡 Статус: {response.status}")
                
                if response.status == 200:
                    html = await response.text()
                    
                    price_match = re.search(r'"price":\s*"?(\d+)"?', html)
                    if not price_match:
                        price_match = re.search(r'data-auto="price-value">\s*([\d\s]+)\s*₽', html)
                    if not price_match:
                        price_match = re.search(r'"formattedPrice":"([\d\s]+)\s*₽"', html)

                    if price_match:
                        try:
                            price_text = price_match.group(1).replace(' ', '')
                            price = int(price_text)
                        except (ValueError, AttributeError):
                            price = 0
                            print("⚠️ Не удалось преобразовать цену в число")
                    else:
                        price = 0
                        print("⚠️ Цена не найдена в HTML")
                    
                    title_match = re.search(r'<h1[^>]*data-auto="title"[^>]*>(.*?)</h1>', html)
                    if not title_match:
                        title_match = re.search(r'<title[^>]*>(.*?) - Яндекс Маркет</title>', html)
                    if not title_match:
                        title_match = re.search(r'<meta[^>]*property="og:title"[^>]*content="([^"]+)"', html)

                    if title_match:
                        title = title_match.group(1).strip()
                        
                        title = re.sub(r'<[^>]+>', '', title)
                        
                        if len(title) < 5 or '@' in title or 'marketfront' in title:
                            title = generate_title_from_url(clean_url)
                    else:
                        title = generate_title_from_url(clean_url)
                    
                    
                    product_id = re.search(r'/(\d+)(?:\?|$)', clean_url)
                    
                    if price > 0:
                        return {
                            'success': True,
                            'price': price,
                            'title': title,
                            'url': clean_url,
                            'product_id': product_id.group(1) if product_id else re.sub(r'\D', '', clean_url)[-10:] or "yamarket",
                            'source': 'yamarket'
                        }
                    else:
                        return {'success': False, 'error': 'Цена не найдена или равна 0'}
                    
                else:
                    return {'success': False, 'error': f'Ошибка {response.status}'}
                
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return {'success': False, 'error': str(e)}

def generate_title_from_url(url: str):
    """Простая генерация названия"""
    match = re.search(r'/card/([^/]+)/', url)
    return match.group(1).replace('-', ' ').title() if match else "Товар Яндекс.Маркет"