"""
Utility functions for issues app
"""
import exifread
from geopy.geocoders import Nominatim
from django.conf import settings


def extract_gps_from_image(image_file):
    """
    Extract GPS coordinates from image EXIF data.
    Returns (latitude, longitude) tuple or (None, None) if not found.
    """
    try:
        # Reset file pointer
        image_file.seek(0)
        
        # Read EXIF tags
        tags = exifread.process_file(image_file, details=False)
        
        # Get GPS tags
        gps_latitude = tags.get('GPS GPSLatitude')
        gps_latitude_ref = tags.get('GPS GPSLatitudeRef')
        gps_longitude = tags.get('GPS GPSLongitude')
        gps_longitude_ref = tags.get('GPS GPSLongitudeRef')
        
        if not all([gps_latitude, gps_latitude_ref, gps_longitude, gps_longitude_ref]):
            return None, None
        
        # Convert EXIF format to decimal degrees
        lat = convert_to_degrees(gps_latitude.values, gps_latitude_ref.values)
        lon = convert_to_degrees(gps_longitude.values, gps_longitude_ref.values)
        
        return lat, lon
    except Exception as e:
        print(f"Error extracting GPS: {e}")
        return None, None


def convert_to_degrees(values, ref):
    """Convert EXIF GPS coordinate format to decimal degrees"""
    degrees = float(values[0].num) / float(values[0].den)
    minutes = float(values[1].num) / float(values[1].den)
    seconds = float(values[2].num) / float(values[2].den)
    
    decimal = degrees + (minutes / 60.0) + (seconds / 3600.0)
    
    if ref in ['S', 'W']:
        decimal = -decimal
    
    return decimal


def reverse_geocode(latitude, longitude):
    """
    Get human-readable address from coordinates.
    Returns address string or None.
    """
    try:
        geolocator = Nominatim(user_agent="civic_issues_app")
        location = geolocator.reverse(f"{latitude}, {longitude}", timeout=10)
        if location:
            return location.address
    except Exception as e:
        print(f"Error reverse geocoding: {e}")
    return None
