# FixMyArea - Civic Issues Portal

A Django-based web application for reporting and tracking civic issues in real-time. Users can upload photos of issues (road problems, street light issues, garbage, etc.), and the system automatically extracts location from image GPS data and assigns issues to the appropriate authorities.

## Features

- **Issue Reporting**: Users can report civic issues with photos
- **GPS Extraction**: Automatically extracts location from image EXIF data
- **Authority Assignment**: Automatically assigns issues to authorities based on geographic zones
- **Public Feed**: View all reported issues with filtering and search
- **Authority Dashboard**: Authorities can view assigned issues and post status updates
- **Status Tracking**: Track issue status from open to resolved
- **Authentication**: Email/password and OAuth (Google) authentication

## Technology Stack

- **Backend**: Django 4.2
- **Database**: SQLite (development) / PostgreSQL (production)
- **Image Processing**: Pillow, exifread
- **Geospatial**: Shapely for point-in-polygon checks
- **Authentication**: django-allauth
- **Storage**: Local filesystem (development) / AWS S3 or Cloudinary (production)
- **Frontend**: Bootstrap 5, Leaflet.js for maps

## Installation

1. **Clone the repository** (or navigate to the project directory)

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Create environment file** (optional, for production):
   Create a `.env` file in the project root:
   ```
   SECRET_KEY=your-secret-key-here
   DEBUG=True
   USE_CLOUD_STORAGE=False
   # For AWS S3:
   # AWS_ACCESS_KEY_ID=your-key
   # AWS_SECRET_ACCESS_KEY=your-secret
   # AWS_STORAGE_BUCKET_NAME=your-bucket
   # AWS_S3_REGION_NAME=us-east-1
   ```

5. **Run migrations**:
   ```bash
   python manage.py migrate
   ```

6. **Create a superuser**:
   ```bash
   python manage.py createsuperuser
   ```

7. **Load initial data** (create issue categories):
   ```bash
   python manage.py shell
   ```
   Then in the shell:
   ```python
   from issues.models import IssueCategory
   IssueCategory.objects.create(name="Road Issues", icon="🛣️", description="Potholes, road damage, etc.")
   IssueCategory.objects.create(name="Street Lights", icon="💡", description="Broken or non-functional street lights")
   IssueCategory.objects.create(name="Garbage", icon="🗑️", description="Garbage collection issues, overflowing bins")
   IssueCategory.objects.create(name="Water Supply", icon="💧", description="Water supply problems")
   IssueCategory.objects.create(name="Other", icon="📋", description="Other civic issues")
   ```

8. **Run the development server**:
   ```bash
   python manage.py runserver
   ```

9. **Access the application**:
   - Open http://127.0.0.1:8000 in your browser
   - Admin panel: http://127.0.0.1:8000/admin

## Setting Up Authorities and Zones

### Method 1: Using Django Admin

1. Log in to the admin panel
2. Create an Authority (e.g., "Municipality of City X")
3. Create AuthorityZone entries with GeoJSON polygon data

### Method 2: Using Management Command

Create a GeoJSON file with zone polygons, then:

```bash
python manage.py import_zones zones.geojson --authority-name "Municipality of City X"
```

Example GeoJSON format:
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "properties": {
        "name": "Ward 1"
      },
      "geometry": {
        "type": "Polygon",
        "coordinates": [[
          [77.5, 12.9],
          [77.6, 12.9],
          [77.6, 13.0],
          [77.5, 13.0],
          [77.5, 12.9]
        ]]
      }
    }
  ]
}
```

### Method 3: Assign Users as Authority Managers

1. Create a user account for the authority
2. In Django admin, edit the UserProfile and set `is_authority = True`
3. In the Authority admin, add the user to `authorized_users`

## Usage

### For Citizens

1. **Sign up** or **log in**
2. Click **"Report Issue"**
3. Fill in issue details and upload a photo
4. Location will be extracted from image GPS if available, or enter manually
5. Submit the issue
6. View your issue and track its status

### For Authorities

1. **Log in** with an authority account
2. Access the **Authority Dashboard**
3. View all issues assigned to your authority
4. Click on an issue to view details
5. Post status updates and describe measures taken

## Project Structure

```
FIXMYAREA/
├── civic/              # Main Django project settings
├── accounts/           # User accounts and profiles
├── issues/             # Issue reporting and tracking
├── authorities/        # Authority management and zones
├── templates/          # HTML templates
├── static/             # Static files (CSS, JS, images)
├── media/              # User-uploaded files
└── manage.py           # Django management script
```

## Configuration

### Cloud Storage (Production)

To use AWS S3 or Cloudinary for image storage:

1. Set `USE_CLOUD_STORAGE=True` in `.env`
2. Configure AWS credentials in `.env`:
   ```
   AWS_ACCESS_KEY_ID=your-key
   AWS_SECRET_ACCESS_KEY=your-secret
   AWS_STORAGE_BUCKET_NAME=your-bucket
   AWS_S3_REGION_NAME=us-east-1
   ```

### OAuth (Google Login)

1. Create a Google OAuth application
2. Add credentials to Django admin under Social Applications
3. Configure redirect URIs

## Development

### Running Tests

```bash
python manage.py test
```

### Creating Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

## License

This project is open source and available for use.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
