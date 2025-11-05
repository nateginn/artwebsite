# acceleratedrehabtherapy/apps/main/views.py

import hashlib
import json
import os
import requests
from django.conf import settings
from django.core.cache import cache
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.cache import cache_page
from django.views.decorators.http import require_GET
from django.views.decorators.http import require_http_methods

@require_GET
def home(request):
    """Main home page view"""
    context = {
        'google_maps_api_key': settings.GOOGLE_MAPS_API_KEY
    }
    return render(request, 'main/home.html', context)

def generate_review_hash(review_text, author):
    """Generate a unique hash for a review based on content and author"""
    content = f"{review_text}{author}".encode('utf-8')
    return hashlib.md5(content).hexdigest()

def get_google_reviews():
    cache_key = 'google_reviews'
    cached_reviews = cache.get(cache_key)
    
    if cached_reviews:
        return cached_reviews

    api_key = os.getenv('GOOGLE_MAPS_API_KEY')
    place_id = os.getenv('GOOGLE_PLACE_ID')
    
    if not api_key or not place_id:
        return []

    url = f'https://maps.googleapis.com/maps/api/place/details/json?place_id={place_id}&fields=reviews&key={api_key}'
    
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        
        if 'result' in data:
            reviews = data['result'].get('reviews', [])
            filtered_reviews = [
                {
                    'id': generate_review_hash(review['text'], review['author_name']),
                    'author': review['author_name'],
                    'text': review['text'],
                    'rating': review['rating'],
                    'time': review['time'],
                    'type': 'Google Review',
                    'source': 'google',
                    'profession': 'Customer'
                }
                for review in reviews
                if review['rating'] >= 4
            ]
            
            if filtered_reviews:
                cache.set(cache_key, filtered_reviews, 43200)  # 12 hours
            return filtered_reviews
        else:
            return []
            
    except Exception:
        return []

def get_legacy_reviews():
    try:
        json_path = os.path.join(settings.BASE_DIR, 'acceleratedrehabtherapy','data', 'legacy_reviews.json')
        if not os.path.exists(json_path):
            return []
            
        with open(json_path) as f:
            data = json.load(f)
            reviews = data.get('legacy_reviews', [])
            formatted_reviews = [
                {
                    'id': generate_review_hash(review['text'], review['author']),
                    'author': review['author'],
                    'text': review['text'],
                    'rating': review['rating'],
                    'type': review.get('type', 'Patient'),
                    'source': 'legacy',
                    'profession': review.get('profession', '-')
                }
                for review in reviews
            ]
            return formatted_reviews
    except Exception:
        return []

def merge_reviews(google_reviews, legacy_reviews):
    """Merge reviews, removing duplicates based on content hash"""
    seen_hashes = set()
    merged_reviews = []
    
    # Add Google reviews first (they take precedence)
    for review in google_reviews:
        seen_hashes.add(review['id'])
        merged_reviews.append(review)
    
    # Add legacy reviews only if they're unique
    for review in legacy_reviews:
        if review['id'] not in seen_hashes:
            seen_hashes.add(review['id'])
            merged_reviews.append(review)
    
    return merged_reviews

