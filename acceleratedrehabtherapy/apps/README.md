acceleratedrehabtherapy\apps\README.md

# Django Applications

This directory contains all the Django applications for the Accelerated Rehab Therapy website. Each app is designed to handle specific functionality of the website.

## Main App

The main app handles core website functionality and home page management.

### Models
- `MainPageConfig`: Manages home page content including:
  - Title and description
  - Main content (CKEditor)
  - Hero section content
  - Call-to-action buttons

### Views
- `MainPageView`: Class-based view for rendering the home page
  - Implements ListView for content management
  - Handles page configuration
  - Manages template context

### Templates
Located in `main/templates/main/`:
- `home.html`: Home page template featuring:
  - Full-screen hero slider
  - Alpine.js-powered image transitions
  - Progress bar animation
  - Responsive design with Tailwind CSS

### Static Files
Located in `static/`:
- Images:
  - Slider images (01.jpg through 04.jpg)
  - Logo and branding assets
- Styles:
  - Tailwind CSS utilities
  - Custom animations
- JavaScript:
  - Alpine.js components
  - HTMX interactions

## Theme App

Manages the site's visual appearance and Tailwind CSS configuration.

### Features
- Tailwind CSS configuration
- Custom color scheme:
  - Yellow accent colors
  - Dark navy backgrounds
  - Professional typography
- Responsive breakpoints
- Component styling

### Static Source
- Contains Tailwind source files
- NPM configuration
- Build scripts

## Directory Structure
```
apps/
├── main/                      # Main website functionality
│   ├── migrations/           # Database migrations
│   ├── static/               # App-specific static files
│   ├── templates/            # App templates
│   │   └── main/            # Main app templates
│   │       └── home.html    # Home page template
│   ├── admin.py             # Admin interface configuration
│   ├── apps.py              # App configuration
│   ├── models.py            # Database models
│   ├── urls.py              # URL routing
│   └── views.py             # View logic
└── README.md                 # This file
```

## Dependencies

### Main App
- django-ckeditor-5: Rich text editing
- Pillow: Image handling
- django-htmx: Dynamic interactions
- django-compressor: Asset compression
- WhiteNoise: Static file serving

### Theme App
- django-tailwind: CSS framework
- django-compressor: Asset optimization

## Future Apps

Planned applications for future development:
1. `services`: Physical therapy services
2. `blog`: Health and wellness articles
3. `contact`: Contact form and location info
4. `appointments`: Scheduling system
5. `testimonials`: Patient reviews

## Development Guidelines

1. Keep apps focused and single-purpose
2. Follow Django's app structure conventions
3. Document all models and views
4. Write tests for critical functionality
5. Use type hints in Python code
6. Follow PEP 8 style guidelines
7. Maintain responsive design principles
8. Optimize for performance