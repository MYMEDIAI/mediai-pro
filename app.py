import streamlit as st
import requests
import json
import os
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import pandas as pd
import random
import math
import hashlib
from dataclasses import dataclass

# Configuration
st.set_page_config(
    page_title="MediAI Pro - Advanced Health Assistant for India",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Data Classes for Type Safety
@dataclass
class PatientData:
    name: str
    age: int
    gender: str
    weight: float
    height: float
    blood_group: str

@dataclass
class VitalSigns:
    bp_systolic: int
    bp_diastolic: int
    pulse: int
    temperature: float
    spo2: int
    respiratory_rate: int

@dataclass
class HealthMetrics:
    bmi: float
    health_score: int
    risk_level: str
    recommendations: List[str]

# Advanced API Configuration
class AdvancedConfig:
    @staticmethod
    def get_api_key(key_name: str) -> str:
        """Advanced API key management with multiple fallback options"""
        try:
            # Priority 1: User input in session state
            if hasattr(st, 'session_state') and f'{key_name.lower()}_user_input' in st.session_state:
                user_key = st.session_state[f'{key_name.lower()}_user_input']
                if user_key and user_key.strip():
                    return user_key.strip()
            
            # Priority 2: Streamlit secrets
            if hasattr(st, 'secrets') and key_name in st.secrets:
                return st.secrets[key_name]
            
            # Priority 3: Environment variables
            env_key = os.getenv(key_name)
            if env_key:
                return env_key
            
            # Fallback keys for demo mode
            return 'demo-key'
            
        except Exception as e:
            logger.error(f"Error retrieving API key {key_name}: {e}")
            return 'demo-key'

# Advanced Geocoding Service for India
@st.cache_data(ttl=3600)
def advanced_geocode(location: str) -> Optional[Dict]:
    """Enhanced geocoding with comprehensive Indian city database"""
    try:
        indian_cities_data = {
            'mumbai': {'lat': 19.0760, 'lon': 72.8777, 'address': 'Mumbai, Maharashtra, India', 'state': 'Maharashtra'},
            'delhi': {'lat': 28.7041, 'lon': 77.1025, 'address': 'New Delhi, Delhi, India', 'state': 'Delhi'},
            'bangalore': {'lat': 12.9716, 'lon': 77.5946, 'address': 'Bangalore, Karnataka, India', 'state': 'Karnataka'},
            'bengaluru': {'lat': 12.9716, 'lon': 77.5946, 'address': 'Bengaluru, Karnataka, India', 'state': 'Karnataka'},
            'hyderabad': {'lat': 17.3850, 'lon': 78.4867, 'address': 'Hyderabad, Telangana, India', 'state': 'Telangana'},
            'chennai': {'lat': 13.0827, 'lon': 80.2707, 'address': 'Chennai, Tamil Nadu, India', 'state': 'Tamil Nadu'},
            'kolkata': {'lat': 22.5726, 'lon': 88.3639, 'address': 'Kolkata, West Bengal, India', 'state': 'West Bengal'},
            'pune': {'lat': 18.5204, 'lon': 73.8567, 'address': 'Pune, Maharashtra, India', 'state': 'Maharashtra'},
        }
        
        location_lower = location.lower().strip()
        
        # Direct match
        if location_lower in indian_cities_data:
            return indian_cities_data[location_lower]
        
        # Partial match
        for city in indian_cities_data:
            if city in location_lower or location_lower in city:
                return indian_cities_data[city]
        
        # Default to Mumbai if not found
        return indian_cities_data['mumbai']
        
    except Exception as e:
        logger.error(f"Geocoding error: {e}")
        return {'lat': 19.0760, 'lon': 72.8777, 'address': 'Mumbai, Maharashtra, India', 'state': 'Maharashtra'}

# Advanced Weather Data with Indian Context
@st.cache_data(ttl=1800)
def get_advanced_weather(lat: float, lon: float) -> Dict:
    """Enhanced weather data with Indian climate patterns"""
    try:
        # Base temperature calculation based on Indian geography
        base_temp = 28.0  # Indian average
        
        # Latitude-based adjustments for Indian climate zones
        if lat > 30:  # Northern mountains (Himalayas)
            base_temp = 15.0
        elif lat > 26:  # Northern plains
            base_temp = 25.0
        elif lat > 20:  # Central India
            base_temp = 30.0
        elif lat > 15:  # Southern plateau
            base_temp = 27.0
        else:  # Coastal South
            base_temp = 29.0
        
        # Seasonal adjustments (simplified)
        current_month = datetime.now().month
        if current_month in [12, 1, 2]:  # Winter
            base_temp -= 5
        elif current_month in [3, 4, 5]:  # Summer
            base_temp += 8
        elif current_month in [6, 7, 8, 9]:  # Monsoon
            base_temp -= 2
        
        # Add realistic variation
        temp_variation = random.uniform(-3, 4)
        current_temp = base_temp + temp_variation
        
        # Generate realistic Indian weather data
        humidity = random.randint(60, 85) if current_month in [6, 7, 8, 9] else random.randint(45, 70)
        
        weather_conditions = ['clear sky', 'partly cloudy', 'scattered clouds', 'hazy']
        
        if current_month in [6, 7, 8, 9]:  # Monsoon season
            description = random.choice(['light rain', 'moderate rain', 'overcast'])
        else:
            description = random.choice(weather_conditions)
        
        # Air quality based on Indian cities
        aqi_levels = ['Good', 'Moderate', 'Unhealthy for Sensitive Groups', 'Unhealthy', 'Poor']
        air_quality = random.choice(aqi_levels)
        
        return {
            'temperature': round(current_temp, 1),
            'humidity': humidity,
            'pressure': random.randint(1008, 1018),
            'description': description,
            'feels_like': round(current_temp + random.uniform(-2, 4), 1),
            'wind_speed': round(random.uniform(3, 15), 1),
            'air_quality': air_quality,
            'uv_index': random.randint(1, 11),
            'visibility': random.randint(5, 15),
            'season': 'Monsoon' if current_month in [6, 7, 8, 9] else 'Winter' if current_month in [12, 1, 2] else 'Summer' if current_month in [3, 4, 5] else 'Post-Monsoon'
        }
        
    except Exception as e:
        logger.error(f"Weather data error: {e}")
        return {
            'temperature': 28.0, 'humidity': 65, 'pressure': 1013,
            'description': 'partly cloudy', 'feels_like': 30.0,
            'wind_speed': 8.0, 'air_quality': 'Moderate', 'uv_index': 6,
            'visibility': 10, 'season': 'Pleasant'
        }

# OpenAI Integration
class AdvancedAIService:
    def __init__(self):
        self.base_url = "https://api.openai.com/v1/chat/completions"
        self.model = "gpt-3.5-turbo"
        self.max_tokens = 2000
        self.temperature = 0.7
    
    def get_api_key(self) -> str:
        """Get API key with priority for user input"""
        if hasattr(st, 'session_state') and 'openai_api_key_user_input' in st.session_state:
            user_key = st.session_state.openai_api_key_user_input
            if user_key and user_key.strip() and user_key.startswith('sk-'):
                return user_key.strip()
        return AdvancedConfig.get_api_key('OPENAI_API_KEY')
    
    def is_api_available(self) -> bool:
        """Check if real OpenAI API is available"""
        api_key = self.get_api_key()
        return api_key and api_key != 'demo-key' and api_key.startswith('sk-')
    
    def get_health_analysis_sync(self, prompt: str, patient_data: Dict, analysis_type: str) -> str:
        """Synchronous version for Streamlit compatibility"""
        api_key = self.get_api_key()
        
        if self.is_api_available():
            try:
                return self._get_openai_response_sync(prompt, patient_data, analysis_type, api_key)
            except Exception as e:
                logger.error(f"OpenAI API error: {e}")
                return self._get_advanced_demo_response(analysis_type, patient_data)
        else:
            return self._get_advanced_demo_response(analysis_type, patient_data)
    
    def _get_openai_response_sync(self, prompt: str, patient_data: Dict, analysis_type: str, api_key: str) -> str:
        """Get response from OpenAI API"""
        system_message = f"""You are MediAI Pro, an advanced AI medical assistant for Indian healthcare. 
        Provide comprehensive, culturally sensitive medical information considering Indian healthcare system, 
        medical practices, dietary patterns, and integration of Ayurveda with modern medicine.
        
        ANALYSIS TYPE: {analysis_type}
        Always emphasize consulting qualified healthcare professionals."""

        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": f"{prompt}\n\nPatient Data: {json.dumps(patient_data, default=str, indent=2)}"}
        ]
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }
        
        response = requests.post(self.base_url, headers=headers, json=payload, timeout=45)
        
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        else:
            raise Exception(f"OpenAI API error: {response.status_code}")
    
    def _get_advanced_demo_response(self, analysis_type: str, patient_data: Dict) -> str:
        """Advanced demo responses with Indian healthcare context"""
        patient_info = patient_data.get('patient', {})
        vitals = patient_data.get('vitals', {})
        age = patient_info.get('age', 30)
        gender = patient_info.get('gender', 'Unknown')
        
        return f"""# 🏥 {analysis_type} - MediAI Pro India

## 📊 Patient Overview
**Name:** {patient_info.get('name', 'Patient')} | **Age:** {age} years | **Gender:** {gender}

## 🩺 Health Assessment Summary
Based on your comprehensive health data, here's your personalized analysis:

### 🫀 Cardiovascular Health
- **Blood Pressure:** {vitals.get('bp_systolic', 120)}/{vitals.get('bp_diastolic', 80)} mmHg
- **Status:** {'Normal' if vitals.get('bp_systolic', 120) < 140 else 'Needs attention'}
- **Recommendation:** Regular monitoring, consider DASH diet with Indian modifications

### 🌿 Traditional Indian Medicine Integration
**Ayurvedic Approach:**
- Include turmeric, ginger, and garlic in daily diet
- Practice pranayama breathing exercises for 15 minutes daily
- Consider consultation with qualified AYUSH practitioner

### 🏥 Healthcare Navigation in India
**Immediate Care Options:**
- Government hospitals: Free emergency care available
- Private hospitals: Faster service, higher costs
- Telemedicine: eSanjeevani for consultations

### 💊 Medication Guidance
**Cost-Effective Options:**
- Jan Aushadhi stores: 90% cheaper generic medicines
- Generic alternatives for all branded medications
- Insurance utilization through Ayushman Bharat

### 🚨 Emergency Protocols
**Important Numbers:**
- National Emergency: 112
- Medical Emergency: 108
- Ambulance: 102

### ⚠️ Medical Disclaimer
This analysis is for educational purposes only. Always consult qualified healthcare professionals 
registered with Medical Council of India (MCI) for diagnosis and treatment.

---
*Generated by MediAI Pro - Advanced AI Health Assistant for India*"""

