"""
Service layer for authority zone routing
"""
from .models import Authority, AuthorityZone


def find_authority_for_location(latitude, longitude):
    """
    Find the authority responsible for a given location using point-in-polygon.
    Returns the Authority object or None if no match found.
    """
    if latitude is None or longitude is None:
        return None
    
    # Check all zones to find which one contains this point
    zones = AuthorityZone.objects.all()
    
    for zone in zones:
        if zone.contains_point(latitude, longitude):
            return zone.authority
    
    return None
