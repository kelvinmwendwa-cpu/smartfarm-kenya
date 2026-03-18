from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, SelectField, IntegerField, FloatField, DateField, FileField
from wtforms.validators import DataRequired, Length, Email, NumberRange, EqualTo
from flask_bcrypt import Bcrypt
from datetime import datetime, timedelta
import os
from werkzeug.utils import secure_filename
from flask import send_from_directory
from flask_wtf.csrf import CSRFProtect, generate_csrf
import requests
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
csrf = CSRFProtect(app)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-here')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///smartfarm.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    farm_name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    crops = db.relationship('Crop', backref='farmer', lazy=True, cascade='all, delete-orphan')
    livestock = db.relationship('Livestock', backref='farmer', lazy=True, cascade='all, delete-orphan')
    activities = db.relationship('Activity', backref='farmer', lazy=True, cascade='all, delete-orphan')
    images = db.relationship('FarmImage', backref='farmer', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
    
    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

class Crop(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    planting_date = db.Column(db.Date, nullable=False)
    expected_harvest_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), default='growing')  # growing, ready, harvested
    notes = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Livestock(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(50), nullable=False)  # cow, goat, chicken, etc.
    breed = db.Column(db.String(50))
    number = db.Column(db.Integer, nullable=False, default=1)
    health_status = db.Column(db.String(20), default='healthy')  # healthy, sick, treatment
    notes = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Activity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(50), nullable=False)  # planting, watering, fertilizing, harvesting
    description = db.Column(db.Text, nullable=False)
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date())
    crop_id = db.Column(db.Integer, db.ForeignKey('crop.id'), nullable=True)
    livestock_id = db.Column(db.Integer, db.ForeignKey('livestock.id'), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class FarmImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Admin Models
class Admin(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
    
    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

class CropInfo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    crop_name = db.Column(db.String(100), nullable=False)
    best_planting_season = db.Column(db.String(100), nullable=False)
    planting_tips = db.Column(db.Text)
    growing_period_days = db.Column(db.Integer)
    water_requirements = db.Column(db.String(200))
    soil_type = db.Column(db.String(100))
    admin_id = db.Column(db.Integer, db.ForeignKey('admin.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class MarketPrice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    crop_name = db.Column(db.String(100), nullable=False)
    price_per_kg = db.Column(db.Float, nullable=False)
    market_location = db.Column(db.String(100), nullable=False)
    price_date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date())
    trend = db.Column(db.String(20))  # increasing, decreasing, stable
    admin_id = db.Column(db.Integer, db.ForeignKey('admin.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class FarmerAlert(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    alert_type = db.Column(db.String(50), nullable=False)  # general, weather, market, disease
    target_audience = db.Column(db.String(50), default='all')  # all, specific
    target_users = db.Column(db.Text)  # JSON string of user IDs for specific targeting
    is_active = db.Column(db.Boolean, default=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('admin.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)

# Forms
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=20)])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    farm_name = StringField('Farm Name', validators=[DataRequired(), Length(max=100)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

class CropForm(FlaskForm):
    name = StringField('Crop Name', validators=[DataRequired()])
    planting_date = DateField('Planting Date', validators=[DataRequired()], format='%Y-%m-%d')
    expected_harvest_date = DateField('Expected Harvest Date', validators=[DataRequired()], format='%Y-%m-%d')
    notes = TextAreaField('Notes')
    submit = SubmitField('Save Crop')

class LivestockForm(FlaskForm):
    type = SelectField('Livestock Type', choices=[('cow', 'Cow'), ('goat', 'Goat'), ('chicken', 'Chicken'), ('pig', 'Pig'), ('sheep', 'Sheep'), ('other', 'Other')], validators=[DataRequired()])
    breed = StringField('Breed')
    number = IntegerField('Number', validators=[DataRequired(), NumberRange(min=1)])
    health_status = SelectField('Health Status', choices=[('healthy', 'Healthy'), ('sick', 'Sick'), ('treatment', 'Under Treatment')], validators=[DataRequired()])
    notes = TextAreaField('Notes')
    submit = SubmitField('Save Livestock')

class ActivityForm(FlaskForm):
    type = SelectField('Activity Type', choices=[('planting', 'Planting'), ('watering', 'Watering'), ('fertilizing', 'Fertilizing'), ('harvesting', 'Harvesting'), ('feeding', 'Feeding'), ('treatment', 'Treatment'), ('other', 'Other')], validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    date = DateField('Date', validators=[DataRequired()], format='%Y-%m-%d')
    submit = SubmitField('Log Activity')

class ImageUploadForm(FlaskForm):
    image = FileField('Upload Image', validators=[DataRequired()])
    description = TextAreaField('Description')
    submit = SubmitField('Upload Image')

# Admin Forms
class AdminLoginForm(FlaskForm):
    username = StringField('Admin Username', validators=[DataRequired(), Length(min=4, max=20)])
    password = PasswordField('Admin Password', validators=[DataRequired()])
    submit = SubmitField('Admin Login')

class CropInfoForm(FlaskForm):
    crop_name = StringField('Crop Name', validators=[DataRequired(), Length(max=100)])
    best_planting_season = StringField('Best Planting Season', validators=[DataRequired(), Length(max=100)])
    planting_tips = TextAreaField('Planting Tips')
    growing_period_days = IntegerField('Growing Period (Days)', validators=[NumberRange(min=1)])
    water_requirements = StringField('Water Requirements', validators=[Length(max=200)])
    soil_type = StringField('Soil Type', validators=[Length(max=100)])
    submit = SubmitField('Save Crop Info')

class MarketPriceForm(FlaskForm):
    crop_name = StringField('Crop Name', validators=[DataRequired(), Length(max=100)])
    price_per_kg = FloatField('Price per KG (KES)', validators=[DataRequired(), NumberRange(min=0)])
    market_location = StringField('Market Location', validators=[DataRequired(), Length(max=100)])
    trend = SelectField('Price Trend', choices=[('increasing', 'Increasing'), ('decreasing', 'Decreasing'), ('stable', 'Stable')])
    submit = SubmitField('Update Price')

class FarmerAlertForm(FlaskForm):
    title = StringField('Alert Title', validators=[DataRequired(), Length(max=200)])
    message = TextAreaField('Alert Message', validators=[DataRequired()])
    alert_type = SelectField('Alert Type', choices=[
        ('general', 'General'),
        ('weather', 'Weather Alert'),
        ('market', 'Market Update'),
        ('disease', 'Disease Warning')
    ])
    target_audience = SelectField('Target Audience', choices=[
        ('all', 'All Farmers'),
        ('specific', 'Specific Farmers')
    ])
    target_users = TextAreaField('Target Users (comma-separated usernames for specific targeting)')
    expires_hours = IntegerField('Expires in Hours', default=24, validators=[NumberRange(min=1)])
    submit = SubmitField('Send Alert')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = RegisterForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            farm_name=form.farm_name.data
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    total_crops = Crop.query.filter_by(user_id=current_user.id).count()
    total_livestock = db.session.query(db.func.sum(Livestock.number)).filter_by(user_id=current_user.id).scalar() or 0
    recent_activities = Activity.query.filter_by(user_id=current_user.id).order_by(Activity.created_at.desc()).limit(5).all()
    
    # Get crops ready for harvest
    ready_crops = Crop.query.filter(
        Crop.user_id == current_user.id,
        Crop.expected_harvest_date <= datetime.utcnow().date(),
        Crop.status == 'growing'
    ).all()
    
    # Get recent images
    recent_images = FarmImage.query.filter_by(user_id=current_user.id).order_by(FarmImage.created_at.desc()).limit(3).all()
    
    return render_template('dashboard.html', 
                         total_crops=total_crops,
                         total_livestock=total_livestock,
                         recent_activities=recent_activities,
                         ready_crops=ready_crops,
                         recent_images=recent_images,
                         now=datetime.now)

@app.route('/crops')
@login_required
def crops():
    crop_list = Crop.query.filter_by(user_id=current_user.id).order_by(Crop.created_at.desc()).all()
    return render_template('crops.html', crops=crop_list, now=datetime.now)

@app.route('/crops/add', methods=['GET', 'POST'])
@login_required
def add_crop():
    form = CropForm()
    if form.validate_on_submit():
        crop = Crop(
            name=form.name.data,
            planting_date=form.planting_date.data,
            expected_harvest_date=form.expected_harvest_date.data,
            notes=form.notes.data,
            user_id=current_user.id
        )
        db.session.add(crop)
        db.session.commit()
        
        # Log planting activity
        activity = Activity(
            type='planting',
            description=f'Planted {form.name.data}',
            date=form.planting_date.data,
            crop_id=crop.id,
            user_id=current_user.id
        )
        db.session.add(activity)
        db.session.commit()
        
        flash('Crop added successfully!', 'success')
        return redirect(url_for('crops'))
    
    return render_template('crop_form.html', form=form, title='Add Crop')

@app.route('/crops/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_crop(id):
    crop = Crop.query.get_or_404(id)
    if crop.user_id != current_user.id:
        flash('Access denied!', 'danger')
        return redirect(url_for('crops'))
    
    form = CropForm(obj=crop)
    if form.validate_on_submit():
        crop.name = form.name.data
        crop.planting_date = form.planting_date.data
        crop.expected_harvest_date = form.expected_harvest_date.data
        crop.notes = form.notes.data
        db.session.commit()
        flash('Crop updated successfully!', 'success')
        return redirect(url_for('crops'))
    
    return render_template('crop_form.html', form=form, title='Edit Crop')

@app.route('/crops/delete/<int:id>')
@login_required
def delete_crop(id):
    crop = Crop.query.get_or_404(id)
    if crop.user_id != current_user.id:
        flash('Access denied!', 'danger')
        return redirect(url_for('crops'))
    
    db.session.delete(crop)
    db.session.commit()
    flash('Crop deleted successfully!', 'success')
    return redirect(url_for('crops'))

@app.route('/livestock')
@login_required
def livestock():
    livestock_list = Livestock.query.filter_by(user_id=current_user.id).order_by(Livestock.created_at.desc()).all()
    return render_template('livestock.html', livestock_list=livestock_list)

@app.route('/livestock/add', methods=['GET', 'POST'])
@login_required
def add_livestock():
    form = LivestockForm()
    if form.validate_on_submit():
        animal = Livestock(
            type=form.type.data,
            breed=form.breed.data,
            number=form.number.data,
            health_status=form.health_status.data,
            notes=form.notes.data,
            user_id=current_user.id
        )
        db.session.add(animal)
        db.session.commit()
        flash('Livestock added successfully!', 'success')
        return redirect(url_for('livestock'))
    
    return render_template('livestock_form.html', form=form, title='Add Livestock')

@app.route('/livestock/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_livestock(id):
    animal = Livestock.query.get_or_404(id)
    if animal.user_id != current_user.id:
        flash('Access denied!', 'danger')
        return redirect(url_for('livestock'))
    
    form = LivestockForm(obj=animal)
    if form.validate_on_submit():
        animal.type = form.type.data
        animal.breed = form.breed.data
        animal.number = form.number.data
        animal.health_status = form.health_status.data
        animal.notes = form.notes.data
        db.session.commit()
        flash('Livestock updated successfully!', 'success')
        return redirect(url_for('livestock'))
    
    return render_template('livestock_form.html', form=form, title='Edit Livestock')

@app.route('/livestock/delete/<int:id>')
@login_required
def delete_livestock(id):
    animal = Livestock.query.get_or_404(id)
    if animal.user_id != current_user.id:
        flash('Access denied!', 'danger')
        return redirect(url_for('livestock'))
    
    db.session.delete(animal)
    db.session.commit()
    flash('Livestock deleted successfully!', 'success')
    return redirect(url_for('livestock'))

@app.route('/weather', methods=['GET', 'POST'])
@login_required
def weather():
    # Kenyan counties with their coordinates
    kenya_counties = {
        'Nairobi': {'lat': -1.2921, 'lon': 36.8219, 'name': 'Nairobi'},
        'Mombasa': {'lat': -4.0435, 'lon': 39.6682, 'name': 'Mombasa'},
        'Kisumu': {'lat': -0.0917, 'lon': 34.7680, 'name': 'Kisumu'},
        'Nakuru': {'lat': -0.3031, 'lon': 36.0685, 'name': 'Nakuru'},
        'Eldoret': {'lat': 0.5143, 'lon': 35.2694, 'name': 'Eldoret'},
        'Kitale': {'lat': 1.0150, 'lon': 35.0030, 'name': 'Kitale'},
        'Garissa': {'lat': -0.4529, 'lon': 39.6460, 'name': 'Garissa'},
        'Kakuma': {'lat': 3.2833, 'lon': 35.0167, 'name': 'Kakuma'},
        'Lodwar': {'lat': 3.1208, 'lon': 35.6167, 'name': 'Lodwar'},
        'Mandera': {'lat': 3.9371, 'lon': 41.8569, 'name': 'Mandera'},
        'Wajir': {'lat': 1.7471, 'lon': 40.0548, 'name': 'Wajir'},
        'Marsabit': {'lat': 2.3286, 'lon': 37.9900, 'name': 'Marsabit'},
        'Isiolo': {'lat': 0.3538, 'lon': 37.5833, 'name': 'Isiolo'},
        'Meru': {'lat': 0.0419, 'lon': 37.6548, 'name': 'Meru'},
        'Embu': {'lat': -0.5313, 'lon': 37.4520, 'name': 'Embu'},
        'Thika': {'lat': -1.0333, 'lon': 37.0694, 'name': 'Thika'},
        'Nyeri': {'lat': -0.4235, 'lon': 36.9511, 'name': 'Nyeri'},
        'Kerugoya': {'lat': -0.7083, 'lon': 37.1833, 'name': 'Kerugoya'},
        'Muranga': {'lat': -0.7167, 'lon': 37.1500, 'name': 'Muranga'},
        'Kericho': {'lat': -0.3676, 'lon': 35.2853, 'name': 'Kericho'},
        'Bomet': {'lat': -0.7333, 'lon': 35.3500, 'name': 'Bomet'},
        'Narok': {'lat': -1.0781, 'lon': 35.8701, 'name': 'Narok'},
        'Kajiado': {'lat': -1.8536, 'lon': 36.8333, 'name': 'Kajiado'},
        'Naivasha': {'lat': -0.7133, 'lon': 36.4333, 'name': 'Naivasha'},
        'Busia': {'lat': 0.4600, 'lon': 34.1111, 'name': 'Busia'},
        'Kakamega': {'lat': 0.2842, 'lon': 34.7525, 'name': 'Kakamega'},
        'Bungoma': {'lat': 0.5635, 'lon': 34.5605, 'name': 'Bungoma'},
        'Kitui': {'lat': -1.3742, 'lon': 38.0155, 'name': 'Kitui'},
        'Machakos': {'lat': -1.5177, 'lon': 37.2634, 'name': 'Machakos'},
        'Makueni': {'lat': -1.8041, 'lon': 37.6193, 'name': 'Makueni'},
        'Taveta': {'lat': -3.4034, 'lon': 37.6882, 'name': 'Taveta'},
        'Voi': {'lat': -3.3955, 'lon': 38.5584, 'name': 'Voi'},
        'Malindi': {'lat': -3.2192, 'lon': 40.1164, 'name': 'Malindi'},
        'Lamu': {'lat': -2.2717, 'lon': 40.9020, 'name': 'Lamu'},
        'Homa Bay': {'lat': -0.5278, 'lon': 34.4638, 'name': 'Homa Bay'},
        'Migori': {'lat': -1.0635, 'lon': 34.4731, 'name': 'Migori'},
        'Kisii': {'lat': -0.6817, 'lon': 34.7667, 'name': 'Kisii'},
        'Nyamira': {'lat': -0.5333, 'lon': 34.9000, 'name': 'Nyamira'},
        'Sotik': {'lat': -0.7833, 'lon': 35.6000, 'name': 'Sotik'},
        'Kilifi': {'lat': -3.6333, 'lon': 39.8500, 'name': 'Kilifi'},
        'Kwale': {'lat': -4.3333, 'lon': 39.4500, 'name': 'Kwale'},
        'Tana River': {'lat': -1.8667, 'lon': 40.0000, 'name': 'Tana River'},
        'West Pokot': {'lat': 1.8667, 'lon': 35.1333, 'name': 'West Pokot'},
        'Samburu': {'lat': 1.0000, 'lon': 37.5000, 'name': 'Samburu'},
        'Turkana': {'lat': 2.5000, 'lon': 35.0000, 'name': 'Turkana'},
        'Baringo': {'lat': 0.5000, 'lon': 36.0000, 'name': 'Baringo'},
        'Laikipia': {'lat': 0.0000, 'lon': 37.0000, 'name': 'Laikipia'},
        'Nandi': {'lat': 0.0000, 'lon': 35.0000, 'name': 'Nandi'},
        'Uasin Gishu': {'lat': 0.5000, 'lon': 35.0000, 'name': 'Uasin Gishu'},
        'Elgeyo Marakwet': {'lat': 1.0000, 'lon': 35.5000, 'name': 'Elgeyo Marakwet'},
        'Trans Nzoia': {'lat': 1.0000, 'lon': 35.0000, 'name': 'Trans Nzoia'},
        'Pokot': {'lat': 1.8667, 'lon': 35.1333, 'name': 'Pokot'},
        'Marakwet': {'lat': 1.0000, 'lon': 35.5000, 'name': 'Marakwet'}
    }
    
    selected_county = request.form.get('county', 'Nairobi') if request.method == 'POST' else 'Nairobi'
    county_info = kenya_counties.get(selected_county, kenya_counties['Nairobi'])
    
    api_key = os.getenv('WEATHER_API_KEY', 'demo_key')
    
    # For demo purposes, return realistic mock data for each county
    if api_key == 'demo_key' or api_key == 'your-openweather-api-key-here':
        # Different weather data for different regions
        if selected_county in ['Mombasa', 'Malindi', 'Lamu', 'Kilifi', 'Kwale']:  # Coastal counties
            weather_data = {
                'city': county_info['name'],
                'temperature': 32,
                'description': 'Hot and humid',
                'humidity': 75,
                'wind_speed': 15,
                'icon': 'sun'
            }
        elif selected_county in ['Nairobi', 'Kiambu', 'Kajiado', 'Machakos', 'Muranga']:  # Central counties
            weather_data = {
                'city': county_info['name'],
                'temperature': 22,
                'description': 'Partly cloudy',
                'humidity': 60,
                'wind_speed': 12,
                'icon': 'partly-cloudy'
            }
        elif selected_county in ['Kisumu', 'Siaya', 'Homa Bay', 'Migori', 'Kisii']:  # Lake Victoria counties
            weather_data = {
                'city': county_info['name'],
                'temperature': 26,
                'description': 'Warm and breezy',
                'humidity': 70,
                'wind_speed': 18,
                'icon': 'wind'
            }
        elif selected_county in ['Turkana', 'Marsabit', 'Isiolo', 'Garissa', 'Wajir']:  # Northern counties
            weather_data = {
                'city': county_info['name'],
                'temperature': 35,
                'description': 'Hot and dry',
                'humidity': 25,
                'wind_speed': 20,
                'icon': 'sun'
            }
        elif selected_county in ['Eldoret', 'Uasin Gishu', 'Nandi', 'Trans Nzoia']:  # Rift Valley highlands
            weather_data = {
                'city': county_info['name'],
                'temperature': 20,
                'description': 'Cool and pleasant',
                'humidity': 55,
                'wind_speed': 10,
                'icon': 'cloud'
            }
        else:  # Default for other counties
            weather_data = {
                'city': county_info['name'],
                'temperature': 24,
                'description': 'Moderate conditions',
                'humidity': 65,
                'wind_speed': 14,
                'icon': 'partly-cloudy'
            }
    else:
        try:
            # Use coordinates for more accurate weather data
            url = f'http://api.openweathermap.org/data/2.5/weather?lat={county_info["lat"]}&lon={county_info["lon"]}&appid={api_key}&units=metric'
            response = requests.get(url)
            data = response.json()
            
            if response.status_code == 200 and 'main' in data:
                weather_data = {
                    'city': county_info['name'],
                    'temperature': round(data['main']['temp']),
                    'description': data['weather'][0]['description'],
                    'humidity': data['main']['humidity'],
                    'wind_speed': round(data['wind']['speed'], 1),
                    'icon': data['weather'][0]['main'].lower()
                }
            else:
                weather_data = {'error': f'Unable to fetch weather data for {county_info["name"]}. Please try again later.'}
        except Exception as e:
            weather_data = {'error': f'Weather service unavailable. Using demo data for {county_info["name"]}.',
                          'city': county_info['name'],
                          'temperature': 24,
                          'description': 'Demo data',
                          'humidity': 65,
                          'wind_speed': 12,
                          'icon': 'partly-cloudy'}
    
    return render_template('weather.html', weather=weather_data, counties=kenya_counties, selected_county=selected_county, csrf_token=generate_csrf())

@app.route('/activities')
@login_required
def activities():
    activity_list = Activity.query.filter_by(user_id=current_user.id).order_by(Activity.date.desc()).all()
    return render_template('activities.html', activities=activity_list)

@app.route('/activities/add', methods=['GET', 'POST'])
@login_required
def add_activity():
    form = ActivityForm()
    if form.validate_on_submit():
        activity = Activity(
            type=form.type.data,
            description=form.description.data,
            date=form.date.data,
            user_id=current_user.id
        )
        db.session.add(activity)
        db.session.commit()
        flash('Activity logged successfully!', 'success')
        return redirect(url_for('activities'))
    
    return render_template('activity_form.html', form=form, title='Log Activity')

@app.route('/gallery')
@login_required
def gallery():
    images = FarmImage.query.filter_by(user_id=current_user.id).order_by(FarmImage.created_at.desc()).all()
    return render_template('gallery.html', images=images)

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload_image():
    form = ImageUploadForm()
    if form.validate_on_submit():
        image = form.image.data
        if image:
            filename = secure_filename(image.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{timestamp}_{filename}"
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            
            farm_image = FarmImage(
                filename=filename,
                description=form.description.data,
                user_id=current_user.id
            )
            db.session.add(farm_image)
            db.session.commit()
            flash('Image uploaded successfully!', 'success')
            return redirect(url_for('gallery'))
    
    return render_template('upload.html', form=form)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/notifications')
@login_required
def notifications():
    # Get crops that need attention
    today = datetime.utcnow().date()
    
    # Crops ready for harvest
    ready_crops = Crop.query.filter(
        Crop.user_id == current_user.id,
        Crop.expected_harvest_date <= today,
        Crop.status == 'growing'
    ).all()
    
    # Crops that need watering (simplified - every 3 days after planting)
    watering_needed = []
    crops = Crop.query.filter_by(user_id=current_user.id, status='growing').all()
    for crop in crops:
        days_since_planting = (today - crop.planting_date).days
        if days_since_planting > 0 and days_since_planting % 3 == 0:
            watering_needed.append(crop)
    
    # Sick livestock
    sick_animals = Livestock.query.filter_by(user_id=current_user.id, health_status='sick').all()
    
    return render_template('notifications.html', 
                         ready_crops=ready_crops,
                         watering_needed=watering_needed,
                         sick_animals=sick_animals)

# AI Farming Assistant Routes
@app.route('/ai-assistant')
@login_required
def ai_assistant():
    return render_template('ai_assistant.html')

@app.route('/ai-diagnose', methods=['POST'])
@login_required
def ai_diagnose():
    crop_name = request.form.get('crop_name', '').lower()
    symptoms = request.form.get('symptoms', '').lower()
    livestock_type = request.form.get('livestock_type', '').lower()
    animal_symptoms = request.form.get('animal_symptoms', '').lower()
    
    # Handle photo uploads
    crop_photo = request.files.get('crop_photo')
    animal_photo = request.files.get('animal_photo')
    
    diagnosis = ""
    recommendations = []
    urgency = "low"
    photo_info = ""
    
    if crop_name and symptoms:
        diagnosis, recommendations, urgency = diagnose_crop_disease(crop_name, symptoms)
        if crop_photo:
            photo_info = f"Photo uploaded: {crop_photo.filename} (Size: {crop_photo.content_length // 1024}KB)"
    elif livestock_type and animal_symptoms:
        diagnosis, recommendations, urgency = diagnose_livestock_disease(livestock_type, animal_symptoms)
        if animal_photo:
            photo_info = f"Photo uploaded: {animal_photo.filename} (Size: {animal_photo.content_length // 1024}KB)"
    else:
        diagnosis = "Please provide both crop/livestock information and symptoms for accurate diagnosis."
        recommendations = ["Ensure you provide detailed symptoms for better AI analysis."]
        urgency = "low"
    
    return render_template('ai_assistant.html', 
                         diagnosis=diagnosis,
                         recommendations=recommendations,
                         urgency=urgency,
                         crop_name=crop_name.title() if crop_name else '',
                         livestock_type=livestock_type.title() if livestock_type else '',
                         symptoms=symptoms,
                         animal_symptoms=animal_symptoms,
                         photo_info=photo_info)

def diagnose_crop_disease(crop_name, symptoms):
    """AI-powered crop disease diagnosis"""
    disease_database = {
        'maize': {
            'yellow leaves': {
                'diagnosis': 'Nitrogen Deficiency',
                'recommendations': [
                    'Apply nitrogen-rich fertilizer (UREA or CAN)',
                    'Increase soil pH with lime if below 6.0',
                    'Add organic matter like compost or manure',
                    'Consider foliar spray for quick recovery'
                ],
                'urgency': 'medium'
            },
            'wilting': {
                'diagnosis': 'Drought Stress or Root Rot',
                'recommendations': [
                    'Check soil moisture and water appropriately',
                    'Improve drainage if waterlogged',
                    'Apply fungicide if root rot suspected',
                    'Mulch to retain soil moisture'
                ],
                'urgency': 'high'
            },
            'spots on leaves': {
                'diagnosis': 'Leaf Blight or Fungal Infection',
                'recommendations': [
                    'Apply copper-based fungicide immediately',
                    'Remove affected leaves to prevent spread',
                    'Ensure proper air circulation',
                    'Avoid overhead watering'
                ],
                'urgency': 'high'
            },
            'stunted growth': {
                'diagnosis': 'Nutrient Deficiency or Soil Problems',
                'recommendations': [
                    'Test soil for nutrient levels',
                    'Apply balanced NPK fertilizer',
                    'Check for pest infestation in roots',
                    'Consider crop rotation next season'
                ],
                'urgency': 'medium'
            }
        },
        'tomatoes': {
            'yellow leaves': {
                'diagnosis': 'Early Blight or Nutrient Deficiency',
                'recommendations': [
                    'Apply fungicide spray (Mancozeb or Copper)',
                    'Remove lower affected leaves',
                    'Ensure proper spacing for air circulation',
                    'Add calcium to prevent blossom end rot'
                ],
                'urgency': 'medium'
            },
            'wilting': {
                'diagnosis': 'Bacterial Wilt or Fusarium Wilt',
                'recommendations': [
                    'Remove and destroy infected plants immediately',
                    'Soil solarization before next planting',
                    'Use disease-resistant varieties',
                    'Avoid overwatering'
                ],
                'urgency': 'high'
            },
            'white powder': {
                'diagnosis': 'Powdery Mildew',
                'recommendations': [
                    'Apply sulfur-based fungicide',
                    'Increase air circulation',
                    'Reduce humidity around plants',
                    'Remove affected plant parts'
                ],
                'urgency': 'medium'
            },
            'fruit rot': {
                'diagnosis': 'Anthracnose or Fruit Rot',
                'recommendations': [
                    'Apply appropriate fungicide immediately',
                    'Harvest ripe fruits promptly',
                    'Improve air circulation',
                    'Use drip irrigation instead of overhead'
                ],
                'urgency': 'high'
            }
        },
        'beans': {
            'yellow spots': {
                'diagnosis': 'Angular Leaf Spot',
                'recommendations': [
                    'Apply copper-based fungicide',
                    'Remove infected plant debris',
                    'Use certified disease-free seeds',
                    'Practice crop rotation'
                ],
                'urgency': 'medium'
            },
            'wilting': {
                'diagnosis': 'Root Rot or Bacterial Blight',
                'recommendations': [
                    'Improve soil drainage',
                    'Apply soil drench fungicide',
                    'Avoid overwatering',
                    'Use resistant varieties'
                ],
                'urgency': 'high'
            },
            'powdery mildew': {
                'diagnosis': 'Powdery Mildew Infection',
                'recommendations': [
                    'Apply sulfur fungicide',
                    'Reduce plant density',
                    'Ensure proper ventilation',
                    'Remove affected leaves'
                ],
                'urgency': 'medium'
            }
        },
        'kale': {
            'holes in leaves': {
                'diagnosis': 'Caterpillar or Aphid Damage',
                'recommendations': [
                    'Apply organic pesticide (neem oil)',
                    'Introduce beneficial insects',
                    'Hand-pick larger caterpillars',
                    'Use row covers for young plants'
                ],
                'urgency': 'medium'
            },
            'yellowing': {
                'diagnosis': 'Nutrient Deficiency',
                'recommendations': [
                    'Apply nitrogen-rich fertilizer',
                    'Add compost to soil',
                    'Check soil pH',
                    'Ensure adequate watering'
                ],
                'urgency': 'low'
            },
            'curling leaves': {
                'diagnosis': 'Aphid Infestation',
                'recommendations': [
                    'Apply soapy water spray',
                    'Release ladybugs for natural control',
                    'Use reflective mulch',
                    'Monitor for ant activity'
                ],
                'urgency': 'medium'
            }
        }
    }
    
    # Check for symptom matches
    if crop_name in disease_database:
        for symptom_key, disease_info in disease_database[crop_name].items():
            if symptom_key in symptoms or any(word in symptoms for word in symptom_key.split()):
                return (
                    disease_info['diagnosis'],
                    disease_info['recommendations'],
                    disease_info['urgency']
                )
    
    # Default response if no specific match
    return (
        f"General crop health issue detected for {crop_name.title()}",
        [
            "Conduct soil testing to identify nutrient deficiencies",
            "Check for pest infestation and apply appropriate control measures",
            "Ensure proper watering and drainage",
            "Consider consulting local agricultural extension officer",
            "Apply balanced fertilizer as a general treatment"
        ],
        "medium"
    )

def diagnose_livestock_disease(livestock_type, symptoms):
    """AI-powered livestock disease diagnosis"""
    disease_database = {
        'cattle': {
            'loss of appetite': {
                'diagnosis': 'Digestive Issues or General Illness',
                'recommendations': [
                    'Isolate the animal from the herd',
                    'Provide clean water and high-quality forage',
                    'Monitor temperature twice daily',
                    'Consult veterinarian if symptoms persist > 24 hours',
                    'Check for signs of bloat or indigestion'
                ],
                'urgency': 'medium'
            },
            'diarrhea': {
                'diagnosis': 'Bacterial or Parasitic Infection',
                'recommendations': [
                    'Provide electrolytes to prevent dehydration',
                    'Collect fecal sample for laboratory testing',
                    'Administer deworming medication',
                    'Clean and disinfect feeding area',
                    'Isolate from healthy animals'
                ],
                'urgency': 'high'
            },
            'lameness': {
                'diagnosis': 'Foot Injury or Joint Issues',
                'recommendations': [
                    'Examine hooves for foreign objects or injury',
                    'Clean and disinfect affected area',
                    'Provide soft bedding and rest',
                    'Check for signs of foot rot',
                    'Consult veterinarian for persistent lameness'
                ],
                'urgency': 'medium'
            },
            'coughing': {
                'diagnosis': 'Respiratory Infection',
                'recommendations': [
                    'Isolate to prevent spread to herd',
                    'Provide clean, dust-free environment',
                    'Monitor temperature and breathing',
                    'Consult veterinarian for antibiotics',
                    'Ensure proper ventilation in housing'
                ],
                'urgency': 'high'
            },
            'weight loss': {
                'diagnosis': 'Malnutrition or Parasitic Load',
                'recommendations': [
                    'Conduct fecal egg count test',
                    'Implement strategic deworming program',
                    'Improve nutrition with quality feed',
                    'Check teeth for chewing problems',
                    'Monitor feed intake and competition'
                ],
                'urgency': 'medium'
            }
        },
        'goats': {
            'bloating': {
                'diagnosis': 'Acute Bloat - Emergency Condition',
                'recommendations': [
                    'EMERGENCY: Call veterinarian immediately',
                    'Keep animal standing and walking',
                    'Massage rumen area gently',
                    'Administer anti-foaming agents if available',
                    'Do not allow to lie down'
                ],
                'urgency': 'high'
            },
            'diarrhea': {
                'diagnosis': 'Coccidiosis or Bacterial Enteritis',
                'recommendations': [
                    'Isolate and provide supportive care',
                    'Administer oral rehydration salts',
                    'Give coccidiostat medication',
                    'Clean and disinfect living area',
                    'Consult veterinarian for proper diagnosis'
                ],
                'urgency': 'high'
            },
            'limping': {
                'diagnosis': 'Foot Rot or Injury',
                'recommendations': [
                    'Examine and clean hooves thoroughly',
                    'Trim hooves if overgrown',
                    'Apply foot rot medication',
                    'Provide dry, clean bedding',
                    'Separate from rest of flock'
                ],
                'urgency': 'medium'
            },
            'not eating': {
                'diagnosis': 'Stress or Digestive Issues',
                'recommendations': [
                    'Offer favorite treats to encourage eating',
                    'Check for dental problems',
                    'Monitor for other symptoms',
                    'Ensure fresh water is available',
                    'Reduce stress factors'
                ],
                'urgency': 'medium'
            }
        },
        'chicken': {
            'sneezing': {
                'diagnosis': 'Respiratory Infection or Environmental Irritation',
                'recommendations': [
                    'Improve coop ventilation',
                    'Clean and disinfect waterers and feeders',
                    'Separate sick birds',
                    'Add vitamins to water',
                    'Consult vet for antibiotics if needed'
                ],
                'urgency': 'medium'
            },
            'diarrhea': {
                'diagnosis': 'Coccidiosis or Bacterial Infection',
                'recommendations': [
                    'Administer coccidiostat in water',
                    'Clean litter and bedding',
                    'Provide clean water and electrolytes',
                    'Isolate affected birds',
                    'Improve sanitation practices'
                ],
                'urgency': 'high'
            },
            'lethargic': {
                'diagnosis': 'General Illness or Nutritional Deficiency',
                'recommendations': [
                    'Check for external parasites',
                    'Provide vitamin supplements',
                    'Ensure adequate heat and shelter',
                    'Monitor food and water intake',
                    'Separate for close observation'
                ],
                'urgency': 'medium'
            },
            'feather loss': {
                'diagnosis': 'Molting or Parasite Infestation',
                'recommendations': [
                    'Check for mites and lice',
                    'Provide protein-rich feed during molting',
                    'Dust with appropriate pesticide if needed',
                    'Clean and disinfect coop',
                    'Reduce stress factors'
                ],
                'urgency': 'low'
            }
        },
        'sheep': {
            'limping': {
                'diagnosis': 'Foot Rot or Foot Scald',
                'recommendations': [
                    'Trim and clean hooves thoroughly',
                    'Apply foot rot medication',
                    'Provide dry, clean pasture',
                    'Separate from healthy sheep',
                    'Implement foot bathing program'
                ],
                'urgency': 'medium'
            },
            'weight loss': {
                'diagnosis': 'Parasitic Worm Load or Poor Nutrition',
                'recommendations': [
                    'Administer broad-spectrum dewormer',
                    'Improve pasture management',
                    'Provide supplemental feeding',
                    'Check teeth for problems',
                    'Monitor body condition score'
                ],
                'urgency': 'medium'
            },
            'coughing': {
                'diagnosis': 'Pneumonia or Lungworm Infection',
                'recommendations': [
                    'Isolate affected sheep immediately',
                    'Provide shelter from weather',
                    'Consult veterinarian for antibiotics',
                    'Reduce stress and handling',
                    'Improve ventilation in housing'
                ],
                'urgency': 'high'
            }
        }
    }
    
    # Check for symptom matches
    if livestock_type in disease_database:
        for symptom_key, disease_info in disease_database[livestock_type].items():
            if symptom_key in symptoms or any(word in symptoms for word in symptom_key.split()):
                return (
                    disease_info['diagnosis'],
                    disease_info['recommendations'],
                    disease_info['urgency']
                )
    
    # Default response if no specific match
    return (
        f"General health concern detected for {livestock_type.title()}",
        [
            "Isolate the animal for observation",
            "Provide clean water and appropriate feed",
            "Monitor temperature and behavior closely",
            "Maintain clean living conditions",
            "Consult veterinarian if symptoms persist or worsen"
        ],
        "medium"
    )

# Admin Routes
@app.route('/admin')
def admin_login():
    form = AdminLoginForm()
    return render_template('admin_login.html', form=form, csrf_token=generate_csrf())

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_authenticate():
    form = AdminLoginForm()
    if form.validate_on_submit():
        admin = Admin.query.filter_by(username=form.username.data).first()
        if admin and admin.check_password(form.password.data):
            session['admin_id'] = admin.id
            session['admin_username'] = admin.username
            flash('Admin login successful!', 'success')
            return redirect(url_for('admin_dashboard'))
        flash('Invalid admin credentials', 'danger')
    return render_template('admin_login.html', form=form, csrf_token=generate_csrf())

@app.route('/admin/dashboard')
def admin_dashboard():
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))
    
    total_users = User.query.count()
    total_crops = Crop.query.count()
    total_livestock = Livestock.query.count()
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    recent_alerts = FarmerAlert.query.order_by(FarmerAlert.created_at.desc()).limit(5).all()
    
    return render_template('admin_dashboard.html', 
                         total_users=total_users,
                         total_crops=total_crops,
                         total_livestock=total_livestock,
                         recent_users=recent_users,
                         recent_alerts=recent_alerts)

@app.route('/admin/members')
def admin_members():
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))
    
    members = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin_members.html', members=members)

@app.route('/admin/crop-info')
def admin_crop_info():
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))
    
    crop_info = CropInfo.query.order_by(CropInfo.crop_name).all()
    return render_template('admin_crop_info.html', crop_info=crop_info)

@app.route('/admin/add-crop-info', methods=['GET', 'POST'])
def admin_add_crop_info():
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))
    
    form = CropInfoForm()
    if form.validate_on_submit():
        crop_info = CropInfo(
            crop_name=form.crop_name.data,
            best_planting_season=form.best_planting_season.data,
            planting_tips=form.planting_tips.data,
            growing_period_days=form.growing_period_days.data,
            water_requirements=form.water_requirements.data,
            soil_type=form.soil_type.data,
            admin_id=session['admin_id']
        )
        db.session.add(crop_info)
        db.session.commit()
        flash('Crop information added successfully!', 'success')
        return redirect(url_for('admin_crop_info'))
    
    return render_template('admin_crop_info_form.html', form=form, title='Add Crop Information', csrf_token=generate_csrf())

@app.route('/admin/crop-info/edit/<int:id>', methods=['GET', 'POST'])
def admin_edit_crop_info(id):
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))
    
    crop_info = CropInfo.query.get_or_404(id)
    form = CropInfoForm(obj=crop_info)
    if form.validate_on_submit():
        crop_info.crop_name = form.crop_name.data
        crop_info.best_planting_season = form.best_planting_season.data
        crop_info.planting_tips = form.planting_tips.data
        crop_info.growing_period_days = form.growing_period_days.data
        crop_info.water_requirements = form.water_requirements.data
        crop_info.soil_type = form.soil_type.data
        db.session.commit()
        flash('Crop information updated successfully!', 'success')
        return redirect(url_for('admin_crop_info'))
    
    return render_template('admin_crop_info_form.html', form=form, title='Edit Crop Information', csrf_token=generate_csrf())

