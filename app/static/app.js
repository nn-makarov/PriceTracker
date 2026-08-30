const API_BASE = '';

async function searchProducts(query) {
    console.log('Full query:', query);
    console.log('Query length:', query.length);
    console.log('Contains market.yandex.ru:', query.includes('market.yandex.ru'));
    try {
        const response = await fetch(`/api/search?query=${encodeURIComponent(query)}`);
        const data = await response.json();
        
        if (data.results && data.results.length > 0) {
            displayResults(data.results);
        } else {
            showNotification((data.error || 'Товары не найдены') + ' Впишите цену вручную ниже.', 'error');
        }
    } catch (error) {
        console.error('Search error:', error);
        showNotification('Ошибка поиска', 'error');
    }
}

function displayResults(products) {
    const resultsDiv = document.getElementById('results');
    
    resultsDiv.innerHTML = products.map(product => `
        <div class="product-card">
            <div class="product-title">${product.title}</div>
            <div class="product-price">
                ${product.price} ₽
            </div>
            <div style="font-size: 12px; color: #666; margin-bottom: 10px;">
                Источник: ${product.source || 'yandex'}
            </div>
            <button class="track-btn" onclick="trackProduct('${product.product_id}', '${product.title.replace(/'/g, "\\'")}', ${product.price}, '${product.url}', '${product.source || 'yandex'}')">
                📌 Отслеживать цену
            </button>
        </div>
    `).join('');
}

async function trackProduct(productId, title, price, url, source) {
    try {
        console.log('🟡 Tracking product data:', {productId, title, price, url, source});
        
        const requestBody = {
            url: url,
            title: title,
            current_price: price
        };
        console.log('🟡 Request body:', requestBody);
        
        const response = await fetch('/api/track', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestBody)
        });
        
        console.log('🟡 Response status:', response.status);
        
        if (response.ok) {
            const result = await response.json();
            console.log('✅ Product tracked:', result);
            showNotification('Товар добавлен для отслеживания!', 'success');
            loadTrackedProducts();
        } else {
            const error = await response.json();
            console.error('❌ Track error:', error);
            showNotification(error.detail || 'Ошибка добавления', 'error');
        }
    } catch (error) {
        console.error('❌ Track failed:', error);
        showNotification('Ошибка соединения', 'error');
    }
}


// Удаление товара со всей историей цен, с подтверждением.
async function deleteProduct(id, title) {
    if (!confirm(`Удалить «${title}» вместе с историей цен?`)) {
        return;
    }
    try {
        const response = await fetch(`/api/products/${id}`, { method: 'DELETE' });
        if (response.ok) {
            showNotification('Товар удалён', 'success');
            loadTrackedProducts();
        } else {
            const error = await response.json();
            showNotification(error.detail || 'Не удалось удалить', 'error');
        }
    } catch (error) {
        showNotification('Ошибка соединения', 'error');
    }
}

async function loadTrackedProducts() {
    try {
        const response = await fetch('/api/tracked-products');
        if (response.ok) {
            const products = await response.json();
            displayTrackedProducts(products);
        }
    } catch (error) {
        console.error('Load products error:', error);
    }
}

function showNotification(message, type = 'info') {
    if (typeof message === 'object') {
        message = JSON.stringify(message);
    }
    
    const prefix = type === 'error' ? '❌ ОШИБКА: ' : 
                   type === 'success' ? '✅ ' : 'ℹ️ ';
    alert(prefix + message);
}

function displayTrackedProducts(products) {
    const container = document.getElementById('trackedProducts');
    if (!container) {
        console.error('❌ trackedProducts container not found');
        return;
    }
    
    console.log('📦 Displaying tracked products:', products);
    
    if (products.length === 0) {
        container.innerHTML = '<p>Нет отслеживаемых товаров</p>';
        return;
    }
    
    container.innerHTML = products.map(product => `
        <div class="tracked-product" style="border: 1px solid #ddd; padding: 15px; margin: 10px 0; border-radius: 8px;">
            <h4 style="margin: 0 0 10px 0;">${product.title}</h4>
            <p style="margin: 5px 0; font-size: 18px; font-weight: bold; color: #2c5aa0;">
                Текущая цена: ${product.current_price} руб.
            </p>
            <p style="margin: 5px 0; color: #666; font-size: 14px;">
                URL: <a href="${product.url}" target="_blank">${product.url}</a>
            </p>
            <p style="margin: 5px 0; color: #888; font-size: 12px;">
                ID: ${product.id}
            </p>
            <button onclick="deleteProduct(${product.id}, '${product.title.replace(/'/g, "\\'")}')"
                    style="background: #d9534f; color: white; border: none; padding: 6px 12px; border-radius: 6px; cursor: pointer; font-size: 13px;">
                🗑 Удалить
            </button>
        </div>
    `).join('');
    
    console.log('✅ Tracked products displayed');
}


// Ручное добавление товара: когда парсер не смог достать цену с Маркета,
// пользователь смотрит её на сайте и вводит сам. Использует тот же
// /api/track, что и кнопка автоматического отслеживания.
async function addManual() {
    const url = document.getElementById('manualUrl').value.trim();
    const title = document.getElementById('manualTitle').value.trim();
    const price = parseFloat(document.getElementById('manualPrice').value);

    if (!url || !title || isNaN(price)) {
        showNotification('Заполните ссылку, название и цену', 'error');
        return;
    }

    try {
        const response = await fetch('/api/track', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url, title, current_price: price })
        });

        if (response.ok) {
            showNotification('Товар добавлен!', 'success');
            document.getElementById('manualUrl').value = '';
            document.getElementById('manualTitle').value = '';
            document.getElementById('manualPrice').value = '';
            loadTrackedProducts();
        } else {
            const error = await response.json();
            showNotification(error.detail || 'Ошибка добавления', 'error');
        }
    } catch (error) {
        showNotification('Ошибка соединения', 'error');
    }
}

document.addEventListener('DOMContentLoaded', function() {
    loadTrackedProducts();
});