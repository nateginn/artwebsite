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
def auto_injury(request):
    """Auto injury page view"""
    return render(request, 'main/auto_injury.html')

@require_GET
def home(request):
    """Main home page view"""
    context = {
        'google_maps_api_key': settings.GOOGLE_MAPS_API_KEY
    }
    return render(request, 'main/home.html', context)

@require_GET
def chiropractor(request):
    """Chiropractor page view"""
    return render(request, 'main/chiropractor.html')