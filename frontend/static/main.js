// Слушаем события HTMX
document.body.addEventListener('htmx:configRequest', function(evt) {
    console.log("Отправляем HTMX запрос на: " + evt.detail.path);
});