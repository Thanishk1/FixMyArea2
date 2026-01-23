# Quick Setup Guide

## Initial Setup Steps

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run migrations**:
   ```bash
   python manage.py migrate
   ```

3. **Create superuser**:
   ```bash
   python manage.py createsuperuser
   ```

4. **Create initial categories**:
   ```bash
   python manage.py create_categories
   ```

5. **Run the server**:
   ```bash
   python manage.py runserver
   ```

## Setting Up Authorities (Example)

1. **Log in to admin** (http://127.0.0.1:8000/admin)

2. **Create an Authority**:
   - Go to Authorities → Add Authority
   - Name: "Municipality of Example City"
   - Contact Email: "admin@examplecity.gov"
   - Save

3. **Import zones** (using the example GeoJSON):
   ```bash
   python manage.py import_zones setup_example_zones.geojson --authority-name "Municipality of Example City"
   ```
   
   **Note**: Update the coordinates in `setup_example_zones.geojson` to match your actual city's boundaries.

4. **Create an authority user**:
   - Go to Users → Add User
   - Create a user account
   - Go to User Profiles → Add User Profile
   - Select the user, check "Is authority"
   - Save

5. **Assign user to authority**:
   - Go to Authorities → Edit your authority
   - Add the user to "Authorized users"
   - Save

## Testing the Application

1. **Create a test user account** (sign up at http://127.0.0.1:8000/accounts/signup/)

2. **Report an issue**:
   - Click "Report Issue"
   - Fill in details and upload a photo
   - If the photo has GPS data, location will be extracted automatically
   - Otherwise, enter coordinates manually or use "Use My Current Location"

3. **View as authority**:
   - Log in with the authority account
   - Go to Authority Dashboard
   - View assigned issues and post updates

## Getting Real GeoJSON Data

To get actual zone boundaries for your city:

1. **OpenStreetMap**: Use tools like Overpass Turbo to query administrative boundaries
2. **Government Data**: Many cities provide GeoJSON files of wards/zones
3. **Manual Creation**: Use tools like geojson.io to draw polygons

Example query for Overpass Turbo:
```
[out:json][timeout:25];
(
  relation["admin_level"="8"]["boundary"="administrative"]["name"~"Ward"];
);
out geom;
```

Convert the result to GeoJSON format and use with the import command.

## Scraping GWMC ward corporators + localities (66 wards)

This project includes a scraper for the GWMC ward-wise profile page:
- Source: `https://gwmc.gov.in/wardwise_profile.aspx`
- Command: `python manage.py scrape_gwmc_wards --out gwmc_wards.csv`

Options:
- `--format json` to export JSON instead of CSV
- `--out <path>` to set output file name

Notes:
- This uses ASP.NET WebForms postbacks and relies on the page structure; if GWMC changes their HTML/IDs, we may need to tune the parsing heuristics.
