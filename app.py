import os
import requests
import time
import concurrent.futures
import re
from flask import Flask, render_template, request, jsonify, url_for, redirect
from bs4 import BeautifulSoup
import threading
import uuid
import json
from datetime import datetime
import logging

app = Flask(__name__)

# Add website name and metadata for SEO
SITE_NAME = "DeployProbe"
SITE_TAGLINE = "Deployed it? Let's see if it survives the storm."
SITE_DESCRIPTION = "Test if your deployed website can handle traffic storms and analyze code quality for scalability. Perfect for developers preparing for high-traffic scenarios."
SITE_KEYWORDS = "load testing, website performance, high traffic, scalability testing, code quality, deployment analysis"

# Add a dictionary to store test progress
test_progress = {}

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler()]
)

def perform_load_test(url, num_requests=100, concurrency=10):
    """Simulate load testing with concurrent requests"""
    success_count = 0
    failed_count = 0
    response_times = []
    status_codes = {}
    errors = {}
    
    def make_request(url):
        try:
            start_time = time.time()
            response = requests.get(url, timeout=5)
            end_time = time.time()
            return {
                'status_code': response.status_code,
                'response_time': end_time - start_time,
                'success': 200 <= response.status_code < 400
            }
        except Exception as e:
            err_type = type(e).__name__
            return {
                'status_code': None,
                'response_time': None,
                'success': False,
                'error': err_type
            }
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [executor.submit(make_request, url) for _ in range(num_requests)]
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            if result['success']:
                success_count += 1
                response_times.append(result['response_time'])
                
                # Track status codes
                status_code = result['status_code']
                if status_code in status_codes:
                    status_codes[status_code] += 1
                else:
                    status_codes[status_code] = 1
            else:
                failed_count += 1
                # Track error types
                if 'error' in result:
                    error_type = result['error']
                    if error_type in errors:
                        errors[error_type] += 1
                    else:
                        errors[error_type] = 1
    
    if success_count > 0:
        avg_response_time = sum(response_times) / len(response_times)
        max_response_time = max(response_times) if response_times else 0
        min_response_time = min(response_times) if response_times else 0
        
        # Calculate percentiles (90th and 95th)
        sorted_times = sorted(response_times)
        p90_index = int(len(sorted_times) * 0.9)
        p95_index = int(len(sorted_times) * 0.95)
        p90_time = sorted_times[p90_index] if p90_index < len(sorted_times) else max_response_time
        p95_time = sorted_times[p95_index] if p95_index < len(sorted_times) else max_response_time
    else:
        avg_response_time = max_response_time = min_response_time = 0
        p90_time = p95_time = 0
    
    success_rate = (success_count / num_requests) * 100 if num_requests > 0 else 0
    
    # Calculate requests per second
    total_time = sum(response_times) if response_times else 0
    requests_per_second = success_count / total_time if total_time > 0 else 0
    
    # Analyze result quality
    performance_rating = "Excellent"
    if success_rate < 90:
        performance_rating = "Poor"
    elif success_rate < 95:
        performance_rating = "Fair"
    elif success_rate < 98:
        performance_rating = "Good"
        
    if avg_response_time > 3:
        performance_rating = "Poor"
    elif avg_response_time > 1.5 and performance_rating != "Poor":
        performance_rating = "Fair"
    
    # Enhanced analysis for high traffic capacity
    estimated_capacity = 0
    capacity_rating = ""
    capacity_message = ""
    
    # Calculate estimated capacity based on response metrics
    if success_rate > 95 and avg_response_time < 1.0:
        # Excellent performance, can likely handle high traffic
        estimated_capacity = int(requests_per_second * 60) * 10  # Estimate for 10 minutes of traffic
        capacity_rating = "Excellent"
        capacity_message = f"Can likely handle {estimated_capacity:,}+ concurrent users"
    elif success_rate > 90 and avg_response_time < 2.0:
        # Good performance
        estimated_capacity = int(requests_per_second * 45) * 5  # More conservative estimate
        capacity_rating = "Good"
        capacity_message = f"Can likely handle {estimated_capacity:,}+ concurrent users"
    elif success_rate > 80 and avg_response_time < 3.5:
        # Average performance
        estimated_capacity = int(requests_per_second * 30) * 3
        capacity_rating = "Average"
        capacity_message = f"Can handle approximately {estimated_capacity:,} concurrent users"
    else:
        # Poor performance
        estimated_capacity = int(requests_per_second * 15)
        capacity_rating = "Limited"
        capacity_message = f"May struggle with more than {estimated_capacity:,} concurrent users"
    
    # Determine if site can handle 5000-6000 users
    can_handle_target = estimated_capacity >= 5000
    
    return {
        'success': True,
        'success_count': success_count,
        'failed_count': failed_count,
        'success_rate': success_rate,
        'avg_response_time': avg_response_time,
        'max_response_time': max_response_time,
        'min_response_time': min_response_time,
        'p90_response_time': p90_time,
        'p95_response_time': p95_time,
        'status_codes': status_codes,
        'error_types': errors,
        'concurrency': concurrency,
        'total_requests': num_requests,
        'requests_per_second': requests_per_second,
        'performance_rating': performance_rating,
        'estimated_capacity': estimated_capacity,
        'capacity_rating': capacity_rating,
        'capacity_message': capacity_message,
        'can_handle_target': can_handle_target
    }

