# GoBuddy - Tourism & Travel Management System
## User Manual & Project Documentation

Welcome to **GoBuddy**, a high-end holiday planning and management platform. This project features a robust interactive mapping system, dynamic itineraries, and seamless admin-to-customer workflows.

---

## 1. Quick Access Links
| PAGE | URL | DESCRIPTION |
| :--- | :--- | :--- |
| **User Home** | `http://127.0.0.1:8000/` | Public site to browse packages and plan trips. |
| **Trip Planner** | `http://127.0.0.1:8000/customers/plan/` | Interactive map-based itinerary builder. |
| **Admin Dashboard** | `http://127.0.0.1:8000/panel/dashboard/` | Manager panel for packages and destinations. |

---

## 2. Core Workflows (The "GoBuddy" Way)

### A. Managing Destinations (Admin)
1. Navigate to **Destinations > Add New**.
2. Use the **Interactive Leaflet Map** to pinpoint the location.
3. **India Restriction**: Note that selections are restricted to India. Clicks outside India will show an alert.
4. **Auto-Fill**: Selecting a point on the map or using the search bar will automatically fill the **Destination Name**, **State**, and **Slug**.
5. Save to make it available for packages and trip planning.

### B. Creating Packages (Admin)
1. Go to **Packages > Create New**.
2. Select your destinations from the right-hand card list.
3. **Auto-Sync**: Locations you select are automatically added to the **Day 1 Itinerary**.
4. **Routing**: The map will automatically draw a driving route between your selected locations.
5. **Timeline Builder**:
   - Use **Move Up/Down** buttons to sequence the day's activities.
   - Use the **Move Day** dropdown to shift locations/activities to different days.
   - **Start/End Points**: These are automatically calculated based on the first and last locations in your itinerary.

### C. Planning a Trip (Customer)
1. Login as a Customer/User.
2. Select **Plan a Trip**.
3. Pick your preferred destinations from the modern tile gallery.
4. Watch as your **Timeline Itinerary** builds itself automatically.
5. Customize activities (Sightseeing, Food, Travel) with specific icons for each type.
6. Submit for approval to the Admin team.

---

## 3. Technology Stack & Features
- **Map Provider**: Leaflet.js with CartoDB Voyager tiles (Optimized to avoid 403 blocks).
- **Geocoding**: OpenStreetMap Nominatim restricted to `countrycodes=in`.
- **Routing**: Leaflet Routing Machine for automatic travel path visualization.
- **Styling**: TailwindCSS with Custom Glassmorphism (Customer) and Clean Dashboard (Admin) aesthetics.

---

## 4. Setup & Installation
1. **Database**: Create a MySQL DB named `gobuddy_db`.
2. **Environment**: Update `settings.py` with your MySQL credentials.
3. **Install**: `pip install django mysqlclient django-crispy-forms`
4. **Initialize**: `python manage.py migrate`
5. **Superuser**: `python manage.py createsuperuser`
6. **Launch**: `python manage.py runserver`

---

## 5. Troubleshooting
- **Map Not Loading**: Ensure you have an active internet connection for Leaflet/CartoDB tiles.
- **Access Blocked**: Standard OSM tiles are replaced with CartoDB to prevent local "Referer" blocks.
- **Icons Missing**: Ensure FontAwesome 5/6 is loaded in `base.html`.
