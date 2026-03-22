// Dark mode toggle
function toggleDarkMode() {
    var html = document.documentElement;
    var current = html.getAttribute('data-theme');
    var newTheme = current === 'dark' ? 'light' : 'dark';
    html.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);

    // Toggle icons
    var moon = document.querySelector('.icon-moon');
    var sun = document.querySelector('.icon-sun');
    if (moon && sun) {
        if (newTheme === 'dark') {
            moon.style.display = 'none';
            sun.style.display = 'block';
        } else {
            moon.style.display = 'block';
            sun.style.display = 'none';
        }
    }
}

document.addEventListener('DOMContentLoaded', function() {
    // Load saved theme
    var saved = localStorage.getItem('theme');
    if (saved) {
        document.documentElement.setAttribute('data-theme', saved);
        var moon = document.querySelector('.icon-moon');
        var sun = document.querySelector('.icon-sun');
        if (moon && sun && saved === 'dark') {
            moon.style.display = 'none';
            sun.style.display = 'block';
        }
    }

    // Auto-hide alerts after 5 seconds
    var alerts = document.querySelectorAll('.alert');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            alert.style.opacity = '0';
            alert.style.transition = 'opacity 0.5s';
            setTimeout(function() { alert.remove(); }, 500);
        }, 5000);
    });
});