def check_status_code(url):
    """Check if website returns 200 status code"""
    try:
        response = requests.get(url, timeout=5)
        return {
            'status_code': response.status_code,
            'success': 200 <= response.status_code < 400,
            'message': f"Site returned status code {response.status_code}"
        }
    except Exception as e:
        return {
            'status_code': None,
            'success': False,
            'message': f"Error connecting to site: {str(e)}"
        }

def check_content(url):
    """Check if website has meaningful content"""
    try:
        response = requests.get(url, timeout=5)
        if not response.ok:
            return {'success': False, 'message': "Failed to retrieve content"}
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.extract()
            
        # Get text content
        text = soup.get_text()
        
        # Check if there's substantial text content (at least 100 characters)
        if len(text.strip()) > 100:
            return {
                'success': True,
                'message': "Site has meaningful content",
                'content_size': len(response.text)
            }
        else:
            return {
                'success': False,
                'message': "Site may have insufficient content",
                'content_size': len(response.text)
            }
    except Exception as e:
        return {'success': False, 'message': f"Error checking content: {str(e)}"}

def check_mobile_responsiveness(url):
    """Check if site has viewport meta tag for mobile responsiveness"""
    try:
        response = requests.get(url, timeout=5)
        if not response.ok:
            return {'success': False, 'message': "Could not fetch page for responsive check"}
        
        soup = BeautifulSoup(response.text, 'html.parser')
        viewport_meta = soup.find('meta', attrs={'name': 'viewport'})
        
        if viewport_meta:
            return {
                'success': True,
                'message': "Viewport meta tag found, site appears mobile-friendly",
                'viewport': viewport_meta.get('content', 'No content attribute')
            }
        else:
            return {
                'success': False,
                'message': "No viewport meta tag found, site may not be mobile-friendly"
            }
    except Exception as e:
        return {'success': False, 'message': f"Error checking mobile responsiveness: {str(e)}"}

def measure_page_speed(url):
    """Basic page speed measurement"""
    try:
        start_time = time.time()
        response = requests.get(url, timeout=10)
        end_time = time.time()
        
        load_time = end_time - start_time
        
        # Classify speed
        if load_time < 1.0:
            speed_rating = "Excellent"
        elif load_time < 2.0:
            speed_rating = "Good"
        elif load_time < 4.0:
            speed_rating = "Average"
        else:
            speed_rating = "Slow"
            
        return {
            'success': True,
            'load_time': load_time,
            'speed_rating': speed_rating
        }
    except Exception as e:
        return {'success': False, 'message': f"Error measuring page speed: {str(e)}"}

