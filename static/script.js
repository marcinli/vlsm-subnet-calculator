// Załadowanie plików dźwiękowych
const clickSound = new Audio('/static/sounds/click.mp3');
const errorSound = new Audio('/static/sounds/error.mp3');

// Funkcja odtwarzania dźwięku kliknięcia
function playClickSound() {
    clickSound.play();
}

// Funkcja odtwarzania dźwięku błędu
function playErrorSound() {
    errorSound.play();
}

// Funkcja walidacji formularza
function validateForm() {
    const networkInput = document.querySelector('#network');
    const hostsInput = document.querySelector('#hosts');
    const errorModal = document.querySelector('#error-modal');
    const errorMessage = document.querySelector('#error-message');

    let errors = [];
    const networkRegex = /^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\/\d{1,2}$/; // Walidacja adresu sieci
    const hostsRegex = /^\s*\d+(\s*,\s*\d+)*\s*$/; // Poprawiona walidacja hostów

    // Walidacja adresu sieci
    if (!networkRegex.test(networkInput.value)) {
        errors.push('Niepoprawny format adresu sieci (np. 192.168.1.0/24).');
    }

    // Walidacja liczby hostów
    if (!hostsRegex.test(hostsInput.value)) {
        errors.push('Liczba hostów powinna być liczbami oddzielonymi przecinkami (np. 50,20,10).');
    }

    if (errors.length > 0) {
        errorMessage.textContent = errors.join('\n'); // Wyświetlenie błędów w okienku
        errorModal.style.display = 'block'; // Pokazanie modala
        playErrorSound(); // Odtworzenie dźwięku błędu
    } else {
        playClickSound(); // Odtworzenie dźwięku kliknięcia
        document.querySelector('#vlsm-form').submit(); // Prześlij formularz
    }
}

// Funkcja zamykania modala błędu
function closeModal() {
    document.querySelector('#error-modal').style.display = 'none';
}

// Dodanie dźwięków do przycisków eksportu
document.addEventListener('DOMContentLoaded', function () {
    const exportTxtButton = document.querySelector('#export_txt');
    const exportPdfButton = document.querySelector('#export_pdf');

    if (exportTxtButton) {
        exportTxtButton.addEventListener('click', playClickSound);
    }
    if (exportPdfButton) {
        exportPdfButton.addEventListener('click', playClickSound);
    }
});