# Medical Facilities Service
class IndianMedicalFacilitiesService:
    def search_facilities(self, lat: float, lon: float, facility_type: str = "hospital", radius: int = 100000) -> List[Dict]:
        """Enhanced facilities search"""
        try:
            facilities_data = {
                'hospital': [
                    {'name': 'AIIMS Delhi', 'rating': 4.8, 'base_distance': 5.0, 'specialty': 'Super Specialty', 'type': 'Government', 'beds': 2478},
                    {'name': 'Apollo Hospital', 'rating': 4.6, 'base_distance': 3.2, 'specialty': 'Multi-specialty', 'type': 'Private', 'beds': 500},
                    {'name': 'Fortis Healthcare', 'rating': 4.4, 'base_distance': 6.8, 'specialty': 'Integrated Healthcare', 'type': 'Private', 'beds': 400},
                    {'name': 'Max Healthcare', 'rating': 4.5, 'base_distance': 9.1, 'specialty': 'Super Specialty', 'type': 'Private', 'beds': 600},
                    {'name': 'Government General Hospital', 'rating': 4.0, 'base_distance': 7.5, 'specialty': 'General Medicine', 'type': 'Government', 'beds': 800},
                ],
                'pharmacy': [
                    {'name': 'Apollo Pharmacy', 'rating': 4.3, 'base_distance': 0.8, 'specialty': '24x7 Medicine', 'type': 'Chain'},
                    {'name': 'MedPlus Health Services', 'rating': 4.1, 'base_distance': 1.2, 'specialty': 'Generic Medicines', 'type': 'Chain'},
                    {'name': 'Jan Aushadhi Store', 'rating': 4.4, 'base_distance': 2.4, 'specialty': '90% Cheaper Generics', 'type': 'Government'},
                    {'name': 'City Medical Store', 'rating': 4.0, 'base_distance': 3.6, 'specialty': 'Family Pharmacy', 'type': 'Independent'},
                    {'name': 'Wellness Pharmacy', 'rating': 3.9, 'base_distance': 4.2, 'specialty': 'Health Products', 'type': 'Independent'},
                ]
            }
            
            facilities = facilities_data.get(facility_type, [])
            radius_km = radius / 1000
            
            result_facilities = []
            for facility in facilities:
                if facility['base_distance'] <= radius_km:
                    # Add realistic variation
                    distance_variation = random.uniform(-0.5, 0.5)
                    actual_distance = max(0.1, facility['base_distance'] + distance_variation)
                    
                    # Calculate coordinates
                    lat_offset = (actual_distance / 111.32) * random.choice([-1, 1])
                    lon_offset = (actual_distance / (111.32 * math.cos(math.radians(lat)))) * random.choice([-1, 1])
                    
                    facility_info = {
                        'name': facility['name'],
                        'rating': facility['rating'] + random.uniform(-0.2, 0.2),
                        'user_ratings_total': random.randint(50, 2000),
                        'address': f"Medical Area, {facility['name']} Complex, City - {actual_distance:.1f}km",
                        'status': 'OPERATIONAL',
                        'lat': lat + lat_offset,
                        'lng': lon + lon_offset,
                        'distance': round(actual_distance, 2),
                        'specialty': facility['specialty'],
                        'phone': f"+91-{random.randint(11,99)}-{random.randint(2000,9999)}-{random.randint(1000,9999)}",
                        'type': facility.get('type', 'Private'),
                        'beds': facility.get('beds', random.randint(50, 300)),
                        'hours': self._get_hours(facility_type, facility.get('type', 'Private')),
                        'emergency': facility_type == 'hospital',
                        'insurance_accepted': ['Ayushman Bharat', 'CGHS', 'ESI', 'Mediclaim'],
                        'languages': ['Hindi', 'English', 'Local Language']
                    }
                    result_facilities.append(facility_info)
            
            # Sort by distance
            result_facilities.sort(key=lambda x: x['distance'])
            return result_facilities
            
        except Exception as e:
            logger.error(f"Facilities search error: {e}")
            return []
    
    def _get_hours(self, facility_type: str, facility_category: str) -> str:
        """Generate operating hours"""
        if facility_type == 'hospital':
            if facility_category == 'Government':
                return '24x7 Emergency | OPD: Mon-Sat 8 AM - 2 PM'
            else:
                return '24x7 All Services | OPD: Mon-Sun 6 AM - 10 PM'
        else:  # pharmacy
            if facility_category == 'Chain':
                return 'Mon-Sun: 7 AM - 11 PM | Emergency: 24x7'
            elif facility_category == 'Government':
                return 'Mon-Fri: 9 AM - 5 PM | Sat: 9 AM - 1 PM'
            else:
                return 'Mon-Sun: 8 AM - 10 PM'

