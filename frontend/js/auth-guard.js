/**
 * Auth Guard - перевірка авторизації
 * Підключити на всіх захищених сторінках
 */

if (!api.isAuthenticated()) {
    window.location.href = 'login.html';
}