@app.route('/admin/market-prices')
def admin_market_prices():
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))
    
    prices = MarketPrice.query.order_by(MarketPrice.price_date.desc()).all()
    return render_template('admin_market_prices.html', prices=prices)

@app.route('/admin/market-prices/add', methods=['GET', 'POST'])
def admin_add_market_price():
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))
    
    form = MarketPriceForm()
    if form.validate_on_submit():
        market_price = MarketPrice(
            crop_name=form.crop_name.data,
            price_per_kg=form.price_per_kg.data,
            market_location=form.market_location.data,
            trend=form.trend.data,
            admin_id=session['admin_id']
        )
        db.session.add(market_price)
        db.session.commit()
        flash('Market price added successfully!', 'success')
        return redirect(url_for('admin_market_prices'))
    
    return render_template('admin_market_price_form.html', form=form, title='Add Market Price', csrf_token=generate_csrf())

@app.route('/admin/alerts')
def admin_alerts():
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))
    
    alerts = FarmerAlert.query.order_by(FarmerAlert.created_at.desc()).all()
    return render_template('admin_alerts.html', alerts=alerts)

@app.route('/admin/alerts/send', methods=['GET', 'POST'])
def admin_send_alert():
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))
    
    form = FarmerAlertForm()
    farmers = User.query.order_by(User.username).all()
    
    if form.validate_on_submit():
        # Calculate expiration time
        expires_at = datetime.utcnow() + timedelta(hours=form.expires_hours.data)
        
        # Handle target users
        target_users_json = None
        if form.target_audience.data == 'specific':
            usernames = [u.strip() for u in form.target_users.data.split(',')]
            target_users = User.query.filter(User.username.in_(usernames)).all()
            target_users_json = str([str(u.id) for u in target_users])
        
        alert = FarmerAlert(
            title=form.title.data,
            message=form.message.data,
            alert_type=form.alert_type.data,
            target_audience=form.target_audience.data,
            target_users=target_users_json,
            expires_at=expires_at,
            admin_id=session['admin_id']
        )
        db.session.add(alert)
        db.session.commit()
        flash('Alert sent successfully!', 'success')
        return redirect(url_for('admin_alerts'))
    
    return render_template('admin_alert_form.html', form=form, title='Send Alert', csrf_token=generate_csrf(), farmers=farmers)