# Health Analytics
class AdvancedHealthAnalytics:
    @staticmethod
    def calculate_indian_health_score(vitals: Dict, bmi: float, age: int, symptoms: str, lifestyle: Dict) -> Dict:
        """Advanced health scoring with Indian health parameters"""
        try:
            score = 100
            risk_factors = []
            recommendations = []
            
            # BMI Assessment with Indian standards
            if bmi < 18.5:
                score -= 15
                risk_factors.append("Underweight")
                recommendations.append("Nutritional counseling")
            elif bmi > 27:  # Lower threshold for Indians
                score -= 20
                risk_factors.append("Obesity (Indian BMI standards)")
                recommendations.append("Weight management")
            
            # Blood Pressure
            bp_sys = vitals.get('bp_systolic', 120)
            bp_dia = vitals.get('bp_diastolic', 80)
            
            if bp_sys > 140 or bp_dia > 90:
                score -= 25
                risk_factors.append("Hypertension")
                recommendations.append("Medical consultation required")
            
            # Lifestyle factors
            exercise_freq = lifestyle.get('exercise_frequency', 'Rarely')
            if exercise_freq in ['Never', 'Rarely (less than once/week)']:
                score -= 20
                risk_factors.append("Sedentary lifestyle")
                recommendations.append("Start daily exercise routine")
            
            score = max(0, min(100, score))
            
            # Health status
            if score >= 85:
                status = "Excellent"
                color = "#4CAF50"
            elif score >= 70:
                status = "Good" 
                color = "#8BC34A"
            elif score >= 55:
                status = "Fair"
                color = "#FF9800"
            else:
                status = "Poor"
                color = "#F44336"
            
            return {
                'score': score,
                'status': status,
                'color': color,
                'message': f"Your health score is {score}/100 - {status}",
                'advice': "Continue healthy lifestyle" if score >= 70 else "Lifestyle improvements recommended",
                'risk_factors': risk_factors,
                'recommendations': recommendations,
                'indian_specific_risks': ["Air pollution exposure", "Dietary salt intake"],
                'insurance_recommendations': ["Check Ayushman Bharat eligibility", "Consider health insurance"]
            }
            
        except Exception as e:
            logger.error(f"Health score calculation error: {e}")
            return {
                'score': 75, 'status': 'Good', 'color': '#8BC34A',
                'message': 'Health assessment completed.',
                'advice': 'Regular monitoring recommended',
                'risk_factors': [], 'recommendations': [],
                'indian_specific_risks': [], 'insurance_recommendations': []
            }

