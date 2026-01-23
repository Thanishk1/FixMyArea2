from django.db import models
from django.contrib.auth.models import User
from shapely.geometry import Point, Polygon
from shapely import wkt
import json


class Authority(models.Model):
    """Represents a civic authority (municipality, ward office, etc.)"""
    name = models.CharField(max_length=200)
    contact_email = models.EmailField()
    contact_phone = models.CharField(max_length=20, blank=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Users who can manage this authority's issues
    authorized_users = models.ManyToManyField(User, related_name='authorities', blank=True)
    
    def __str__(self):
        return self.name


class AuthorityZone(models.Model):
    """Geographic zone (polygon) assigned to an authority"""
    authority = models.ForeignKey(Authority, on_delete=models.CASCADE, related_name='zones')
    name = models.CharField(max_length=200, help_text="Zone name (e.g., 'Ward 1', 'Zone A')")
    # Store polygon as GeoJSON string for simplicity (can be upgraded to PostGIS later)
    polygon_geojson = models.TextField(help_text="GeoJSON polygon coordinates")
    created_at = models.DateTimeField(auto_now_add=True)
    
    def get_polygon(self):
        """Convert GeoJSON to Shapely Polygon for point-in-polygon checks"""
        try:
            geojson = json.loads(self.polygon_geojson)
            if geojson.get('type') == 'Polygon':
                coords = geojson['coordinates'][0]  # First ring
                return Polygon(coords)
            elif geojson.get('type') == 'MultiPolygon':
                # Handle MultiPolygon by taking the first polygon
                coords = geojson['coordinates'][0][0]
                return Polygon(coords)
        except (json.JSONDecodeError, KeyError, IndexError):
            return None
        return None
    
    def contains_point(self, latitude, longitude):
        """Check if a point (lat, lng) is within this zone"""
        polygon = self.get_polygon()
        if polygon is None:
            return False
        point = Point(longitude, latitude)  # Note: Shapely uses (x, y) = (lng, lat)
        return polygon.contains(point)
    
    def __str__(self):
        return f"{self.authority.name} - {self.name}"