@app.route('/farmer-portal')
@login_required
def farmer_portal():
    # Get latest market prices, crop info, and alerts
    prices = MarketPrice.query.order_by(MarketPrice.price_date.desc()).limit(12).all()
    crop_info = CropInfo.query.order_by(CropInfo.crop_name).all()
    
    # Get alerts relevant to current user
    user_alerts = []
    all_alerts = FarmerAlert.query.order_by(FarmerAlert.created_at.desc()).limit(10).all()
    
    for alert in all_alerts:
        # Check if alert is for all users or specific to this user
        if (alert.target_audience == 'all' or 
            (alert.target_users and str(current_user.id) in alert.target_users)):
            user_alerts.append(alert)
    
    return render_template('farmer_portal.html', prices=prices, crop_info=crop_info, alerts=user_alerts)

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_id', None)
    session.pop('admin_username', None)
    flash('Admin logged out successfully!', 'info')
    return redirect(url_for('admin_login'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        
        # Create default admin if not exists
        if not Admin.query.filter_by(username='admin').first():
            default_admin = Admin(
                username='admin',
                email='admin@smartfarm.co.ke',
                full_name='SmartFarm Kenya Administrator'
            )
            default_admin.set_password('admin123')
            db.session.add(default_admin)
            db.session.commit()
            print("Default admin created: username: admin, password: admin123")
        
    app.run(debug=True, host='0.0.0.0', port=5000)
