// main/static/main/js/main.js
document.addEventListener('DOMContentLoaded', function() {
    // Content height check for header styling
    const content = document.getElementById('content');
    if (content && content.offsetHeight < 504) {
        document.querySelector('.base-header__wrapper')?.classList.add('no-pseudo');
    }

    // Main slider functionality
    class MainSlider {
        constructor() {
            this.slides = document.querySelectorAll('.main-slider__image');
            if (!this.slides.length) return;
            
            this.currentSlide = 0;
            this.slideInterval = setInterval(() => this.nextSlide(), 3000);
        }

        nextSlide() {
            this.slides[this.currentSlide].classList.remove('isShow');
            this.currentSlide = (this.currentSlide + 1) % this.slides.length;
            this.slides[this.currentSlide].classList.add('isShow');
        }
    }

    // Initialize slider if it exists
    if (document.querySelector('.main-slider')) {
        new MainSlider();
    }
});