def validate_url(url):
    """Validate if the provided string is a proper URL"""
    regex = re.compile(
        r'^(?:http|https)://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return re.match(regex, url) is not None

@app.route('/', methods=['GET'])
def index():
    """Display homepage with URL input form"""
    meta = {
        'title': f"{SITE_NAME} - {SITE_TAGLINE}",
        'description': SITE_DESCRIPTION,
        'keywords': SITE_KEYWORDS,
        'og_image': url_for('static', filename='img/logo.png', _external=True),
        'twitter_card': 'summary_large_image',
        'canonical': request.base_url
    }
    return render_template('index.html', meta=meta)

# Define a function to run tests in background
def run_tests_in_background(url, test_id, user_capacity=5000):
    """Run all tests in background and update progress"""
    try:
        # Initialize progress
        test_progress[test_id] = {
            'status': 'running',
            'progress': 0,
            'message': 'Starting tests...',
            'started_at': datetime.now().isoformat(),
            'results': {},
            'user_capacity': user_capacity  # Store the target capacity
        }
        
        # Step 1: Check status code
        update_progress(test_id, 10, 'Checking site availability...')
        status_check = check_status_code(url)
        test_progress[test_id]['results']['status_check'] = status_check
        
        if not status_check['success']:
            # Site is not available, end tests early
            test_progress[test_id]['status'] = 'completed'
            test_progress[test_id]['progress'] = 100
            test_progress[test_id]['message'] = 'Tests completed with errors.'
            test_progress[test_id]['completed_at'] = datetime.now().isoformat()
            test_progress[test_id]['results']['page_speed'] = {'success': False}
            test_progress[test_id]['results']['content_check'] = {'success': False}
            test_progress[test_id]['results']['mobile_check'] = {'success': False}
            test_progress[test_id]['results']['load_test'] = {'success': False}
            test_progress[test_id]['results']['code_quality'] = {'success': False}
            return
            
        # Step 2: Check code quality with focus on high traffic handling - MOVED UP
        update_progress(test_id, 25, 'Analyzing code quality and scalability...')
        code_quality = check_code_quality(url)
        test_progress[test_id]['results']['code_quality'] = code_quality
        
        # Step 3: Check content
        update_progress(test_id, 40, 'Analyzing content...')
        content_check = check_content(url)
        test_progress[test_id]['results']['content_check'] = content_check
        
        # Step 4: Check mobile responsiveness
        update_progress(test_id, 50, 'Checking mobile responsiveness...')
        mobile_check = check_mobile_responsiveness(url)
        test_progress[test_id]['results']['mobile_check'] = mobile_check
        
        # Step 5: Measure page speed
        update_progress(test_id, 60, 'Measuring page speed...')
        page_speed = measure_page_speed(url)
        test_progress[test_id]['results']['page_speed'] = page_speed
        
        # Step 6: Perform enhanced load test to evaluate high user capacity
        update_progress(test_id, 70, f'Running load tests to simulate {user_capacity} users...')
        # Adjust test parameters based on user capacity
        if user_capacity > 10000:
            num_requests = 100
            concurrency = 20
        elif user_capacity > 5000:
            num_requests = 75
            concurrency = 15
        else:
            num_requests = 50
            concurrency = 10
            
        load_test = perform_load_test(url, num_requests=num_requests, concurrency=concurrency)
        # Update the test with the user's target capacity
        load_test['target_capacity'] = user_capacity
        load_test['can_handle_target'] = load_test['estimated_capacity'] >= user_capacity
        
        test_progress[test_id]['results']['load_test'] = load_test
        
        # Step 7: Perform targeted high-concurrency test
        update_progress(test_id, 90, 'Testing site under high concurrency...')
        # Adjust concurrency based on user capacity
        high_concurrency = min(25, max(10, user_capacity // 300))  # Scale with capacity but cap at 25
        high_concurrency_test = perform_load_test(url, num_requests=40, concurrency=high_concurrency)
        test_progress[test_id]['results']['high_concurrency_test'] = high_concurrency_test
        
        # All tests completed
        update_progress(test_id, 100, 'All tests completed successfully!')
        test_progress[test_id]['status'] = 'completed'
        test_progress[test_id]['completed_at'] = datetime.now().isoformat()
        
    except Exception as e:
        # Handle any errors
        test_progress[test_id]['status'] = 'error'
        test_progress[test_id]['message'] = f"Error during tests: {str(e)}"
        test_progress[test_id]['progress'] = 100
        test_progress[test_id]['completed_at'] = datetime.now().isoformat()

def update_progress(test_id, progress, message):
    """Update the progress of a test"""
    if test_id in test_progress:
        test_progress[test_id]['progress'] = progress
        test_progress[test_id]['message'] = message

@app.route('/test', methods=['POST'])
def test_site():
    """Process form submission and start tests asynchronously"""
    url = request.form.get('url', '').strip()
    user_capacity = request.form.get('user_capacity', '5000')  # New field for user capacity
    
    # Try to convert to integer, default to 5000 if fails
    try:
        user_capacity = int(user_capacity)
    except ValueError:
        user_capacity = 5000
    
    if not url:
        return render_template('index.html', error="Please enter a URL")
    
    if not validate_url(url):
        return render_template('index.html', error="Please enter a valid URL (including http:// or https://)")
    
    # Generate a unique test ID
    test_id = str(uuid.uuid4())
    
    # Start tests in background with user capacity parameter
    thread = threading.Thread(target=run_tests_in_background, args=(url, test_id, user_capacity))
    thread.daemon = True
    thread.start()
    
    # Return the progress page with the test ID and user capacity
    meta = {
        'title': f"Testing {url} - {SITE_NAME}",
        'description': f"Analyzing if {url} can survive the storm of {user_capacity} concurrent users.",
        'keywords': SITE_KEYWORDS,
        'og_image': url_for('static', filename='img/logo.png', _external=True),
        'twitter_card': 'summary_large_image',
        'canonical': request.base_url,
        'noindex': True  # Don't index progress pages
    }
    return render_template('progress.html', test_id=test_id, url=url, user_capacity=user_capacity, meta=meta, site_name=SITE_NAME, site_tagline=SITE_TAGLINE)

@app.route('/progress/<test_id>', methods=['GET'])
def get_progress(test_id):
    """Return the current progress of a test"""
    if test_id in test_progress:
        return jsonify(test_progress[test_id])
    else:
        return jsonify({'error': 'Test not found'}), 404

@app.route('/results/<test_id>', methods=['GET'])
def show_results(test_id):
    """Show test results after completion with focus on high traffic handling"""
    # Add current datetime for templates
    now = datetime.now()
    
    if test_id in test_progress and test_progress[test_id]['status'] == 'completed':
        results = test_progress[test_id]['results']
        url = request.args.get('url', 'Unknown URL')
        user_capacity = test_progress[test_id].get('user_capacity', 5000)
        
        # Pass high concurrency test results if available
        high_concurrency_test = results.get('high_concurrency_test', {})
        
        # SEO metadata for results page
        load_test = results.get('load_test', {'success': False})
        can_handle = load_test.get('can_handle_target', False) if isinstance(load_test, dict) else False
        
        meta_title = f"Storm Test: {url} {'Survived' if can_handle else 'Failed'} {user_capacity:,} Users - {SITE_NAME}"
        meta_description = f"Analysis shows {url} {'can' if can_handle else 'cannot'} survive a storm of {user_capacity:,} concurrent users. View the complete report."
        
        meta = {
            'title': meta_title,
            'description': meta_description,
            'keywords': SITE_KEYWORDS + f", {url}, deployment testing",
            'og_image': url_for('static', filename='img/logo.png', _external=True),
            'twitter_card': 'summary_large_image',
            'canonical': request.base_url
        }
        
        return render_template('results.html',
                              url=url,
                              status_check=results.get('status_check', {'success': False}),
                              content_check=results.get('content_check', {'success': False}),
                              mobile_check=results.get('mobile_check', {'success': False}),
                              page_speed=results.get('page_speed', {'success': False}),
                              load_test=load_test,
                              code_quality=results.get('code_quality', {'success': False}),
                              high_concurrency_test=high_concurrency_test,
                              user_capacity=user_capacity,
                              meta=meta, 
                              site_name=SITE_NAME, 
                              site_tagline=SITE_TAGLINE,
                              now=now,  # Pass current datetime to template
                              test_id=test_id)  # Pass test_id to template
    else:
        # SEO metadata for error page
        meta = {
            'title': f"Test Not Found - {SITE_NAME}",
            'description': SITE_DESCRIPTION,
            'keywords': SITE_KEYWORDS,
            'og_image': url_for('static', filename='img/logo.png', _external=True),
            'twitter_card': 'summary',
            'canonical': url_for('index', _external=True),
            'noindex': True
        }
        return redirect(url_for('index'))

def check_code_quality(url):
    """Check basic code quality indicators of the website with focus on scale handling"""
    try:
        response = requests.get(url, timeout=5)
        if not response.ok:
            return {'success': False, 'message': "Could not fetch page for code check"}
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Check HTML structure
        html_tag = soup.find('html')
        head_tag = soup.find('head')
        body_tag = soup.find('body')
        
        # Check for document type declaration
        html_content = response.text
        has_doctype = '<!DOCTYPE' in html_content.upper()
        
        # Check for inline styles (not best practice)
        inline_styles = len(soup.select('[style]'))
        
        # Check for valid meta tags
        meta_title = soup.find('title')
        meta_description = soup.find('meta', attrs={'name': 'description'})
        
        # Check for console errors or unnecessary JS (simplified approach)
        script_tags = len(soup.find_all('script'))
        inline_scripts = len(soup.select('script:not([src])'))
        
        # Generate a score
        score = 100
        issues = []
        
        if not has_doctype:
            score -= 10
            issues.append("Missing DOCTYPE declaration")
        
        if not html_tag or not head_tag or not body_tag:
            score -= 15
            issues.append("Improper HTML structure")
        
        if inline_styles > 5:
            score -= (min(inline_styles, 20) // 2)
            issues.append(f"Found {inline_styles} inline styles (best practice is to use CSS files)")
        
        if not meta_title:
            score -= 10
            issues.append("Missing title tag")
            
        if not meta_description:
            score -= 5
            issues.append("Missing meta description")
            
        if inline_scripts > 3:
            score -= min(inline_scripts, 15)
            issues.append(f"Found {inline_scripts} inline scripts (best practice is to use external JS files)")
            
        # Determine quality level
        if score >= 90:
            quality_level = "Excellent"
        elif score >= 75:
            quality_level = "Good"
        elif score >= 60:
            quality_level = "Average"
        else:
            quality_level = "Needs Improvement"
        
        # Enhanced checks for scalability and performance best practices
        # Check for resource optimization
        images = soup.find_all('img')
        unoptimized_images = 0
        for img in images:
            # Check if image has width/height attributes (prevents layout shifts)
            if not (img.get('width') and img.get('height')):
                unoptimized_images += 1
        
        # Check for proper cache headers
        cache_headers = False
        headers = response.headers
        cache_control = headers.get('Cache-Control')
        etag = headers.get('ETag')
        expires = headers.get('Expires')
        if cache_control or etag or expires:
            cache_headers = True
            
        # Check for minified resources
        css_files = len(soup.find_all('link', rel='stylesheet'))
        js_files = len(soup.find_all('script', src=True))
        
        # Check for GZIP/compression
        compression = 'gzip' in headers.get('Content-Encoding', '').lower() or 'br' in headers.get('Content-Encoding', '').lower()
        
        # Check for CDN usage
        potential_cdn_domains = ['cloudfront.net', 'cloudflare.com', 'akamai', 'fastly', 'cdn']
        cdn_detected = False
        for link in soup.find_all(['script', 'link', 'img']):
            src = link.get('src') or link.get('href') or ''
            if any(cdn in src.lower() for cdn in potential_cdn_domains):
                cdn_detected = True
                break
        
        if not cache_headers:
            score -= 10
            issues.append("Missing cache headers (reduces server load for repeat visitors)")
        
        if unoptimized_images > 3:
            score -= min(unoptimized_images, 15)
            issues.append(f"Found {unoptimized_images} images without proper dimension attributes")
            
        if not compression:
            score -= 10
            issues.append("Content compression not detected (GZIP/Brotli)")
            
        if not cdn_detected and (css_files + js_files + len(images)) > 10:
            score -= 10
            issues.append("Consider using a CDN for static resources to improve scalability")
        
        # Additional scalability-focused metrics
        scalability_score = 100
        scalability_issues = []
        
        if inline_scripts > 3:
            scalability_score -= 15
            scalability_issues.append("Reduce inline JavaScript to improve cacheability")
            
        if not cache_headers:
            scalability_score -= 20
            scalability_issues.append("Add proper cache headers to reduce server load")
            
        if not compression:
            scalability_score -= 20
            scalability_issues.append("Enable GZIP/Brotli compression")
            
        if not cdn_detected:
            scalability_score -= 15
            scalability_issues.append("Use a CDN for static assets")
            
        if len(images) > 10 and unoptimized_images > len(images) * 0.5:
            scalability_score -= 15
            scalability_issues.append("Optimize images and specify dimensions")
        
        # Determine scalability level
        if scalability_score >= 90:
            scalability_level = "Excellent"
        elif scalability_score >= 75:
            scalability_level = "Good"
        elif scalability_score >= 60:
            scalability_level = "Average"
        else:
            scalability_level = "Poor"
            
        # Determine if code quality supports high traffic
        high_traffic_ready = scalability_score >= 75
        
        return {
            'success': True,
            'score': score,
            'quality_level': quality_level,
            'issues': issues,
            'meta': {
                'has_doctype': has_doctype,
                'has_title': meta_title is not None,
                'has_description': meta_description is not None,
                'inline_styles': inline_styles,
                'script_tags': script_tags,
                'inline_scripts': inline_scripts,
                'cache_headers': cache_headers,
                'compression': compression,
                'cdn_detected': cdn_detected,
                'unoptimized_images': unoptimized_images,
                'total_images': len(images)
            },
            'scalability': {
                'score': scalability_score,
                'level': scalability_level,
                'issues': scalability_issues,
                'high_traffic_ready': high_traffic_ready
            }
        }
        
    except Exception as e:
        return {'success': False, 'message': f"Error checking code quality: {str(e)}"}

@app.context_processor
def inject_now():
    """Inject the current datetime into all templates."""
    return {'now': datetime.now()}

# Add 404 error handler
@app.errorhandler(404)
def page_not_found(e):
    """Handle 404 errors with custom template"""
    meta = {
        'title': f"Page Not Found - {SITE_NAME}",
        'description': "The page you're looking for doesn't exist or has been moved.",
        'keywords': SITE_KEYWORDS,
        'og_image': url_for('static', filename='img/logo.png', _external=True),
        'twitter_card': 'summary',
        'canonical': request.base_url,
        'noindex': True
    }
    return render_template('404.html', meta=meta, site_name=SITE_NAME, site_tagline=SITE_TAGLINE), 404

# Add a redirect for the Render health check
@app.route('/health')
def health_check():
    """Health check endpoint for Render"""
    return jsonify({"status": "ok"}), 200

# Clean up tests periodically to avoid memory leaks
@app.before_request
def cleanup_old_tests():
    """Remove old test results to prevent memory leaks"""
    now = datetime.now()
    to_remove = []
    
    for test_id, test_data in test_progress.items():
        # If test is completed and older than 1 hour or is running for more than 15 minutes
        if 'completed_at' in test_data:
            completed_time = datetime.fromisoformat(test_data['completed_at'])
            if (now - completed_time).total_seconds() > 3600:  # 1 hour
                to_remove.append(test_id)
        elif 'started_at' in test_data:
            started_time = datetime.fromisoformat(test_data['started_at'])
            if (now - started_time).total_seconds() > 900:  # 15 minutes
                to_remove.append(test_id)
    
    for test_id in to_remove:
        test_progress.pop(test_id, None)

# Adjust for environment variables set by Render
if __name__ == '__main__':
    # Get port from environment variable (Render sets PORT automatically)
    port = int(os.environ.get('PORT', 5000))
    
    # Debug mode should be off in production
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    app.logger.info(f"Starting DeployProbe on port {port} (debug={debug_mode})")
    
    # Use host='0.0.0.0' to bind to all interfaces
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
