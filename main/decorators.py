from django.core.cache import cache
from django.http import HttpResponseForbidden
from functools import wraps
import time

def rate_limit(key_prefix, max_attempts=5, timeout=300):
    """
    Rate limiting decorator that limits the number of attempts within a time window.
    
    Args:
        key_prefix (str): Prefix for the cache key
        max_attempts (int): Maximum number of attempts allowed
        timeout (int): Time window in seconds
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            # Get the IP address and user agent
            ip = request.META.get('REMOTE_ADDR', '')
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            
            # Create a unique key using both IP and user agent
            session_key = f'{key_prefix}_attempts_{ip}_{user_agent}'
            timestamp_key = f'{key_prefix}_timestamp_{ip}_{user_agent}'
            
            # If user is already logged in, clear any rate limit
            if request.session.get('logged_in'):
                request.session.pop(session_key, None)
                request.session.pop(timestamp_key, None)
                return view_func(request, *args, **kwargs)
            
            # Get the current attempts and timestamp
            attempts = request.session.get(session_key, 0)
            last_attempt = request.session.get(timestamp_key, 0)
            current_time = time.time()
            
            # Reset attempts if timeout has passed
            if current_time - last_attempt > timeout:
                attempts = 0
                request.session[timestamp_key] = current_time
            
            # If too many attempts, return error
            if attempts >= max_attempts:
                return HttpResponseForbidden(
                    f'Too many login attempts. Please try again in {timeout//60} minutes.'
                )
            
            # Call the view
            response = view_func(request, *args, **kwargs)
            
            # If login was successful, clear the attempts
            if response.status_code == 302 and 'file_manager' in response.url:
                request.session.pop(session_key, None)
                request.session.pop(timestamp_key, None)
            else:
                # Increment attempts if login failed
                request.session[session_key] = attempts + 1
                request.session[timestamp_key] = current_time
            
            return response
        return _wrapped_view
    return decorator 