@require_GET
@cache_page(60 * 15)  # Cache for 15 minutes
def reviews_api(request):
    """API endpoint for fetching combined Google and legacy reviews"""
    try:
        # Get legacy reviews first
        legacy_reviews = get_legacy_reviews()
        
        # If we have Google API credentials, try to get Google reviews
        if os.getenv('GOOGLE_MAPS_API_KEY') and os.getenv('GOOGLE_PLACE_ID'):
            google_reviews = get_google_reviews()
            all_reviews = merge_reviews(google_reviews, legacy_reviews)
        else:
            all_reviews = legacy_reviews
        
        # Sort reviews by rating and time
        if all_reviews:
            all_reviews.sort(key=lambda x: (-x['rating'], -x.get('time', 0)))
        
        return JsonResponse({
            'status': 'success',
            'reviews': all_reviews
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

@require_GET
def test_google_reviews(request):
    """Temporary endpoint to test Google Reviews API only"""
    try:
        api_key = os.getenv('GOOGLE_MAPS_API_KEY')
        place_id = os.getenv('GOOGLE_PLACE_ID')
        
        if not api_key or not place_id:
            return JsonResponse({
                'status': 'error',
                'message': 'Missing API credentials'
            }, status=400)
            
        google_reviews = get_google_reviews()
        
        return JsonResponse({
            'status': 'success',
            'reviews': google_reviews
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

@require_GET
def home(request):
    """Main home page view"""
    context = {
        'google_maps_api_key': settings.GOOGLE_MAPS_API_KEY
    }
    return render(request, 'main/home.html', context)

CHIROPRACTIC_SERVICES = [
    'AUTO INJURY',
    'WORK COMP INJURY',
    'SPORTS INJURY',
    'HEAD INJURY',
    'BACK INJURY',
    'NECK INJURY',
    'HIP INJURY',
    'KNEE INJURY',
    'SHOULDER INJURY'
]

@require_GET
def work_comp(request):
    """Work comp page view"""
    context = {
        'services': CHIROPRACTIC_SERVICES,
        'hide_margin': False,  # Set to True if you want to hide the top margin
        'meta_title': 'Work Comp Injury Care in Greeley & Denver | Accelerated Rehab Therapy'
    }
    return render(request, 'main/work_comp.html', context)

@require_GET
def auto_injury(request):
    """Auto injury page view"""
    context = {
        'services': CHIROPRACTIC_SERVICES,
        'hide_margin': False,
        'meta_title': 'Auto Injury Treatment in Greeley & Denver | Accelerated Rehab Therapy'
    }
    return render(request, 'main/auto_injury.html', context)

@require_GET
def chiropractor(request):
    """Chiropractor page view"""
    context = {
        'meta_title': 'Chiropractor Services in Greeley & Denver | Accelerated Rehab Therapy'
    }
    return render(request, 'main/chiropractor.html', context)

@require_GET
def massage(request):
    """Massage page view"""
    context = {
        'meta_title': 'Therapeutic Massage in Greeley & Denver | Accelerated Rehab Therapy'
    }
    return render(request, 'main/massage.html', context)

@require_GET
def acupuncture(request):
    """Acupuncture page view"""
    context = {
        'meta_title': 'Acupuncture Treatment in Greeley & Denver | Accelerated Rehab Therapy'
    }
    return render(request, 'main/acupuncture.html', context)

@require_GET
def physical_therapy(request):
    """Physical therapy page view"""
    context = {
        'meta_title': 'Physical Therapy in Greeley & Denver | Accelerated Rehab Therapy'
    }
    return render(request, 'main/physical_therapy.html', context)

import logging
import sys
from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.mail import send_mail, BadHeaderError
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.http import require_http_methods, require_GET

# Debug print to verify module loading
print("\n=== VIEWS.PY LOADED ===")
print(f"Current module: {__name__}")
print(f"File: {__file__}")

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger('contact_form')

@require_http_methods(["GET", "POST"])
def contact(request):
    logger = logging.getLogger('contact_form')
    
    if request.method == "POST":
        # Get form data
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone', '')
        message = request.POST.get('message', '')
        
        # Basic validation
        if not all([name, email, message]):
            messages.error(request, 'Please fill in all required fields.')
            logger.warning("Form validation failed - missing required fields")
            return redirect('contact')
            
        logger.info(f"New contact form submission from {name} ({email})")
        
        # Prepare email content
        subject = f'New Contact Form Submission from {name}'
        email_message = f"""
        New contact form submission:
        
        Name: {name}
        Email: {email}
        Phone: {phone}
        
        Message:
        {message}
        """
        
        try:
            send_mail(
                subject=subject,
                message=email_message.strip(),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.EMAIL_HOST_USER],
                fail_silently=False,
            )
            logger.info(f"Contact form email sent successfully to {settings.EMAIL_HOST_USER}")
            messages.success(request, 'Thank you for your message. We will get back to you soon!')
            return redirect('contact')
            
        except Exception as e:
            logger.error(f"Error sending contact form email: {str(e)}")
            messages.error(request, 'There was an error sending your message. Please try again later.')
            # Log the error with stack trace
            logger.exception("Error sending email")
            messages.error(request, 'There was an error sending your message. Please try again.')
    
    # For GET requests or if there was an error
    logger.debug("Rendering contact form template")
    context = {
        'meta_title': 'Contact Us in Greeley & Denver | Accelerated Rehab Therapy'
    }
    return render(request, 'main/contact.html', context)

@require_GET
def about(request):
    """About page view"""
    context = {
        'meta_title': 'About Accelerated Rehab Therapy | Greeley & Denver'
    }
    return render(request, 'main/about_us.html', context)

@require_GET
def resources(request):
    """Resources page view"""
    context = {
        'meta_title': 'Patient Resources & Information | Accelerated Rehab Therapy'
    }
    return render(request, 'main/resources.html', context)

@require_GET
def es_info(request):
    """Spanish information page summarizing clinic services (not linked in top menu)."""
    html = """
    <!DOCTYPE html>
    <html lang=\"es\">
    <head>
        <meta charset=\"utf-8\">
        <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
        <title>A.R.T. | Información en Español</title>
        <meta name=\"description\" content=\"Hablamos Español. Clínica de rehabilitación y quiropráctica en Greeley y Denver: lesiones de auto y trabajo, terapia física, masaje y acupuntura.\">
        <style>
            body { font-family: system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif; margin: 0; color: #0b1320; }
            header { background: #001524; color: #fff; padding: 18px 16px; }
            header a { color: #ffd166; text-decoration: none; font-weight: 700; }
            main { padding: 24px 16px; max-width: 880px; margin: 0 auto; line-height: 1.6; }
            h1 { font-size: 1.75rem; margin: 0 0 8px; }
            h2 { font-size: 1.25rem; margin-top: 24px; }
            .pill { display: inline-block; background: #f59e0b; color: #000; font-weight: 700; padding: 4px 10px; border-radius: 9999px; font-size: 0.8rem; }
            .grid { display: grid; grid-template-columns: 1fr; gap: 12px; }
            .card { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 12px 14px; }
            .footer { font-size: 0.85rem; color: #475569; margin-top: 28px; }
            @media (min-width: 700px) { .grid { grid-template-columns: repeat(3, 1fr); } }
        </style>
    </head>
    <body>
        <header>
            <div style=\"max-width: 1100px; margin: 0 auto; display: flex; align-items: center; justify-content: space-between;\">
                <div>
                    <div class=\"pill\">Hablamos Español</div>
                    <div style=\"margin-top:6px; font-size: 0.95rem;\">Accelerated Rehab Therapy — Greeley & Denver</div>
                </div>
                <nav><a href=\"/\">Inicio</a></nav>
            </div>
        </header>
        <main>
            <h1>Información en Español</h1>
            <p>
                En Accelerated Rehab Therapy, apoyamos a nuestra comunidad hispana con atención en Español. 
                Ofrecemos cuidado quiropráctico, terapia física, masaje terapéutico y acupuntura para 
                lesiones de auto, lesiones de trabajo y dolor crónico.
            </p>

            <h2>Servicios Principales</h2>
            <div class=\"grid\">
                <div class=\"card\"><strong>Lesiones de Auto</strong><br>Evaluación, documentación y tratamiento para dolor de cuello (latigazo), espalda y tejidos blandos.</div>
                <div class=\"card\"><strong>Lesiones de Trabajo</strong><br>Atención coordinada para reclamos de Work Comp y regreso seguro al trabajo.</div>
                <div class=\"card\"><strong>Terapia Física</strong><br>Planes personalizados para mejorar movilidad, fuerza y reducir el dolor.</div>
                <div class=\"card\"><strong>Quiropráctica</strong><br>Ajustes y rehabilitación para aliviar dolor y mejorar la función.</div>
                <div class=\"card\"><strong>Masaje Terapéutico</strong><br>Alivio de tensión muscular y apoyo a la recuperación.</div>
                <div class=\"card\"><strong>Acupuntura</strong><br>Complemento para manejo de dolor y bienestar general.</div>
            </div>

            <h2>Ubicaciones y Citas</h2>
            <p>
                Greeley: <a href=\"tel:+19703241750\">970-324-1750</a><br>
                Denver: <a href=\"tel:+17206042792\">720-604-2792</a>
            </p>
            <p class=\"footer\">¿Prefiere atención en Español? Llámenos y con gusto le ayudamos.</p>
        </main>
    </body>
    </html>
    """
    return HttpResponse(html)
