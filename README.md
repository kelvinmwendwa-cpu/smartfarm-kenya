# SmartFarm Kenya

A comprehensive farm management system designed specifically for Kenyan farmers. SmartFarm Kenya combines modern technology with traditional farming practices to help you maximize productivity and efficiency.

## Features

### 🌱 Crop Management
- Add and manage crops with planting and harvest dates
- Track growth progress with visual indicators
- Monitor crop status (growing, ready, harvested)
- Add detailed notes for each crop

### 🐄 Livestock Management
- Manage different types of livestock (cows, goats, chickens, pigs, sheep)
- Track herd numbers and health status
- Monitor breeding information
- Record medical treatments and observations

### 🌤️ Weather Information
- Real-time weather data for Nairobi, Kenya
- Farming recommendations based on weather conditions
- Temperature, humidity, and wind speed monitoring
- Seasonal farming tips

### 📋 Activity Logging
- Comprehensive activity tracking system
- Log planting, watering, fertilizing, harvesting activities
- Record livestock feeding and treatments
- Timeline view of all farm operations

### 📸 Photo Gallery
- Upload and organize farm photos
- Track visual progress over time
- Add descriptions to photos
- Grid and timeline views

### 🔔 Smart Notifications
- Harvest readiness alerts
- Watering reminders
- Livestock health notifications
- Personalized farming recommendations

### 👤 User Management
- Secure user registration and login
- Personalized dashboards
- Farm profile management
- Data privacy and security

## Technology Stack

- **Backend:** Flask (Python)
- **Database:** SQLite (with SQLAlchemy ORM)
- **Frontend:** HTML5, CSS3, JavaScript
- **UI Framework:** Custom responsive design
- **Authentication:** Flask-Login with bcrypt
- **File Upload:** Werkzeug security
- **Weather API:** OpenWeatherMap (optional)

## Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Setup Instructions

1. **Clone or download the project**
   ```bash
   cd SmartFarm-Kenya
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On Mac/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   - Copy `.env` file and update the values:
     - `SECRET_KEY`: Generate a secure random string
     - `WEATHER_API_KEY`: Get free API key from OpenWeatherMap (optional)

5. **Initialize the database**
   ```bash
   python app.py
   ```
   The database will be created automatically on first run.

6. **Run the application**
   ```bash
   python app.py
   ```

7. **Access the application**
   Open your browser and go to: `http://localhost:5000`

## Usage

### Getting Started

1. **Register an account**
   - Click "Get Started" on the home page
   - Fill in your details and farm information
   - Login with your credentials

2. **Add your first crop**
   - Navigate to "Crops" from the dashboard
   - Click "Add New Crop"
   - Enter crop details including planting and expected harvest dates

3. **Add livestock**
   - Navigate to "Livestock" from the dashboard
   - Click "Add Livestock"
   - Enter animal details and health information

4. **Log activities**
   - Navigate to "Activities" from the dashboard
   - Click "Log Activity"
   - Record daily farming operations

5. **Upload photos**
   - Navigate to "Gallery" from the dashboard
   - Click "Upload Photo"
   - Add images with descriptions

### Dashboard Overview

The dashboard provides:
- Quick stats (total crops, livestock count)
- Recent activities timeline
- Harvest alerts
- Weather widget
- Quick action buttons

### Mobile Responsiveness

SmartFarm Kenya is fully responsive and works on:
- Desktop computers
- Tablets
- Mobile phones

## Configuration

### Weather API Setup (Optional)

1. Sign up at [OpenWeatherMap](https://openweathermap.org/api)
2. Get your free API key
3. Update `.env` file: `WEATHER_API_KEY=your_api_key_here`
4. Restart the application

Without an API key, the app will show demo weather data.

### Database

The application uses SQLite by default. The database file (`smartfarm.db`) will be created automatically in the project directory.

To reset the database:
```bash
del smartfarm.db  # On Windows
rm smartfarm.db   # On Mac/Linux
```

## Features in Detail

### Crop Management
- **Growth Tracking**: Visual progress bars showing crop development
- **Harvest Alerts**: Automatic notifications when crops are ready
- **Status Management**: Track crops from planting to harvest
- **Notes System**: Add detailed observations and instructions

### Livestock Management
- **Health Monitoring**: Track health status and medical needs
- **Population Tracking**: Monitor herd numbers and changes
- **Breed Management**: Record breed information and characteristics
- **Treatment Records**: Log medical treatments and outcomes

### Activity System
- **Comprehensive Logging**: Record all farm operations
- **Timeline View**: Chronological display of activities
- **Statistics**: Activity type breakdown and frequency
- **Search & Filter**: Find specific activities quickly

### Notification System
- **Smart Alerts**: Context-aware notifications based on farm data
- **Actionable Reminders**: Direct links to relevant actions
- **Priority System**: Urgent alerts highlighted appropriately
- **Personalization**: Tailored to your specific farm operations

## Security

- Password hashing with bcrypt
- Secure session management
- File upload security
- Input validation and sanitization
- CSRF protection

## Support

For issues or questions:
1. Check the troubleshooting section below
2. Review the error logs in the console
3. Ensure all dependencies are properly installed

## Troubleshooting

### Common Issues

**Database Error**: Make sure you have write permissions in the project directory.

**Import Errors**: Ensure all dependencies are installed correctly with `pip install -r requirements.txt`.

**Port Already in Use**: Change the port in `app.py` or close other applications using port 5000.

**File Upload Issues**: Check that the `static/uploads` directory exists and has write permissions.

### Performance Tips

- Keep photo file sizes reasonable (under 5MB)
- Regularly clean up old activities if needed
- Consider database backups for important data

## Contributing

SmartFarm Kenya is designed to be a community-driven project. To contribute:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is open source and available under the MIT License.

## Future Enhancements

Planned features include:
- Mobile app version
- Advanced analytics and reporting
- Integration with agricultural sensors
- Multi-language support
- Offline functionality
- Export capabilities (PDF, Excel)
- Social features for farmer communities

---

**SmartFarm Kenya - Empowering Kenyan Farmers with Technology**
