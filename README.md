# artwebsite\README.md

# Accelerated Rehab Therapy Website

A modern, Django-based website for Accelerated Rehab Therapy, built with Python 3.12 and modern web technologies.

## 🚀 Technologies

- Python 3.12
- Django 5.1.4
- Tailwind CSS
- HTMX
- Alpine.js
- Django CKEditor 5
- Django Jazzmin (Admin Interface)
- WhiteNoise (Static Files)

## 📋 Prerequisites

- Python 3.12+
- Poetry (Python package manager)
- Node.js and npm (for Tailwind CSS)

## 🛠️ Setup

1. Clone the repository:
   ```bash
   git clone [repository-url]
   cd artwebsite
   ```

2. Install Python dependencies:
   ```bash
   poetry install
   ```

3. Install Node.js dependencies:
   ```bash
   cd acceleratedrehabtherapy/theme/static_src
   npm install
   ```

4. Set up the database:
   ```bash
   poetry run python manage.py migrate
   ```

5. Create a superuser:
   ```bash
   poetry run python manage.py createsuperuser
   ```

6. Start the development server:
   ```bash
   poetry run python manage.py runserver
   ```

## 📁 Project Structure

```
artwebsite/
├── acceleratedrehabtherapy/    # Main project directory
│   ├── apps/                   # Django applications
│   │   └── main/              # Main app (home page, core features)
│   ├── static/                 # Project-wide static files
│   │   └── img/               # Image assets
│   │       ├── slider/        # Home page slider images
│   │       └── art-logo.jpg   # Site logo
│   ├── templates/             # Project-wide templates
│   │   ├── base.html         # Base template
│   │   └── includes/         # Reusable components
│   │       ├── header.html   # Site header
│   │       └── footer.html   # Site footer
│   ├── theme/                 # Tailwind configuration
│   └── settings.py           # Project settings
├── media/                     # User-uploaded files
├── poetry.lock               # Poetry dependencies lock file
└── pyproject.toml            # Project configuration
```

## 🔧 Development

- Run Tailwind in watch mode:
  ```bash
  poetry run python manage.py tailwind start
  ```

- Collect static files:
  ```bash
  poetry run python manage.py collectstatic
  ```

## 🎯 Current Features

1. Modern Responsive Header
   - Navigation menu
   - Logo
   - Contact information
   - Mobile-friendly design

2. Dynamic Home Page
   - Full-screen hero slider with 4 images
   - Automatic transitions with progress bar
   - Call-to-action buttons
   - Modern typography and layout

3. Admin Interface
   - Django Jazzmin theme
   - CKEditor 5 for rich text editing
   - User-friendly content management

## 🚀 Deployment

1. Set `DEBUG=False` in production
2. Configure proper database settings
3. Set up proper static files serving (WhiteNoise configured)
4. Configure proper media files handling
5. Set up proper security settings

## 📝 License

This project is proprietary and confidential.

## 🤝 Contributing

For internal development team only. Please follow the project's coding standards and submit pull requests for review.