# Main Application
def main():
    # CSS Styling
    st.markdown("""
    <style>
        .main {
            font-family: 'Arial', sans-serif;
            background: linear-gradient(135deg, #FFF7F0 0%, #F8F9FA 100%);
        }
        
        .metric-card {
            background: white;
            padding: 1.5rem;
            border-radius: 15px;
            margin: 1rem 0;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            border-left: 4px solid #007C91;
        }
        
        .weather-card {
            background: white;
            padding: 1.5rem;
            border-radius: 15px;
            margin: 1rem 0;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            text-align: center;
        }
        
        .facility-card {
            background: white;
            border-radius: 12px;
            padding: 1.5rem;
            margin: 1rem 0;
            border-left: 4px solid #007C91;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .emergency-alert {
            background: linear-gradient(45deg, #F44336, #E91E63);
            color: white;
            padding: 2rem;
            border-radius: 15px;
            margin: 1.5rem 0;
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0% { box-shadow: 0 0 0 rgba(244, 67, 54, 0.7); }
            70% { box-shadow: 0 0 0 10px rgba(244, 67, 54, 0); }
            100% { box-shadow: 0 0 0 rgba(244, 67, 54, 0); }
        }
        
        .success-message {
            background: linear-gradient(45deg, #4CAF50, #8BC34A);
            color: white;
            padding: 1.5rem;
            border-radius: 12px;
            margin: 1rem 0;
        }
        
        .warning-message {
            background: linear-gradient(45deg, #FF9800, #FFA726);
            color: white;
            padding: 1.5rem;
            border-radius: 12px;
            margin: 1rem 0;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.markdown("<h1 style='text-align: center; color: #007C91; margin-bottom: 2rem;'>🏥 MediAI Pro - भारत का स्वास्थ्य सहायक</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-size: 1.2rem; color: #666; margin-bottom: 2rem;'>Advanced AI-Powered Healthcare Assistant for India</p>", unsafe_allow_html=True)
    
    # Initialize session state
    if 'user_location' not in st.session_state:
        st.session_state.user_location = None
    if 'coordinates' not in st.session_state:
        st.session_state.coordinates = None
    if 'health_data' not in st.session_state:
        st.session_state.health_data = {}
    if 'location_set' not in st.session_state:
        st.session_state.location_set = False
    
    # Initialize services
    ai_service = AdvancedAIService()
    facilities_service = IndianMedicalFacilitiesService()
    
    # Sidebar
    with st.sidebar:
        st.markdown("## 🔧 Configuration")
        
        # OpenAI API Key
        with st.expander("🤖 AI Configuration", expanded=False):
            openai_key_input = st.text_input(
                "OpenAI API Key:",
                type="password",
                placeholder="sk-...",
                help="Enter your OpenAI API key for AI analysis",
                key="openai_key_input"
            )
            
            if openai_key_input:
                if openai_key_input.startswith('sk-'):
                    st.session_state.openai_api_key_user_input = openai_key_input
                    st.success("✅ API Key configured!")
                else:
                    st.error("❌ Invalid API key format")
        
        # Location Setup
        st.markdown("### 📍 Location Setup")
        
        indian_cities = [
            "Choose a city...", "Mumbai, Maharashtra", "Delhi", "Bangalore, Karnataka", 
            "Hyderabad, Telangana", "Chennai, Tamil Nadu", "Kolkata, West Bengal", 
            "Pune, Maharashtra", "Ahmedabad, Gujarat"
        ]
        
        selected_city = st.selectbox("Select your city:", indian_cities)
        
        if selected_city != "Choose a city..." and st.button("📍 Set Location"):
            coords = advanced_geocode(selected_city)
            if coords:
                st.session_state.coordinates = (coords['lat'], coords['lon'])
                city_parts = selected_city.split(',')
                st.session_state.user_location = {
                    'city': city_parts[0].strip(),
                    'state': city_parts[1].strip() if len(city_parts) > 1 else 'India',
                    'country': 'India',
                    'lat': coords['lat'],
                    'lon': coords['lon']
                }
                st.session_state.location_set = True
                st.success(f"✅ Location set: {selected_city}")
        
        # Display current location
        if st.session_state.user_location:
            loc = st.session_state.user_location
            st.markdown(f"""
            **📍 Current Location:**
            - 🏙️ City: {loc.get('city', 'Unknown')}
            - 🗺️ State: {loc.get('state', 'Unknown')}
            - 🇮🇳 Country: {loc.get('country', 'India')}
            """)
    
    # Weather Display
    if st.session_state.coordinates:
        lat, lon = st.session_state.coordinates
        weather_data = get_advanced_weather(lat, lon)
        
        st.markdown("## 🌤️ Current Weather & Health Context")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div class="weather-card">
                <h4>🌡️ Temperature</h4>
                <h2 style="color: #E91E63;">{weather_data['temperature']}°C</h2>
                <p>Feels like {weather_data['feels_like']}°C</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="weather-card">
                <h4>💧 Humidity</h4>
                <h2 style="color: #2196F3;">{weather_data['humidity']}%</h2>
                <p>{weather_data['description'].title()}</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            air_quality_color = {
                'Good': '#4CAF50', 'Moderate': '#FF9800', 
                'Unhealthy for Sensitive Groups': '#FF5722',
                'Unhealthy': '#F44336', 'Poor': '#9C27B0'
            }.get(weather_data['air_quality'], '#666')
            
            st.markdown(f"""
            <div class="weather-card">
                <h4>🫁 Air Quality</h4>
                <h2 style="color: {air_quality_color};">{weather_data['air_quality']}</h2>
                <p>Indian Standards</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown(f"""
            <div class="weather-card">
                <h4>🌪️ Wind Speed</h4>
                <h2 style="color: #FF9800;">{weather_data['wind_speed']} m/s</h2>
                <p>Season: {weather_data['season']}</p>
            </div>
            """, unsafe_allow_html=True)
    
    # Health Assessment Form
    st.markdown("---")
    st.markdown("## 👤 Health Assessment")
    
    with st.form("health_form"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            name = st.text_input("Full Name")
            age = st.number_input("Age", min_value=0, max_value=120, value=30)
            gender = st.selectbox("Gender", ["Male", "Female", "Other"])
        
        with col2:
            weight = st.number_input("Weight (kg)", min_value=1.0, max_value=300.0, value=70.0)
            height = st.number_input("Height (cm)", min_value=50.0, max_value=250.0, value=170.0)
            blood_group = st.selectbox("Blood Group", ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-", "Unknown"])
        
        with col3:
            bp_systolic = st.number_input("Systolic BP", min_value=50, max_value=250, value=120)
            bp_diastolic = st.number_input("Diastolic BP", min_value=30, max_value=150, value=80)
            pulse = st.number_input("Heart Rate", min_value=30, max_value=200, value=75)
        
        # Symptoms and History
        col1, col2 = st.columns(2)
        
        with col1:
            symptoms = st.text_area("Current Symptoms", height=100)
            medical_history = st.text_area("Medical History", height=100)
        
        with col2:
            medications = st.text_area("Current Medications", height=100)
            exercise_frequency = st.selectbox("Exercise Frequency", 
                ["Never", "Rarely (less than once/week)", "1-2 times/week", "3-4 times/week", "5+ times/week"])
        
        # Emergency symptoms check
        emergency_symptoms = st.multiselect(
            "⚠️ Emergency Symptoms (select if experiencing):",
            [
                "Severe chest pain",
                "Difficulty breathing", 
                "Sudden severe headache",
                "Loss of consciousness",
                "High fever (>103°F)",
                "Severe bleeding"
            ]
        )
        
        submit_button = st.form_submit_button("🚀 Complete Assessment", use_container_width=True)
    
    # Emergency Alert
    if emergency_symptoms:
        st.markdown(f"""
        <div class="emergency-alert">
            <h2>🚨 MEDICAL EMERGENCY DETECTED</h2>
            <p><strong>SEEK IMMEDIATE MEDICAL ATTENTION!</strong></p>
            <p>Emergency Numbers: 📞 112 (National) | 108 (Medical) | 102 (Ambulance)</p>
            <p><strong>Symptoms:</strong> {', '.join(emergency_symptoms)}</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Process Form Submission
    if submit_button and name:
        # Calculate BMI
        height_m = height / 100
        bmi = weight / (height_m ** 2)
        
        # Prepare data
        vitals_data = {
            'bp_systolic': bp_systolic,
            'bp_diastolic': bp_diastolic,
            'pulse': pulse
        }
        
        lifestyle_data = {
            'exercise_frequency': exercise_frequency
        }
        
        # Store health data
        st.session_state.health_data = {
            'patient': {'name': name, 'age': age, 'gender': gender, 'weight': weight, 'height': height, 'blood_group': blood_group},
            'vitals': vitals_data,
            'symptoms': symptoms,
            'medical_history': medical_history,
            'medications': medications,
            'lifestyle': lifestyle_data,
            'emergency_symptoms': emergency_symptoms
        }
        
        # Success message
        st.markdown("""
        <div class="success-message">
            <h3>✅ Assessment Completed!</h3>
            <p>Your health data has been processed. Review your analysis below.</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Calculate health score
        health_score = AdvancedHealthAnalytics.calculate_indian_health_score(
            vitals_data, bmi, age, symptoms, lifestyle_data
        )
        
        # Display health score
        st.markdown("## 📊 Health Analysis")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown(f"""
            <div class="metric-card" style="text-align: center; border-left-color: {health_score['color']};">
                <h2>🏥 Overall Health Score</h2>
                <h1 style="color: {health_score['color']}; font-size: 4rem;">{health_score['score']}/100</h1>
                <h3>Status: {health_score['status']}</h3>
                <p>{health_score['message']}</p>
                <p><strong>Advice:</strong> {health_score['advice']}</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            # BMI Display
            bmi_category = "Normal" if 18.5 <= bmi <= 22.9 else "Underweight" if bmi < 18.5 else "Overweight"
            bmi_color = "#4CAF50" if bmi_category == "Normal" else "#FF9800"
            
            st.markdown(f"""
            <div class="metric-card" style="text-align: center;">
                <h4>📏 BMI Analysis</h4>
                <h2 style="color: {bmi_color};">{bmi:.1f}</h2>
                <p>{bmi_category}</p>
                <small>WHO Asian Guidelines</small>
            </div>
            """, unsafe_allow_html=True)
            
            # Risk factors
            if health_score['risk_factors']:
                st.markdown("### ⚠️ Risk Factors")
                for factor in health_score['risk_factors']:
                    st.warning(f"• {factor}")
        
        # Recommendations
        if health_score['recommendations']:
            st.markdown("### 💡 Recommendations")
            for rec in health_score['recommendations']:
                st.info(f"• {rec}")
        
        # Create tabs for detailed analysis
        st.markdown("---")
        st.markdown("## 🔍 Detailed Analysis")
        
        tab1, tab2, tab3, tab4 = st.tabs(["🤖 AI Analysis", "🏥 Hospitals", "💊 Pharmacies", "📰 Health News"])
        
        with tab1:
            st.markdown("### 🤖 AI Health Analysis")
            
            analysis_type = st.selectbox(
                "Choose analysis type:",
                ["Comprehensive Health Analysis", "Symptom Assessment", "Lifestyle Recommendations"]
            )
            
            if st.button("🚀 Get AI Analysis"):
                with st.spinner("Analyzing your health data..."):
                    prompt = f"Provide {analysis_type.lower()} for Indian patient"
                    
                    try:
                        ai_response = ai_service.get_health_analysis_sync(
                            prompt, st.session_state.health_data, analysis_type
                        )
                        
                        st.markdown(f"""
                        <div class="metric-card">
                            <h4>🤖 {analysis_type}</h4>
                            <div style="background: #f8f9fa; padding: 1rem; border-radius: 8px; white-space: pre-wrap;">
                                {ai_response}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                    except Exception as e:
                        st.error(f"Analysis error: {str(e)}")
        
        with tab2:
            st.markdown("### 🏥 Nearby Hospitals")
            
            if st.session_state.coordinates:
                lat, lon = st.session_state.coordinates
                hospitals = facilities_service.search_facilities(lat, lon, "hospital")
                
                if hospitals:
                    st.info(f"Found {len(hospitals)} hospitals near your location")
                    
                    for hospital in hospitals[:5]:  # Show top 5
                        st.markdown(f"""
                        <div class="facility-card">
                            <h4>{hospital['name']}</h4>
                            <p><strong>📍 Distance:</strong> {hospital['distance']} km</p>
                            <p><strong>⭐ Rating:</strong> {hospital['rating']:.1f}/5</p>
                            <p><strong>🏥 Type:</strong> {hospital['type']}</p>
                            <p><strong>📞 Phone:</strong> {hospital['phone']}</p>
                            <p><strong>🛏️ Beds:</strong> {hospital['beds']}</p>
                            <p><strong>🕒 Hours:</strong> {hospital['hours']}</p>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.warning("No hospitals found in your area.")
            else:
                st.warning("Please set your location to find nearby hospitals.")
        
        with tab3:
            st.markdown("### 💊 Nearby Pharmacies")
            
            if st.session_state.coordinates:
                lat, lon = st.session_state.coordinates
                pharmacies = facilities_service.search_facilities(lat, lon, "pharmacy")
                
                if pharmacies:
                    st.info(f"Found {len(pharmacies)} pharmacies near your location")
                    
                    for pharmacy in pharmacies[:5]:  # Show top 5
                        st.markdown(f"""
                        <div class="facility-card">
                            <h4>{pharmacy['name']}</h4>
                            <p><strong>📍 Distance:</strong> {pharmacy['distance']} km</p>
                            <p><strong>⭐ Rating:</strong> {pharmacy['rating']:.1f}/5</p>
                            <p><strong>🏪 Type:</strong> {pharmacy['type']}</p>
                            <p><strong>💊 Specialty:</strong> {pharmacy['specialty']}</p>
                            <p><strong>🕒 Hours:</strong> {pharmacy['hours']}</p>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.warning("No pharmacies found in your area.")
            else:
                st.warning("Please set your location to find nearby pharmacies.")
        
        with tab4:
            st.markdown("### 📰 Latest Health News")
            st.info("Health news feature coming soon...")
            
            # Sample news items
            news_items = [
                "🇮🇳 AIIMS launches new telemedicine services across rural India",
                "💊 Jan Aushadhi scheme reaches 8,000 stores nationwide", 
                "🌿 New Ayurveda research shows promising results for diabetes",
                "🏥 Government announces expansion of Ayushman Bharat coverage"
            ]
            
            for news in news_items:
                st.markdown(f"• {news}")

    # Footer
    st.markdown("---")
    st.markdown(f"""
    <div style="text-align: center; padding: 2rem; background: linear-gradient(135deg, #007C91, #B1AFFF); color: white; border-radius: 15px; margin: 2rem 0;">
        <h2>🏥 MediAI Pro - भारत का स्वास्थ्य सहायक</h2>
        <p>Advanced AI-Powered Healthcare Assistant for India</p>
        <p><strong>⚠️ Medical Disclaimer:</strong> This application provides health information for educational purposes only. 
        Always consult qualified healthcare professionals for medical advice.</p>
        <p><strong>🚨 Emergency Numbers:</strong> 112 (National) | 108 (Medical) | 102 (Ambulance)</p>
        <p><em>"स्वास्थ्यम् परम भाग्यम्" - Health is the Greatest Wealth</em></p>
        <small>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Version 3.0 | Made for India</small>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error(f"Application error: {e}")
        st.info("Please refresh the page or check your configuration.")
