# Accelerated Rehab Therapy Website

A modern, Django-based website for Accelerated Rehab Therapy, featuring a complete CI/CD pipeline, PostgreSQL database, and production-ready deployment.

## 🚀 Technologies

### Backend
- Python 3.12
- Django 5.1.4
- PostgreSQL
- Gunicorn
- Nginx
- Poetry (Dependency Management)

### Frontend
- Tailwind CSS
- HTMX
- Alpine.js
- Django CKEditor 5
- Django Jazzmin (Admin Interface)
- WhiteNoise (Static Files)

## 📋 Prerequisites

### Development
- Python 3.12+
- Poetry (Python package manager)
- Node.js and npm (for Tailwind CSS)
- Git

### Production
- Ubuntu Server (tested on 22.04 LTS)
- Nginx
- PostgreSQL
- Systemd (for Gunicorn service)

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

## 🎯 Features

### Website
- Modern responsive design with mobile-first approach
- Dynamic content management through Django admin
- SEO-optimized pages
- Fast loading with optimized static files

### Admin Interface
- Customized Django Jazzmin theme
- Rich text editing with CKEditor 5
- User and permission management
- Activity logs

### Development
- Complete CI/CD pipeline
- Automated testing
- Code quality checks
- Environment-specific settings

### Security
- Production-ready security settings
- Environment-based configuration
- Secure password hashing
- CSRF and XSS protection

## 🚀 Deployment

The project includes GitHub Actions for CI/CD. Pushing to the `main` branch triggers automatic deployment.

### Production Server Setup

1. **Server Requirements**:
   - Ubuntu 22.04 LTS
   - Python 3.12
   - PostgreSQL
   - Nginx
   - Git

2. **Environment Variables**
   Create a `.env` file in the project root with:
   ```
   DEBUG=False
   SECRET_KEY=your-secret-key
   ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com,server-ip
   DATABASE_URL=postgres://user:password@localhost/dbname
   EMAIL_HOST=smtp.gmail.com
   EMAIL_PORT=587
   EMAIL_USE_TLS=True
   EMAIL_HOST_USER=your-email@gmail.com
   EMAIL_HOST_PASSWORD=your-app-password
   DEFAULT_FROM_EMAIL=your-email@gmail.com
   SERVER_EMAIL=your-email@gmail.com
   ```

3. **CI/CD Pipeline**
   - Automatic testing on push to `main`
   - Automatic deployment on successful tests
   - Environment variable management through GitHub Secrets

4. **Manual Deployment Steps** (if needed):
   ```bash
   # Install dependencies
   poetry install --no-interaction
   
   # Run migrations
   poetry run python manage.py migrate
   
   # Collect static files
   poetry run python manage.py collectstatic --noinput
   
   # Restart Gunicorn
   sudo systemctl restart gunicorn
   ```

## 📝 License

This project is proprietary and confidential.

## 🤝 Contributing

For internal development team only. Please follow the project's coding standards and submit pull requests for review.

### Development Workflow

1. Create a new branch for your feature:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes and test locally

3. Commit your changes with a descriptive message:
   ```bash
   git add .
   git commit -m "Add your feature description"
   ```

4. Push to the repository:
   ```bash
   git push origin feature/your-feature-name
   ```

5. Open a pull request to the `main` branch

## 📞 Support

For support, please contact the development team at [growyourbiz4ever@gmail.com].
