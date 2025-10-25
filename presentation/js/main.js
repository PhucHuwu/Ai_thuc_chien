document.addEventListener('DOMContentLoaded', () => {
    const slides = document.querySelectorAll('.slide');
    const prevBtn = document.getElementById('prevBtn');
    const nextBtn = document.getElementById('nextBtn');
    const slideCounter = document.getElementById('slide-counter');
    let currentSlide = 0;

    function showSlide(index) {
        slides.forEach((slide, i) => {
            slide.classList.remove('active');
            if (i === index) {
                slide.classList.add('active');
            }
        });
        slideCounter.textContent = `${index + 1} / ${slides.length}`;
        currentSlide = index;
    }

    function nextSlide() {
        let next = currentSlide + 1;
        if (next >= slides.length) {
            next = 0; // Loop back to the first slide
        }
        showSlide(next);
    }

    function prevSlide() {
        let prev = currentSlide - 1;
        if (prev < 0) {
            prev = slides.length - 1; // Loop back to the last slide
        }
        showSlide(prev);
    }

    nextBtn.addEventListener('click', nextSlide);
    prevBtn.addEventListener('click', prevSlide);

    // Keyboard navigation
    document.addEventListener('keydown', (e) => {
        if (e.key === 'ArrowRight') {
            nextSlide();
        } else if (e.key === 'ArrowLeft') {
            prevSlide();
        }
    });

    // Initialize the first slide
    showSlide(0);
    loadSlideContent(); // Function to load content dynamically
});

async function loadSlideContent() {
    for (let i = 1; i <= 10; i++) {
        try {
            const response = await fetch(`slides/slide${i}.html`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const content = await response.text();
            document.getElementById(`slide${i}`).innerHTML = content;
        } catch (error) {
            console.error(`Could not load slide ${i}:`, error);
            document.getElementById(`slide${i}`).innerHTML = `<div class="error"><h1>Lỗi</h1><p>Không thể tải nội dung cho slide ${i}.</p></div>`;
        }
    }
}
