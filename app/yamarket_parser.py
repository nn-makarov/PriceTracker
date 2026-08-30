import aiohttp
import re
import logging

logger = logging.getLogger("pricetracker")


async def parse_yamarket(product_url: str):
    """Разбор страницы товара Яндекс.Маркета: достаёт название и цену."""
    try:
        logger.info(f"Парсинг Яндекс.Маркет: {product_url}")

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
        }

        clean_url = product_url.split("?")[0]
        timeout = aiohttp.ClientTimeout(total=10)

        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(clean_url, headers=headers) as response:
                logger.info(f"Статус ответа Яндекс.Маркета: {response.status}")

                if response.status != 200:
                    return {"success": False, "error": f"Маркет ответил кодом {response.status}"}

                html = await response.text()

        # Цену ищем несколькими шаблонами — вёрстка Маркета непостоянна.
        price = 0
        for pattern in (
            r'"price":\s*"?(\d+)"?',
            r'data-auto="price-value">\s*([\d\s]+)\s*₽',
            r'"formattedPrice":"([\d\s]+)\s*₽"',
        ):
            m = re.search(pattern, html)
            if m:
                try:
                    price = int(m.group(1).replace(" ", ""))
                    break
                except (ValueError, AttributeError):
                    continue

        # Название — тоже несколькими способами, с запасным вариантом из URL.
        title = ""
        for pattern in (
            r'<h1[^>]*data-auto="title"[^>]*>(.*?)</h1>',
            r'<title[^>]*>(.*?) - Яндекс Маркет</title>',
            r'<meta[^>]*property="og:title"[^>]*content="([^"]+)"',
        ):
            m = re.search(pattern, html)
            if m:
                title = re.sub(r"<[^>]+>", "", m.group(1)).strip()
                if len(title) < 5 or "@" in title or "marketfront" in title:
                    title = ""
                break
        if not title:
            title = generate_title_from_url(clean_url)

        if price <= 0:
            logger.info("Цена на странице не найдена")
            return {"success": False, "error": "Цена не найдена. Маркет мог отдать страницу без цены или капчу."}

        pid = re.search(r"/(\d+)(?:/|$)", clean_url)
        return {
            "success": True,
            "price": price,
            "title": title,
            "url": clean_url,
            "product_id": pid.group(1) if pid else re.sub(r"\D", "", clean_url)[-10:] or "yamarket",
            "source": "yamarket",
        }

    except Exception as e:
        logger.exception("Ошибка парсинга Яндекс.Маркета")
        return {"success": False, "error": str(e)}


def generate_title_from_url(url: str):
    """Запасное название из адреса, если на странице его не нашлось."""
    match = re.search(r"/card/([^/]+)/", url)
    return match.group(1).replace("-", " ").title() if match else "Товар Яндекс.Маркет"
