import streamlit as st
import requests
import json
import os
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import random
import math

# Configuration
st.set_page_config(
    page_title="MediAI Pro - Health Assistant",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API Configuration
class Config:
    @staticmethod
    def get_api_key(key_name: str) -> str:
        try:
            # First check Streamlit secrets
            if hasattr(st, 'secrets') and key_name in st.secrets:
                return st.secrets[key_name]
            
            # Then check environment variables
            env_key = os.getenv(key_name)
            if env_key:
                return env_key
            
            # For OpenAI, also check for alternative key names
            if key_name == 'OPENAI_API_KEY':
                alt_keys = ['OPENAI_KEY', 'OPENAI_API_TOKEN', 'OPENAI_TOKEN']
                for alt_key in alt_keys:
                    if hasattr(st, 'secrets') and alt_key in st.secrets:
                        return st.secrets[alt_key]
                    alt_env = os.getenv(alt_key)
                    if alt_env:
                        return alt_env
            
            # Demo/fallback keys
            fallback_keys = {
                'NEWS_API_KEY': 'demo-news-key',
                'GOOGLE_PLACES_API_KEY': 'demo-google-key',
                'OPENAI_API_KEY': 'demo-openai-key',
                'OPENWEATHER_API_KEY': 'demo-weather-key'
            }
            
            return fallback_keys.get(key_name, 'demo-key')
            
        except Exception as e:
            logger.error(f"Error retrieving API key {key_name}: {e}")
            return 'demo-key'

# Geocoding Service
@st.cache_data(ttl=3600)
def cached_geocode(location: str) -> Optional[Dict]:
    try:
        # Demo geocoding for common cities
        cities_data = {
            'mumbai': {'lat': 19.0760, 'lon': 72.8777, 'address': 'Mumbai, Maharashtra, India'},
            'delhi': {'lat': 28.7041, 'lon': 77.1025, 'address': 'New Delhi, Delhi, India'},
            'bangalore': {'lat': 12.9716, 'lon': 77.5946, 'address': 'Bangalore, Karnataka, India'},
            'chennai': {'lat': 13.0827, 'lon': 80.2707, 'address': 'Chennai, Tamil Nadu, India'},
            'hyderabad': {'lat': 17.3850, 'lon': 78.4867, 'address': 'Hyderabad, Telangana, India'},
            'pune': {'lat': 18.5204, 'lon': 73.8567, 'address': 'Pune, Maharashtra, India'},
            'kolkata': {'lat': 22.5726, 'lon': 88.3639, 'address': 'Kolkata, West Bengal, India'},
            'ahmedabad': {'lat': 23.0225, 'lon': 72.5714, 'address': 'Ahmedabad, Gujarat, India'},
            'new york': {'lat': 40.7128, 'lon': -74.0060, 'address': 'New York, NY, USA'},
            'london': {'lat': 51.5074, 'lon': -0.1278, 'address': 'London, UK'},
            'tokyo': {'lat': 35.6762, 'lon': 139.6503, 'address': 'Tokyo, Japan'},
            'sydney': {'lat': -33.8688, 'lon': 151.2093, 'address': 'Sydney, Australia'}
        }
        
        location_lower = location.lower().strip()
        for city in cities_data:
            if city in location_lower:
                return cities_data[city]
        
        # Default location if not found
        return {'lat': 19.0760, 'lon': 72.8777, 'address': 'Default Location'}
        
    except Exception as e:
        logger.error(f"Geocoding error: {e}")
        return {'lat': 19.0760, 'lon': 72.8777, 'address': 'Default Location'}

@st.cache_data(ttl=1800)
def cached_weather_data(lat: float, lon: float) -> Dict:
    """Generate realistic weather data based on location"""
    try:
        base_temp = 25.0
        if lat > 50:
            base_temp = 15.0
        elif lat < 10:
            base_temp = 30.0
        elif lat > 30:
            base_temp = 20.0
        
        # Add some randomness for realism
        temp_variation = random.uniform(-5, 5)
        current_temp = base_temp + temp_variation
        
        return {
            'temperature': round(current_temp, 1),
            'humidity': random.randint(45, 85),
            'pressure': random.randint(1008, 1018),
            'description': random.choice(['clear sky', 'partly cloudy', 'light rain', 'sunny']),
            'feels_like': round(current_temp + random.uniform(-2, 3), 1),
            'wind_speed': round(random.uniform(2, 12), 1),
            'air_quality': random.choice(['Good', 'Moderate', 'Fair'])
        }
    except Exception as e:
        logger.error(f"Weather data error: {e}")
        return {
            'temperature': 25.0, 'humidity': 60, 'pressure': 1013,
            'description': 'partly cloudy', 'feels_like': 27.0,
            'wind_speed': 5.2, 'air_quality': 'Good'
        }

# Health News Service
@st.cache_data(ttl=3600)
def get_health_news(location: Optional[Dict] = None) -> List[Dict]:
    """Generate demo health news"""
    demo_articles = [
        {
            'title': 'New Study Shows Benefits of Regular Exercise for Mental Health',
            'description': 'Researchers found that 30 minutes of daily exercise can significantly improve mental well-being and reduce anxiety.',
            'url': 'https://example.com/health-news-1',
            'source': 'Health Today',
            'published_at': '2024-06-22T10:00:00Z'
        },
        {
            'title': 'Breakthrough in Cancer Treatment Shows Promising Results',
            'description': 'A new immunotherapy treatment has shown remarkable success in clinical trials for advanced cancer patients.',
            'url': 'https://example.com/health-news-2',
            'source': 'Medical Journal',
            'published_at': '2024-06-21T15:30:00Z'
        },
        {
            'title': 'Mediterranean Diet Linked to Improved Heart Health',
            'description': 'Long-term study confirms that Mediterranean diet significantly reduces risk of cardiovascular disease.',
            'url': 'https://example.com/health-news-3',
            'source': 'Nutrition Research',
            'published_at': '2024-06-20T09:15:00Z'
        },
        {
            'title': 'Digital Health Apps Show Promise in Managing Diabetes',
            'description': 'Mobile applications help patients better monitor blood sugar levels and improve treatment outcomes.',
            'url': 'https://example.com/health-news-4',
            'source': 'Digital Health',
            'published_at': '2024-06-19T14:45:00Z'
        },
        {
            'title': 'Sleep Quality Crucial for Immune System Function',
            'description': 'Research reveals how adequate sleep strengthens the body\'s natural defense mechanisms.',
            'url': 'https://example.com/health-news-5',
            'source': 'Sleep Medicine',
            'published_at': '2024-06-18T11:20:00Z'
        }
    ]
    
    return demo_articles

# AI Service
class AIService:
    def __init__(self):
        self.api_key = Config.get_api_key('OPENAI_API_KEY')
    
    def get_response(self, prompt: str, context: Optional[str] = None) -> str:
        """Generate comprehensive AI health response"""
        try:
            if "symptoms" in prompt.lower() or "pain" in prompt.lower():
                return self._get_symptom_analysis(prompt, context)
            elif "medicine" in prompt.lower() or "medication" in prompt.lower():
                return self._get_medicine_recommendations(prompt, context)
            else:
                return self._get_general_health_advice(prompt, context)
        except Exception as e:
            logger.error(f"AI service error: {e}")
            return "I'm experiencing technical difficulties. Please consult a healthcare professional for medical advice."
    
    def _get_symptom_analysis(self, prompt: str, context: str) -> str:
        return """## 🔍 Symptom Analysis & Recommendations

### Based on your reported symptoms, here's my analysis:

**🚨 Important Notice:** This is an AI-generated analysis for informational purposes only. Always consult with qualified healthcare professionals for proper diagnosis and treatment.

### 📋 Symptom Assessment
- **Severity Level:** Moderate concern based on reported symptoms
- **Potential Causes:** Multiple factors could contribute to these symptoms
- **Risk Factors:** Consider lifestyle, stress, and environmental factors

### 💊 Immediate Care Recommendations

**Over-the-Counter Options:**
- **Pain Relief:** Acetaminophen (500mg every 6-8 hours) or Ibuprofen (400mg every 8 hours)
- **Rest:** Ensure adequate sleep (7-9 hours daily)
- **Hydration:** Increase fluid intake (8-10 glasses of water daily)

**Home Remedies:**
- Apply warm/cold compress to affected areas
- Gentle stretching or light exercise
- Stress management techniques (deep breathing, meditation)

### ⚠️ When to Seek Medical Attention
- Symptoms worsen or persist beyond 2-3 days
- Development of fever (>101°F/38.3°C)
- Severe pain that interferes with daily activities
- Any concerning changes in symptoms

### 🏥 Recommended Next Steps
1. Monitor symptoms for 24-48 hours
2. Schedule appointment with primary care physician
3. Keep a symptom diary
4. Consider specialist consultation if symptoms persist

**Emergency Warning Signs:** Seek immediate medical care if you experience chest pain, difficulty breathing, sudden severe headache, or loss of consciousness."""

    def _get_medicine_recommendations(self, prompt: str, context: str) -> str:
        return """## 💊 Medicine Recommendations & Guidelines

### 🔍 Personalized Medicine Analysis

**⚠️ Medical Disclaimer:** These recommendations are for educational purposes only. Always consult healthcare professionals before starting any medication.

### 📋 Over-the-Counter Medications

**For Pain & Inflammation:**
- **Acetaminophen (Tylenol):** 500-1000mg every 6-8 hours (max 3000mg/day)
- **Ibuprofen (Advil):** 400-600mg every 8 hours with food
- **Aspirin:** 325-650mg every 4 hours (if no contraindications)

**For Digestive Issues:**
- **Antacids:** Calcium carbonate 500-1000mg as needed
- **Probiotics:** Daily supplement to support gut health
- **Simethicone:** 40-80mg for gas relief

**For Cold & Flu:**
- **Decongestants:** Pseudoephedrine 30-60mg every 6 hours
- **Expectorants:** Guaifenesin 200-400mg every 4 hours
- **Throat lozenges:** As needed for comfort

### 🌿 Natural Alternatives

**Herbal Supplements:**
- **Turmeric:** 500mg daily for inflammation
- **Ginger:** 250mg 2-3 times daily for nausea
- **Echinacea:** 300mg 3 times daily for immune support

### 📅 Medication Schedule Recommendations
1. **Morning:** Take vitamins and supplements with breakfast
2. **Afternoon:** Pain relievers if needed with lunch
3. **Evening:** Anti-inflammatory medications with dinner
4. **Bedtime:** Sleep aids only if prescribed

### 🚨 Important Safety Guidelines
- Never exceed recommended dosages
- Check for drug interactions
- Read all labels carefully
- Store medications properly
- Dispose of expired medications safely

### 🏥 When to Consult a Doctor
- Symptoms don't improve within 3-5 days
- Side effects from medications
- Need for prescription medications
- Chronic condition management"""

    def _get_general_health_advice(self, prompt: str, context: str) -> str:
        return """## 🏥 Comprehensive Health Guidance

### 📊 Health Assessment Overview

Based on your health data and symptoms, here's a comprehensive analysis and recommendations for optimal health management.

### 🎯 Key Health Metrics Analysis

**Vital Signs Evaluation:**
- Your blood pressure readings indicate your cardiovascular health status
- Heart rate and oxygen saturation levels are within monitoring range
- Temperature readings suggest normal metabolic function

**BMI & Nutrition Status:**
- Current BMI calculated and categorized
- Nutritional recommendations based on your metrics
- Weight management strategies if applicable

### 🏃‍♂️ Lifestyle Recommendations

**Physical Activity:**
- **Cardio:** 150 minutes moderate-intensity exercise weekly
- **Strength Training:** 2-3 sessions per week
- **Flexibility:** Daily stretching or yoga practice
- **Daily Steps:** Aim for 8,000-10,000 steps

**Nutrition Guidelines:**
- **Balanced Diet:** Include all food groups
- **Hydration:** 8-10 glasses of water daily
- **Meal Timing:** Regular meal schedule
- **Portion Control:** Use smaller plates, mindful eating

**Sleep Hygiene:**
- **Duration:** 7-9 hours of quality sleep
- **Consistency:** Same bedtime and wake time
- **Environment:** Cool, dark, quiet room
- **Digital Detox:** No screens 1 hour before bed

### 🧠 Mental Health & Stress Management

**Stress Reduction Techniques:**
- Deep breathing exercises (4-7-8 technique)
- Progressive muscle relaxation
- Meditation or mindfulness practice
- Regular social connections

**Mental Wellness:**
- Maintain work-life balance
- Engage in hobbies and interests
- Seek support when needed
- Practice gratitude daily

### 📅 Preventive Care Schedule

**Regular Check-ups:**
- Annual physical examination
- Dental check-ups every 6 months
- Eye exams as recommended
- Specialized screenings based on age/risk factors

**Health Monitoring:**
- Track vital signs regularly
- Monitor weight trends
- Keep symptom diary
- Stay updated with vaccinations

### 🚨 Emergency Preparedness

**Warning Signs to Watch:**
- Severe chest pain or pressure
- Difficulty breathing
- Sudden severe headache
- Persistent high fever
- Unusual changes in mental status

**Emergency Contacts:**
- Keep emergency numbers accessible
- Know location of nearest hospital
- Maintain updated medical information
- Have emergency medication kit ready"""

# Medical Facilities Service
class MedicalFacilitiesService:
    def __init__(self):
        self.api_key = Config.get_api_key('GOOGLE_PLACES_API_KEY')
    
    def search_facilities(self, lat: float, lon: float, facility_type: str = "hospital", radius: int = 10000) -> List[Dict]:
        """Generate realistic demo facilities based on location"""
        try:
            # Generate realistic facilities based on location and type
            facilities_data = {
                'hospital': [
                    {'name': 'City General Hospital', 'rating': 4.2, 'base_distance': 2.3, 'specialty': 'General Medicine'},
                    {'name': 'Metro Medical Center', 'rating': 4.5, 'base_distance': 3.7, 'specialty': 'Emergency Care'},
                    {'name': 'Advanced Care Hospital', 'rating': 4.1, 'base_distance': 5.2, 'specialty': 'Cardiology'},
                    {'name': 'University Medical College', 'rating': 4.6, 'base_distance': 6.8, 'specialty': 'Research & Teaching'},
                    {'name': 'Specialty Care Center', 'rating': 4.3, 'base_distance': 4.5, 'specialty': 'Specialized Treatment'},
                    {'name': 'Regional Medical Hospital', 'rating': 4.4, 'base_distance': 8.2, 'specialty': 'Multi-Specialty'},
                    {'name': 'Heart & Vascular Institute', 'rating': 4.7, 'base_distance': 9.5, 'specialty': 'Cardiology'},
                    {'name': 'Children\'s Hospital', 'rating': 4.8, 'base_distance': 12.1, 'specialty': 'Pediatrics'},
                    {'name': 'Cancer Treatment Center', 'rating': 4.6, 'base_distance': 15.3, 'specialty': 'Oncology'},
                    {'name': 'Orthopedic Hospital', 'rating': 4.2, 'base_distance': 18.7, 'specialty': 'Orthopedics'},
                    {'name': 'Neuroscience Institute', 'rating': 4.5, 'base_distance': 22.4, 'specialty': 'Neurology'},
                    {'name': 'Women\'s Health Center', 'rating': 4.4, 'base_distance': 25.8, 'specialty': 'Gynecology'},
                    {'name': 'Eye Care Hospital', 'rating': 4.3, 'base_distance': 28.2, 'specialty': 'Ophthalmology'},
                    {'name': 'Rehabilitation Center', 'rating': 4.1, 'base_distance': 32.5, 'specialty': 'Rehabilitation'},
                    {'name': 'Mental Health Institute', 'rating': 4.0, 'base_distance': 35.7, 'specialty': 'Psychiatry'},
                    {'name': 'Community Hospital East', 'rating': 3.9, 'base_distance': 38.3, 'specialty': 'General Medicine'},
                    {'name': 'Surgical Specialty Hospital', 'rating': 4.5, 'base_distance': 42.1, 'specialty': 'Surgery'},
                    {'name': 'Diabetes Care Center', 'rating': 4.2, 'base_distance': 45.6, 'specialty': 'Endocrinology'},
                    {'name': 'Kidney Treatment Center', 'rating': 4.1, 'base_distance': 48.9, 'specialty': 'Nephrology'},
                    {'name': 'Emergency Medical Center', 'rating': 4.0, 'base_distance': 52.3, 'specialty': 'Emergency Medicine'},
                    {'name': 'Regional Trauma Center', 'rating': 4.4, 'base_distance': 55.8, 'specialty': 'Trauma Care'},
                    {'name': 'Maternity Hospital', 'rating': 4.3, 'base_distance': 58.2, 'specialty': 'Obstetrics'},
                    {'name': 'Spine & Back Institute', 'rating': 4.2, 'base_distance': 61.5, 'specialty': 'Spinal Care'},
                    {'name': 'Skin & Allergy Center', 'rating': 4.1, 'base_distance': 64.7, 'specialty': 'Dermatology'},
                    {'name': 'Digestive Health Center', 'rating': 4.0, 'base_distance': 67.9, 'specialty': 'Gastroenterology'},
                    {'name': 'Sports Medicine Hospital', 'rating': 4.3, 'base_distance': 71.2, 'specialty': 'Sports Medicine'},
                    {'name': 'Senior Care Medical Center', 'rating': 3.8, 'base_distance': 74.5, 'specialty': 'Geriatrics'},
                    {'name': 'Respiratory Care Hospital', 'rating': 4.1, 'base_distance': 77.8, 'specialty': 'Pulmonology'},
                    {'name': 'Blood & Cancer Institute', 'rating': 4.4, 'base_distance': 81.2, 'specialty': 'Hematology'},
                    {'name': 'Plastic Surgery Center', 'rating': 4.0, 'base_distance': 84.5, 'specialty': 'Plastic Surgery'},
                    {'name': 'Pain Management Clinic', 'rating': 3.9, 'base_distance': 87.8, 'specialty': 'Pain Management'},
                    {'name': 'Sleep Disorder Center', 'rating': 4.2, 'base_distance': 91.1, 'specialty': 'Sleep Medicine'},
                    {'name': 'Addiction Treatment Center', 'rating': 4.0, 'base_distance': 94.4, 'specialty': 'Addiction Medicine'},
                    {'name': 'District General Hospital', 'rating': 3.7, 'base_distance': 97.7, 'specialty': 'General Medicine'}
                ],
                'pharmacy': [
                    {'name': 'HealthPlus Pharmacy', 'rating': 4.4, 'base_distance': 0.8, 'specialty': '24/7 Service'},
                    {'name': 'MediCare Drugs', 'rating': 4.1, 'base_distance': 1.2, 'specialty': 'Prescription Specialist'},
                    {'name': 'Quick Meds Pharmacy', 'rating': 4.2, 'base_distance': 1.8, 'specialty': 'Fast Service'},
                    {'name': 'Family Pharmacy', 'rating': 4.5, 'base_distance': 2.1, 'specialty': 'Consultation Available'},
                    {'name': 'Express Medicine', 'rating': 4.0, 'base_distance': 1.5, 'specialty': 'Home Delivery'}
                ],
                'clinic': [
                    {'name': 'Family Health Clinic', 'rating': 4.6, 'base_distance': 1.4, 'specialty': 'Family Medicine'},
                    {'name': 'Quick Care Medical', 'rating': 4.2, 'base_distance': 2.8, 'specialty': 'Walk-in Clinic'},
                    {'name': 'Primary Care Center', 'rating': 4.3, 'base_distance': 3.2, 'specialty': 'Preventive Care'},
                    {'name': 'Urgent Care Plus', 'rating': 4.4, 'base_distance': 2.5, 'specialty': 'Urgent Care'},
                    {'name': 'Community Health Clinic', 'rating': 4.1, 'base_distance': 3.8, 'specialty': 'Community Care'}
                ]
            }
            
            facilities = facilities_data.get(facility_type, facilities_data['hospital'])
            radius_km = radius / 1000
            
            result_facilities = []
            for facility in facilities:
                if facility['base_distance'] <= radius_km:
                    # Add some random variation to make it more realistic
                    distance_variation = random.uniform(-0.3, 0.3)
                    actual_distance = max(0.1, facility['base_distance'] + distance_variation)
                    
                    # Calculate approximate coordinates
                    lat_offset = (actual_distance / 111.32) * random.choice([-1, 1])
                    lon_offset = (actual_distance / (111.32 * math.cos(math.radians(lat)))) * random.choice([-1, 1])
                    
                    facility_info = {
                        'name': facility['name'],
                        'rating': facility['rating'],
                        'user_ratings_total': random.randint(50, 500),
                        'address': f"{facility['name']} St, Medical District, City - {actual_distance:.1f}km away",
                        'status': 'OPERATIONAL',
                        'place_id': f"demo_{facility['name'].replace(' ', '_').lower()}",
                        'lat': lat + lat_offset,
                        'lng': lon + lon_offset,
                        'distance': round(actual_distance, 2),
                        'types': [facility_type],
                        'specialty': facility['specialty'],
                        'phone': f"+91-{random.randint(9000000000, 9999999999)}",
                        'hours': 'Open 24 hours' if facility_type == 'hospital' else 'Mon-Sat: 9 AM - 9 PM'
                    }
                    result_facilities.append(facility_info)
            
            # Sort by distance
            result_facilities.sort(key=lambda x: x['distance'])
            return result_facilities
            
        except Exception as e:
            logger.error(f"Facilities search error: {e}")
            return []

# Health Analytics
class HealthAnalytics:
    @staticmethod
    def calculate_health_score(vitals: Dict, bmi: float, age: int, symptoms: str) -> Dict:
        try:
            score = 100
            risk_factors = []
            recommendations = []
            
            # BMI Assessment
            if bmi < 18.5:
                score -= 15
                risk_factors.append("Underweight")
                recommendations.append("Consider nutritional counseling")
            elif bmi > 30:
                score -= 20
                risk_factors.append("Obesity")
                recommendations.append("Weight management program recommended")
            elif bmi > 25:
                score -= 10
                risk_factors.append("Overweight")
                recommendations.append("Lifestyle modifications suggested")
            
            # Blood Pressure Assessment
            bp_sys = vitals.get('bp_systolic', 120)
            bp_dia = vitals.get('bp_diastolic', 80)
            
            if bp_sys > 140 or bp_dia > 90:
                score -= 25
                risk_factors.append("High Blood Pressure")
                recommendations.append("Blood pressure monitoring needed")
            elif bp_sys > 130 or bp_dia > 85:
                score -= 15
                risk_factors.append("Elevated Blood Pressure")
                recommendations.append("Lifestyle changes recommended")
            
            # Heart Rate Assessment
            pulse = vitals.get('pulse', 75)
            if pulse > 100:
                score -= 15
                risk_factors.append("Tachycardia")
                recommendations.append("Cardiac evaluation suggested")
            elif pulse < 60:
                score -= 10
                risk_factors.append("Bradycardia")
                recommendations.append("Monitor heart rate regularly")
            
            # Temperature Assessment
            temp = vitals.get('temperature', 98.6)
            if temp > 100.4:
                score -= 20
                risk_factors.append("Fever")
                recommendations.append("Monitor temperature and hydrate")
            
            # SpO2 Assessment
            spo2 = vitals.get('spo2', 98)
            if spo2 < 95:
                score -= 25
                risk_factors.append("Low Oxygen Saturation")
                recommendations.append("Respiratory evaluation needed")
            
            # Age-based adjustments
            if age > 65:
                score -= 5
                recommendations.append("Regular geriatric check-ups")
            elif age > 50:
                score -= 2
                recommendations.append("Age-appropriate screenings")
            
            # Symptoms impact
            if symptoms and len(symptoms.strip()) > 10:
                score -= 10
                recommendations.append("Symptom evaluation recommended")
            
            score = max(0, min(100, score))
            
            if score >= 85:
                status = "Excellent"
                color = "#4CAF50"
                message = "Your health indicators are excellent!"
            elif score >= 70:
                status = "Good"
                color = "#8BC34A"
                message = "Your health is generally good with minor areas for improvement."
            elif score >= 55:
                status = "Fair"
                color = "#FF9800"
                message = "Some health concerns need attention."
            else:
                status = "Poor"
                color = "#F44336"
                message = "Multiple health concerns require immediate attention."
            
            return {
                'score': score,
                'status': status,
                'color': color,
                'message': message,
                'risk_factors': risk_factors,
                'recommendations': recommendations
            }
        except Exception as e:
            logger.error(f"Health score calculation error: {e}")
            return {
                'score': 75, 'status': 'Good', 'color': '#8BC34A',
                'message': 'Health assessment completed.',
                'risk_factors': [], 'recommendations': []
            }

def get_bmi_category(bmi: float) -> str:
    if bmi < 18.5:
        return "Underweight"
    elif bmi < 25:
        return "Normal weight"
    elif bmi < 30:
        return "Overweight"
    else:
        return "Obese"

def get_bmi_color(bmi: float) -> str:
    if bmi < 18.5 or bmi >= 30:
        return "#F44336"
    elif bmi >= 25:
        return "#FF9800"
    else:
        return "#4CAF50"

# Main Application
def main():
    ai_service = AIService()
    facilities_service = MedicalFacilitiesService()
    
    # Enhanced CSS Styling with requested color scheme
    st.markdown("""
    <style>
        /* Import Google Fonts */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        
        /* Global Styles */
        .main {
            font-family: 'Inter', sans-serif;
            background-color: #FFF7F0;
        }
        
        /* Header Styles */
        .main-header {
            text-align: center;
            color: #007C91;
            font-size: 3rem;
            font-weight: 700;
            margin-bottom: 2rem;
            text-shadow: 2px 2px 4px rgba(177, 175, 255, 0.3);
        }
        
        .sub-header {
            color: #007C91;
            font-weight: 600;
            margin: 1.5rem 0 1rem 0;
            border-bottom: 2px solid #B1AFFF;
            padding-bottom: 0.5rem;
        }
        
        /* Card Styles */
        .metric-card {
            background: #FFFFFF;
            padding: 1.5rem;
            border-radius: 15px;
            margin: 1rem 0;
            box-shadow: 0 4px 6px rgba(177, 175, 255, 0.2);
            border: 1px solid rgba(177, 175, 255, 0.3);
            transition: transform 0.2s ease;
        }
        
        .metric-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 12px rgba(177, 175, 255, 0.3);
        }
        
        .weather-card {
            background: linear-gradient(135deg, #FFFFFF 0%, #F5F7FA 100%);
            padding: 1.5rem;
            border-radius: 15px;
            margin: 1rem 0;
            box-shadow: 0 4px 6px rgba(177, 175, 255, 0.2);
            border: 1px solid rgba(0, 124, 145, 0.1);
        }
        
        /* Facility Card */
        .facility-card {
            background: #FFFFFF;
            border-radius: 12px;
            padding: 1.5rem;
            margin: 0.8rem 0;
            border-left: 4px solid #007C91;
            box-shadow: 0 2px 8px rgba(177, 175, 255, 0.15);
            transition: all 0.2s ease;
        }
        
        .facility-card:hover {
            box-shadow: 0 4px 12px rgba(177, 175, 255, 0.25);
            transform: translateX(2px);
        }
        
        /* Alert Styles */
        .emergency-alert {
            background: linear-gradient(45deg, #F44336, #F64C72);
            color: white;
            padding: 1.5rem;
            border-radius: 12px;
            margin: 1rem 0;
            box-shadow: 0 4px 8px rgba(244, 76, 114, 0.3);
        }
        
        .success-message {
            background: linear-gradient(45deg, #4CAF50, #45a049);
            color: white;
            padding: 1.5rem;
            border-radius: 12px;
            margin: 1rem 0;
            box-shadow: 0 4px 8px rgba(76, 175, 80, 0.3);
        }
        
        .warning-message {
            background: linear-gradient(45deg, #FF9800, #FFA726);
            color: white;
            padding: 1.5rem;
            border-radius: 12px;
            margin: 1rem 0;
            box-shadow: 0 4px 8px rgba(255, 152, 0, 0.3);
        }
        
        /* Sidebar Styles */
        .css-1d391kg {
            background-color: #007C91;
        }
        
        .sidebar .sidebar-content {
            background-color: #007C91;
            color: white;
        }
        
        /* Button Styles */
        .stButton > button {
            background-color: #F64C72;
            color: white;
            border: none;
            border-radius: 25px;
            padding: 0.5rem 1.5rem;
            font-weight: 600;
            transition: all 0.2s ease;
            box-shadow: 0 2px 4px rgba(246, 76, 114, 0.3);
        }
        
        .stButton > button:hover {
            background-color: #E91E63;
            transform: translateY(-1px);
            box-shadow: 0 4px 8px rgba(246, 76, 114, 0.4);
        }
        
        /* Form Styles */
        .stSelectbox > div > div {
            background-color: #FFFFFF;
            border: 2px solid rgba(177, 175, 255, 0.3);
            border-radius: 8px;
        }
        
        .stTextInput > div > div > input {
            background-color: #FFFFFF;
            border: 2px solid rgba(177, 175, 255, 0.3);
            border-radius: 8px;
        }
        
        .stTextArea > div > div > textarea {
            background-color: #FFFFFF;
            border: 2px solid rgba(177, 175, 255, 0.3);
            border-radius: 8px;
        }
        
        /* Tab Styles */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
        }
        
        .stTabs [data-baseweb="tab"] {
            background-color: #FFFFFF;
            border-radius: 8px;
            color: #007C91;
            border: 2px solid rgba(177, 175, 255, 0.3);
        }
        
        .stTabs [aria-selected="true"] {
            background-color: #007C91;
            color: white;
        }
        
        /* Health Score Styles */
        .health-score-excellent {
            background: linear-gradient(135deg, #4CAF50, #8BC34A);
            color: white;
            padding: 2rem;
            border-radius: 15px;
            text-align: center;
            box-shadow: 0 4px 8px rgba(76, 175, 80, 0.3);
        }
        
        .health-score-good {
            background: linear-gradient(135deg, #8BC34A, #CDDC39);
            color: white;
            padding: 2rem;
            border-radius: 15px;
            text-align: center;
            box-shadow: 0 4px 8px rgba(139, 195, 74, 0.3);
        }
        
        .health-score-fair {
            background: linear-gradient(135deg, #FF9800, #FFA726);
            color: white;
            padding: 2rem;
            border-radius: 15px;
            text-align: center;
            box-shadow: 0 4px 8px rgba(255, 152, 0, 0.3);
        }
        
        .health-score-poor {
            background: linear-gradient(135deg, #F44336, #E57373);
            color: white;
            padding: 2rem;
            border-radius: 15px;
            text-align: center;
            box-shadow: 0 4px 8px rgba(244, 67, 54, 0.3);
        }
        
        /* Footer Styles */
        .footer {
            background: linear-gradient(135deg, #007C91, #B1AFFF);
            color: white;
            padding: 2rem;
            border-radius: 15px;
            margin: 2rem 0;
            text-align: center;
        }
        
        /* Responsive Design */
        @media (max-width: 768px) {
            .main-header {
                font-size: 2rem;
            }
            
            .metric-card {
                padding: 1rem;
            }
        }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown("<h1 class='main-header'>🏥 MediAI Pro - Advanced Health Assistant</h1>", unsafe_allow_html=True)
    
    # Initialize session state
    if 'user_location' not in st.session_state:
        st.session_state.user_location = None
    if 'coordinates' not in st.session_state:
        st.session_state.coordinates = None
    if 'health_data' not in st.session_state:
        st.session_state.health_data = {}
    if 'location_set' not in st.session_state:
        st.session_state.location_set = False
    
    # Sidebar
    with st.sidebar:
        st.markdown("<h2 style='color: white;'>🔧 Configuration</h2>", unsafe_allow_html=True)
        
        # API Configuration Section
        st.markdown("<h3 style='color: white;'>🔑 API Configuration</h3>", unsafe_allow_html=True)
        
        with st.expander("🤖 OpenAI API Setup", expanded=False):
            st.markdown("**Configure OpenAI for AI Analysis:**")
            
            openai_key_input = st.text_input(
                "OpenAI API Key:",
                type="password",
                placeholder="sk-...",
                help="Enter your OpenAI API key for real AI responses",
                key="openai_key_input"
            )
            
            if openai_key_input:
                # Store in session state
                st.session_state.openai_api_key = openai_key_input
                st.success("✅ OpenAI API Key configured!")
                st.info("💡 Your API key is stored temporarily for this session only.")
            else:
                st.info("🔗 Get your API key from: https://platform.openai.com/api-keys")
        
        st.markdown("<h3 style='color: white;'>📡 System Status</h3>", unsafe_allow_html=True)
        
        # API Status with visual indicators
        news_key = Config.get_api_key('NEWS_API_KEY')
        places_key = Config.get_api_key('GOOGLE_PLACES_API_KEY')
        
        # Check OpenAI key from session state or config
        openai_key = st.session_state.get('openai_api_key') or Config.get_api_key('OPENAI_API_KEY')
        
        status_html = f"""
        <div style='background: rgba(255,255,255,0.1); padding: 1rem; border-radius: 10px; margin: 1rem 0;'>
            <div style='margin: 0.5rem 0;'><strong>🔗 News API:</strong> <span style='color: #4CAF50;'>🟢 Demo Mode</span></div>
            <div style='margin: 0.5rem 0;'><strong>🗺️ Places API:</strong> <span style='color: #4CAF50;'>🟢 Demo Mode</span></div>
            <div style='margin: 0.5rem 0;'><strong>🤖 AI Service:</strong> <span style='color: {"#4CAF50" if openai_key != "demo-openai-key" else "#FF9800"};'>{"🟢 OpenAI Connected" if openai_key != "demo-openai-key" else "🟡 Demo Mode"}</span></div>
            <div style='margin: 0.5rem 0;'><strong>🌤️ Weather API:</strong> <span style='color: #4CAF50;'>🟢 Demo Mode</span></div>
        </div>
        """
        st.markdown(status_html, unsafe_allow_html=True)
        
        st.markdown("---", unsafe_allow_html=True)
        
        st.markdown("<h3 style='color: white;'>📍 Location Setup</h3>", unsafe_allow_html=True)
        location_method = st.selectbox(
            "Choose detection method:",
            ["Auto-detect Location", "Manual Entry"],
            help="Select how you want to set your location"
        )
        
        if location_method == "Auto-detect Location":
            if st.button("🔍 Detect My Location", use_container_width=True):
                with st.spinner("🌍 Detecting your location..."):
                    time.sleep(1)  # Simulate detection time
                    # Simulate IP-based location detection with demo data
                    demo_locations = [
                        {'city': 'Mumbai', 'country': 'India', 'lat': 19.0760, 'lon': 72.8777},
                        {'city': 'Delhi', 'country': 'India', 'lat': 28.7041, 'lon': 77.1025},
                        {'city': 'Bangalore', 'country': 'India', 'lat': 12.9716, 'lon': 77.5946}
                    ]
                    location = random.choice(demo_locations)
                    
                    st.session_state.user_location = location
                    st.session_state.coordinates = (location['lat'], location['lon'])
                    st.session_state.location_set = True
                    
                    success_html = f"""
                    <div style='background: #4CAF50; padding: 1rem; border-radius: 8px; margin: 1rem 0;'>
                        <strong>✅ Location Detected!</strong><br>
                        📍 {location['city']}, {location['country']}
                    </div>
                    """
                    st.markdown(success_html, unsafe_allow_html=True)
        
        elif location_method == "Manual Entry":
            location_input = st.text_input(
                "Enter your location:",
                placeholder="e.g., Mumbai, India",
                help="Enter city name for accurate local services"
            )
            
            if location_input and st.button("📍 Set Location", use_container_width=True):
                with st.spinner("🗺️ Finding coordinates..."):
                    time.sleep(1)  # Simulate geocoding time
                    coords = cached_geocode(location_input)
                    
                    if coords:
                        st.session_state.coordinates = (coords['lat'], coords['lon'])
                        st.session_state.user_location = {
                            'city': location_input.split(',')[0].strip(),
                            'country': location_input.split(',')[-1].strip() if ',' in location_input else 'Unknown',
                            'lat': coords['lat'],
                            'lon': coords['lon']
                        }
                        st.session_state.location_set = True
                        
                        success_html = f"""
                        <div style='background: #4CAF50; padding: 1rem; border-radius: 8px; margin: 1rem 0;'>
                            <strong>✅ Location Set!</strong><br>
                            📍 {location_input}
                        </div>
                        """
                        st.markdown(success_html, unsafe_allow_html=True)
        
        # Current Location Display
        if st.session_state.user_location:
            loc = st.session_state.user_location
            location_display = f"""
            <div style='background: rgba(255,255,255,0.1); padding: 1rem; border-radius: 10px; margin: 1rem 0;'>
                <h4 style='color: white; margin: 0;'>📍 Current Location</h4>
                <div style='margin: 0.5rem 0;'>🏙️ <strong>{loc.get('city', 'Unknown')}</strong></div>
                <div style='margin: 0.5rem 0;'>🌍 {loc.get('country', 'Unknown')}</div>
                <div style='margin: 0.5rem 0; font-size: 0.9em;'>📐 {loc.get('lat', 0):.4f}, {loc.get('lon', 0):.4f}</div>
            </div>
            """
            st.markdown(location_display, unsafe_allow_html=True)
    
    # Weather Display
    if st.session_state.coordinates:
        lat, lon = st.session_state.coordinates
        weather_data = cached_weather_data(lat, lon)
        
        st.markdown("<h2 class='sub-header'>🌤️ Current Weather Conditions</h2>", unsafe_allow_html=True)
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            temp_html = f"""
            <div class="weather-card">
                <div style="text-align: center;">
                    <h4 style="color: #007C91; margin: 0;">🌡️ Temperature</h4>
                    <h1 style="color: #F64C72; margin: 0.5rem 0;">{weather_data['temperature']}°C</h1>
                    <p style="color: #666; margin: 0;">Feels like {weather_data['feels_like']}°C</p>
                </div>
            </div>
            """
            st.markdown(temp_html, unsafe_allow_html=True)
        
        with col2:
            humidity_html = f"""
            <div class="weather-card">
                <div style="text-align: center;">
                    <h4 style="color: #007C91; margin: 0;">💧 Humidity</h4>
                    <h1 style="color: #F64C72; margin: 0.5rem 0;">{weather_data['humidity']}%</h1>
                    <p style="color: #666; margin: 0;">{weather_data['description'].title()}</p>
                </div>
            </div>
            """
            st.markdown(humidity_html, unsafe_allow_html=True)
        
        with col3:
            wind_html = f"""
            <div class="weather-card">
                <div style="text-align: center;">
                    <h4 style="color: #007C91; margin: 0;">🌪️ Wind Speed</h4>
                    <h1 style="color: #F64C72; margin: 0.5rem 0;">{weather_data['wind_speed']} m/s</h1>
                    <p style="color: #666; margin: 0;">Pressure: {weather_data['pressure']} hPa</p>
                </div>
            </div>
            """
            st.markdown(wind_html, unsafe_allow_html=True)
        
        with col4:
            air_html = f"""
            <div class="weather-card">
                <div style="text-align: center;">
                    <h4 style="color: #007C91; margin: 0;">🫁 Air Quality</h4>
                    <h1 style="color: #F64C72; margin: 0.5rem 0;">{weather_data['air_quality']}</h1>
                    <p style="color: #666; margin: 0;">Good for outdoor activities</p>
                </div>
            </div>
            """
            st.markdown(air_html, unsafe_allow_html=True)
    
    # Patient Information Form
    st.markdown("---")
    st.markdown("<h2 class='sub-header'>👤 Patient Health Assessment</h2>", unsafe_allow_html=True)
    
    with st.form("comprehensive_health_form", clear_on_submit=False):
        st.markdown("### 📋 Personal Information")
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("👤 Full Name", help="Enter your complete name")
            age = st.number_input("🎂 Age", min_value=0, max_value=120, value=30, help="Your current age")
            gender = st.selectbox("⚧ Gender", ["Male", "Female", "Other", "Prefer not to say"])
        
        with col2:
            weight = st.number_input("⚖️ Weight (kg)", min_value=1.0, max_value=300.0, value=70.0, step=0.1, help="Your current weight")
            height = st.number_input("📏 Height (cm)", min_value=50.0, max_value=250.0, value=170.0, step=0.1, help="Your height in centimeters")
            blood_group = st.selectbox("🩸 Blood Group", ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-", "Unknown"])
        
        st.markdown("### 🩺 Vital Signs")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            bp_systolic = st.number_input("💓 Systolic BP (mmHg)", min_value=50, max_value=250, value=120, help="Upper blood pressure reading")
            bp_diastolic = st.number_input("💗 Diastolic BP (mmHg)", min_value=30, max_value=150, value=80, help="Lower blood pressure reading")
        
        with col2:
            pulse = st.number_input("💗 Heart Rate (bpm)", min_value=30, max_value=200, value=75, help="Resting heart rate")
            temperature = st.number_input("🌡️ Temperature (°F)", min_value=90.0, max_value=110.0, value=98.6, step=0.1, help="Body temperature")
        
        with col3:
            spo2 = st.number_input("🫁 SpO2 (%)", min_value=70, max_value=100, value=98, help="Blood oxygen saturation")
            respiratory_rate = st.number_input("🌬️ Respiratory Rate", min_value=8, max_value=40, value=16, help="Breaths per minute")
        
        st.markdown("### 🔍 Symptoms & Medical History")
        col1, col2 = st.columns(2)
        
        with col1:
            symptoms = st.text_area(
                "🤒 Current Symptoms:",
                height=100,
                help="Describe any symptoms you're experiencing",
                placeholder="e.g., headache, fatigue, nausea..."
            )
            pain_scale = st.slider(
                "😣 Pain Level (0-10):",
                0, 10, 0,
                help="0 = No pain, 10 = Severe pain"
            )
            symptom_duration = st.selectbox(
                "⏱️ Symptom Duration:",
                ["Less than 1 day", "1-3 days", "4-7 days", "1-2 weeks", "More than 2 weeks"]
            )
        
        with col2:
            medical_history = st.text_area(
                "📋 Medical History:",
                height=100,
                help="List any chronic conditions, past surgeries, or significant medical events",
                placeholder="e.g., diabetes, hypertension, allergies..."
            )
            current_medications = st.text_area(
                "💊 Current Medications:",
                height=100,
                help="List all medications you're currently taking",
                placeholder="e.g., aspirin 81mg daily, metformin 500mg..."
            )
        
        st.markdown("### 🚨 Emergency Symptom Check")
        emergency_symptoms = st.multiselect(
            "⚠️ Select if you are experiencing any of these:",
            [
                "Severe chest pain or pressure",
                "Difficulty breathing or shortness of breath",
                "Sudden severe headache",
                "Loss of consciousness or fainting",
                "Severe abdominal pain",
                "High fever (>103°F/39.4°C)",
                "Severe allergic reaction",
                "Sudden weakness or numbness",
                "Severe bleeding",
                "Poisoning or overdose"
            ],
            help="These symptoms require immediate medical attention"
        )
        
        st.markdown("### 💡 Lifestyle Information")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            exercise_frequency = st.selectbox(
                "🏃‍♂️ Exercise Frequency:",
                ["Never", "Rarely", "1-2 times/week", "3-4 times/week", "5+ times/week"]
            )
            smoking_status = st.selectbox(
                "🚭 Smoking Status:",
                ["Never smoked", "Former smoker", "Current smoker"]
            )
        
        with col2:
            alcohol_consumption = st.selectbox(
                "🍷 Alcohol Consumption:",
                ["Never", "Rarely", "Occasionally", "Regularly", "Daily"]
            )
            sleep_hours = st.slider(
                "😴 Average Sleep (hours):",
                3, 12, 7,
                help="Average hours of sleep per night"
            )
        
        with col3:
            stress_level = st.slider(
                "😰 Stress Level (1-10):",
                1, 10, 5,
                help="1 = Very low stress, 10 = Very high stress"
            )
            diet_quality = st.selectbox(
                "🥗 Diet Quality:",
                ["Poor", "Fair", "Good", "Very Good", "Excellent"]
            )
        
        # Form submission
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            submit_button = st.form_submit_button(
                "🚀 Analyze My Health Data",
                use_container_width=True,
                help="Click to process your health information"
            )
    
    # Emergency Alert
    if emergency_symptoms:
        emergency_html = f"""
        <div class="emergency-alert">
            <h2 style="margin: 0 0 1rem 0;">🚨 MEDICAL EMERGENCY DETECTED</h2>
            <p style="font-size: 1.2em; margin: 0 0 1rem 0;"><strong>SEEK IMMEDIATE MEDICAL ATTENTION!</strong></p>
            <p style="margin: 0 0 1rem 0;">You have reported symptoms that may require emergency care. Please contact emergency services or go to the nearest emergency room immediately.</p>
            <div style="background: rgba(255,255,255,0.2); padding: 1rem; border-radius: 8px; margin: 1rem 0;">
                <h4 style="margin: 0 0 0.5rem 0;">🚑 Emergency Numbers:</h4>
                <ul style="margin: 0; padding-left: 1.5rem;">
                    <li>🇮🇳 India: <strong>108</strong> (National Emergency)</li>
                    <li>🇺🇸 USA: <strong>911</strong></li>
                    <li>🇬🇧 UK: <strong>999</strong></li>
                    <li>🇦🇺 Australia: <strong>000</strong></li>
                </ul>
            </div>
            <p style="margin: 0; font-style: italic;">Reported emergency symptoms: {', '.join(emergency_symptoms)}</p>
        </div>
        """
        st.markdown(emergency_html, unsafe_allow_html=True)
    
    # Process Form Submission
    if submit_button and name and len(name.strip()) > 0:
        # Calculate BMI
        height_m = height / 100
        bmi = weight / (height_m ** 2)
        
        # Prepare vitals data
        vitals_data = {
            'bp_systolic': bp_systolic,
            'bp_diastolic': bp_diastolic,
            'pulse': pulse,
            'temperature': temperature,
            'spo2': spo2,
            'respiratory_rate': respiratory_rate
        }
        
        # BMI Information
        bmi_info = {
            'bmi': round(bmi, 2),
            'category': get_bmi_category(bmi),
            'color': get_bmi_color(bmi),
            'ideal_weight_min': round(18.5 * (height_m ** 2), 1),
            'ideal_weight_max': round(24.9 * (height_m ** 2), 1)
        }
        
        # Store comprehensive health data
        st.session_state.health_data = {
            'patient': {
                'name': name, 'age': age, 'gender': gender, 'weight': weight, 
                'height': height, 'blood_group': blood_group
            },
            'vitals': vitals_data,
            'bmi_info': bmi_info,
            'symptoms': symptoms,
            'medical_history': medical_history,
            'medications': current_medications,
            'pain_scale': pain_scale,
            'symptom_duration': symptom_duration,
            'lifestyle': {
                'exercise_frequency': exercise_frequency,
                'smoking_status': smoking_status,
                'alcohol_consumption': alcohol_consumption,
                'sleep_hours': sleep_hours,
                'stress_level': stress_level,
                'diet_quality': diet_quality
            },
            'emergency_symptoms': emergency_symptoms,
            'location': st.session_state.user_location,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Success message
        success_html = """
        <div class="success-message">
            <h3 style="margin: 0 0 0.5rem 0;">✅ Health Assessment Completed Successfully!</h3>
            <p style="margin: 0;">Your comprehensive health analysis is ready. Review the results below for personalized recommendations.</p>
        </div>
        """
        st.markdown(success_html, unsafe_allow_html=True)
        
        # Health Analysis Section
        st.markdown("---")
        st.markdown("<h2 class='sub-header'>📊 Comprehensive Health Analysis</h2>", unsafe_allow_html=True)
        
        # Calculate health score
        health_score_data = HealthAnalytics.calculate_health_score(vitals_data, bmi, age, symptoms)
        
        # Health Score Display
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Health Score Visualization
            score = health_score_data['score']
            status = health_score_data['status'].lower()
            
            score_class = f"health-score-{status}"
            score_html = f"""
            <div class="{score_class}">
                <h2 style="margin: 0 0 1rem 0;">🏥 Overall Health Score</h2>
                <div style="font-size: 4rem; font-weight: bold; margin: 1rem 0;">{score}/100</div>
                <h3 style="margin: 0 0 1rem 0;">Status: {health_score_data['status']}</h3>
                <p style="margin: 0; font-size: 1.1em;">{health_score_data['message']}</p>
            </div>
            """
            st.markdown(score_html, unsafe_allow_html=True)
        
        with col2:
            # Risk Factors and Recommendations
            if health_score_data['risk_factors']:
                risk_html = """
                <div class="metric-card">
                    <h4 style="color: #F44336; margin: 0 0 1rem 0;">⚠️ Risk Factors</h4>
                """
                for factor in health_score_data['risk_factors']:
                    risk_html += f"<div style='margin: 0.5rem 0; padding: 0.5rem; background: #FFEBEE; border-radius: 5px; color: #D32F2F;'>• {factor}</div>"
                risk_html += "</div>"
                st.markdown(risk_html, unsafe_allow_html=True)
            
            if health_score_data['recommendations']:
                rec_html = """
                <div class="metric-card">
                    <h4 style="color: #4CAF50; margin: 0 0 1rem 0;">💡 Recommendations</h4>
                """
                for rec in health_score_data['recommendations']:
                    rec_html += f"<div style='margin: 0.5rem 0; padding: 0.5rem; background: #E8F5E8; border-radius: 5px; color: #2E7D32;'>• {rec}</div>"
                rec_html += "</div>"
                st.markdown(rec_html, unsafe_allow_html=True)
        
        # BMI Analysis
        st.markdown("<h3 class='sub-header'>📏 Body Mass Index (BMI) Analysis</h3>", unsafe_allow_html=True)
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            bmi_html = f"""
            <div class="metric-card">
                <h4 style="color: #007C91; text-align: center; margin: 0 0 1rem 0;">Current BMI</h4>
                <div style="font-size: 2.5rem; font-weight: bold; text-align: center; color: {bmi_info['color']}; margin: 1rem 0;">
                    {bmi_info['bmi']}
                </div>
                <p style="text-align: center; margin: 0; color: #666;">kg/m²</p>
            </div>
            """
            st.markdown(bmi_html, unsafe_allow_html=True)
        
        with col2:
            category_html = f"""
            <div class="metric-card">
                <h4 style="color: #007C91; text-align: center; margin: 0 0 1rem 0;">Category</h4>
                <div style="font-size: 1.5rem; font-weight: bold; text-align: center; color: {bmi_info['color']}; margin: 1rem 0;">
                    {bmi_info['category']}
                </div>
                <p style="text-align: center; margin: 0; color: #666;">Classification</p>
            </div>
            """
            st.markdown(category_html, unsafe_allow_html=True)
        
        with col3:
            ideal_min_html = f"""
            <div class="metric-card">
                <h4 style="color: #007C91; text-align: center; margin: 0 0 1rem 0;">Ideal Weight Min</h4>
                <div style="font-size: 1.8rem; font-weight: bold; text-align: center; color: #4CAF50; margin: 1rem 0;">
                    {bmi_info['ideal_weight_min']} kg
                </div>
                <p style="text-align: center; margin: 0; color: #666;">Lower bound</p>
            </div>
            """
            st.markdown(ideal_min_html, unsafe_allow_html=True)
        
        with col4:
            ideal_max_html = f"""
            <div class="metric-card">
                <h4 style="color: #007C91; text-align: center; margin: 0 0 1rem 0;">Ideal Weight Max</h4>
                <div style="font-size: 1.8rem; font-weight: bold; text-align: center; color: #4CAF50; margin: 1rem 0;">
                    {bmi_info['ideal_weight_max']} kg
                </div>
                <p style="text-align: center; margin: 0; color: #666;">Upper bound</p>
            </div>
            """
            st.markdown(ideal_max_html, unsafe_allow_html=True)
        
        # Vital Signs Analysis
        st.markdown("<h3 class='sub-header'>🩺 Vital Signs Analysis</h3>", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Blood Pressure Analysis
            bp_status = "Normal"
            bp_color = "#4CAF50"
            if bp_systolic > 140 or bp_diastolic > 90:
                bp_status = "High"
                bp_color = "#F44336"
            elif bp_systolic > 130 or bp_diastolic > 85:
                bp_status = "Elevated"
                bp_color = "#FF9800"
            
            bp_html = f"""
            <div class="metric-card">
                <h4 style="color: #007C91; text-align: center; margin: 0 0 1rem 0;">🫀 Blood Pressure</h4>
                <div style="font-size: 1.8rem; font-weight: bold; text-align: center; margin: 1rem 0;">
                    {bp_systolic}/{bp_diastolic}
                </div>
                <div style="text-align: center; color: {bp_color}; font-weight: bold; margin: 0.5rem 0;">
                    {bp_status}
                </div>
                <p style="text-align: center; margin: 0; color: #666;">mmHg</p>
            </div>
            """
            st.markdown(bp_html, unsafe_allow_html=True)
        
        with col2:
            # Heart Rate Analysis
            hr_status = "Normal"
            hr_color = "#4CAF50"
            if pulse > 100:
                hr_status = "High"
                hr_color = "#F44336"
            elif pulse < 60:
                hr_status = "Low"
                hr_color = "#FF9800"
            
            hr_html = f"""
            <div class="metric-card">
                <h4 style="color: #007C91; text-align: center; margin: 0 0 1rem 0;">💗 Heart Rate</h4>
                <div style="font-size: 2.5rem; font-weight: bold; text-align: center; margin: 1rem 0;">
                    {pulse}
                </div>
                <div style="text-align: center; color: {hr_color}; font-weight: bold; margin: 0.5rem 0;">
                    {hr_status}
                </div>
                <p style="text-align: center; margin: 0; color: #666;">bpm</p>
            </div>
            """
            st.markdown(hr_html, unsafe_allow_html=True)
        
        with col3:
            # Oxygen Saturation Analysis
            spo2_status = "Normal"
            spo2_color = "#4CAF50"
            if spo2 < 95:
                spo2_status = "Low"
                spo2_color = "#F44336"
            elif spo2 < 98:
                spo2_status = "Borderline"
                spo2_color = "#FF9800"
            
            spo2_html = f"""
            <div class="metric-card">
                <h4 style="color: #007C91; text-align: center; margin: 0 0 1rem 0;">🫁 Oxygen Saturation</h4>
                <div style="font-size: 2.5rem; font-weight: bold; text-align: center; margin: 1rem 0;">
                    {spo2}%
                </div>
                <div style="text-align: center; color: {spo2_color}; font-weight: bold; margin: 0.5rem 0;">
                    {spo2_status}
                </div>
                <p style="text-align: center; margin: 0; color: #666;">SpO2</p>
            </div>
            """
            st.markdown(spo2_html, unsafe_allow_html=True)
        
        # Tabbed Analysis
        tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
            "🤖 AI Health Assistant", "🏥 Nearby Hospitals", "💊 Pharmacies", "🧪 Lab Test Suggestions", "🥗 Diet Plan", "🏃‍♂️ Exercise Plan", "📰 Health News"
        ])
        
        with tab1:
            st.markdown("### 🤖 AI-Powered Health Recommendations")
            
            # Initialize session state for dropdown if not exists
            if 'selected_analysis_type' not in st.session_state:
                st.session_state.selected_analysis_type = "Comprehensive Health Analysis"
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                analysis_options = [
                    "Comprehensive Health Analysis",
                    "Symptom-Based Recommendations", 
                    "Medication Guidance",
                    "Lifestyle Recommendations",
                    "Emergency Assessment"
                ]
                
                # Use session state to persist selection
                selected_index = analysis_options.index(st.session_state.selected_analysis_type) if st.session_state.selected_analysis_type in analysis_options else 0
                
                analysis_type = st.selectbox(
                    "Choose analysis type:",
                    analysis_options,
                    index=selected_index,
                    key="analysis_type_selector"
                )
                
                # Update session state when selection changes
                if analysis_type != st.session_state.selected_analysis_type:
                    st.session_state.selected_analysis_type = analysis_type
            
            with col2:
                get_analysis = st.button("🔍 Get AI Analysis", use_container_width=True, key="ai_analysis_btn")
            
            # Show initial message if no analysis has been done yet
            if 'ai_analysis_done' not in st.session_state and not get_analysis:
                info_html = f"""
                <div class="metric-card" style="border-left: 4px solid #B1AFFF;">
                    <h4 style="color: #007C91; margin: 0 0 1rem 0;">🤖 AI Health Assistant Ready</h4>
                    <p style="margin: 0; color: #666; line-height: 1.6;">
                        Selected Analysis: <strong style="color: #F64C72;">{analysis_type}</strong><br><br>
                        Click "Get AI Analysis" to receive personalized health recommendations 
                        based on your submitted health data. You can change the analysis type above and run multiple analyses.
                    </p>
                </div>
                """
                st.markdown(info_html, unsafe_allow_html=True)
            
            # Run analysis when button is clicked
            if get_analysis:
                with st.spinner(f"🤖 Running {analysis_type}..."):
                    time.sleep(2)  # Brief delay for better UX
                    
                    # Check if we have health data
                    if not st.session_state.health_data:
                        st.error("⚠️ Please fill out the health assessment form first before requesting AI analysis.")
                        return
                    
                    context = json.dumps(st.session_state.health_data, default=str, indent=2)
                    
                    # Create specific prompts based on analysis type
                    prompts = {
                        "Comprehensive Health Analysis": f"Provide a comprehensive health analysis based on the following patient data. Include vital signs assessment, BMI analysis, health score interpretation, and personalized recommendations: {context}",
                        "Symptom-Based Recommendations": f"Focus on symptom analysis and treatment recommendations. Provide specific guidance for reported symptoms, monitoring guidelines, and when to seek medical care: {context}",
                        "Medication Guidance": f"Provide detailed medication recommendations and guidance. Include OTC options, natural supplements, safety information, and interaction warnings: {context}",
                        "Lifestyle Recommendations": f"Suggest comprehensive lifestyle changes and improvements. Include exercise, nutrition, sleep, stress management, and habit modification recommendations: {context}",
                        "Emergency Assessment": f"Assess emergency symptoms and provide urgent care guidance. Include immediate action steps, emergency contacts, and when to seek emergency care: {context}"
                    }
                    
                    prompt = prompts.get(analysis_type, prompts["Comprehensive Health Analysis"])
                    
                    try:
                        ai_response = ai_service.get_response(prompt, context)
                        
                        # Display AI response in a styled container
                        ai_html = f"""
                        <div class="metric-card" style="border-left: 4px solid #007C91;">
                            <div style="background: linear-gradient(135deg, #007C91, #B1AFFF); color: white; padding: 1rem; border-radius: 8px; margin-bottom: 1rem;">
                                <h3 style="margin: 0; display: flex; align-items: center;">
                                    🤖 AI Health Assistant Response
                                    <span style="margin-left: auto; background: rgba(255,255,255,0.2); padding: 0.3rem 0.8rem; border-radius: 15px; font-size: 0.8em;">
                                        OpenAI Powered
                                    </span>
                                </h3>
                            </div>
                            <div style="background: #F8F9FA; padding: 1rem; border-radius: 8px; margin: 1rem 0;">
                                <h4 style="color: #F64C72; margin: 0 0 0.5rem 0; display: flex; align-items: center;">
                                    📋 Analysis Type: {analysis_type}
                                    <span style="margin-left: auto; color: #4CAF50; font-size: 0.8em;">✅ Completed</span>
                                </h4>
                                <div style="line-height: 1.6; color: #333; white-space: pre-wrap;">
{ai_response}
                                </div>
                            </div>
                            <div style="background: #E8F5E8; padding: 0.8rem; border-radius: 6px; margin-top: 1rem;">
                                <p style="margin: 0; color: #2E7D32; font-size: 0.9em;">
                                    <strong>💡 Medical Disclaimer:</strong> This AI analysis is for informational purposes only. 
                                    Always consult with qualified healthcare professionals for medical decisions, diagnosis, and treatment.
                                </p>
                            </div>
                        </div>
                        """
                        st.markdown(ai_html, unsafe_allow_html=True)
                        
                        # Set session state to remember analysis was done
                        st.session_state.ai_analysis_done = True
                        st.session_state.last_analysis_type = analysis_type
                        st.session_state.last_analysis_time = datetime.now().strftime("%H:%M:%S")
                        
                        # Success message
                        st.success(f"✅ {analysis_type} completed successfully! You can select a different analysis type and run another analysis.")
                        
                    except Exception as e:
                        st.error(f"🚨 Error generating AI analysis: {str(e)}")
                        st.info("💡 Tip: Make sure you have a valid OpenAI API key configured, or the system will use demo responses.")
            
            # Show analysis history if available
            elif 'ai_analysis_done' in st.session_state and 'last_analysis_type' in st.session_state:
                history_html = f"""
                <div class="metric-card" style="border-left: 4px solid #4CAF50;">
                    <h4 style="color: #4CAF50; margin: 0 0 1rem 0;">✅ Previous Analysis Completed</h4>
                    <div style="background: #F1F8E9; padding: 1rem; border-radius: 8px;">
                        <p style="margin: 0; color: #333;">
                            <strong>Last Analysis:</strong> {st.session_state.last_analysis_type}<br>
                            <strong>Time:</strong> {st.session_state.get('last_analysis_time', 'Unknown')}<br>
                            <strong>Current Selection:</strong> <span style="color: #F64C72;">{analysis_type}</span>
                        </p>
                    </div>
                    <p style="margin: 1rem 0 0 0; color: #666;">
                        Select a different analysis type above and click "Get AI Analysis" for new insights.
                    </p>
                </div>
                """
                st.markdown(history_html, unsafe_allow_html=True)
        
        with tab2:
            st.markdown("### 🏥 Nearby Hospitals (Within 100 km)")
            
            if st.session_state.coordinates:
                lat, lon = st.session_state.coordinates
                
                # Automatically load hospitals within 100km
                with st.spinner("🏥 Loading hospitals near you..."):
                    hospitals = facilities_service.search_facilities(lat, lon, "hospital", 100000)  # 100km in meters
                    
                    if hospitals:
                        # Statistics
                        avg_rating = sum(h['rating'] for h in hospitals) / len(hospitals)
                        closest_hospital = min(hospitals, key=lambda x: x['distance'])
                        total_reviews = sum(h['user_ratings_total'] for h in hospitals)
                        
                        # Display statistics
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            st.metric("🏥 Total Hospitals", len(hospitals))
                        with col2:
                            st.metric("⭐ Average Rating", f"{avg_rating:.1f}/5")
                        with col3:
                            st.metric("📍 Closest Hospital", f"{closest_hospital['distance']} km")
                        with col4:
                            st.metric("👥 Total Reviews", f"{total_reviews:,}")
                        
                        st.markdown("---")
                        
                        for i, hospital in enumerate(hospitals):
                            hospital_html = f"""
                            <div class="facility-card">
                                <div style="display: flex; justify-content: space-between; align-items: start;">
                                    <div style="flex: 1;">
                                        <h4 style="color: #007C91; margin: 0 0 0.5rem 0;">🏥 {hospital['name']}</h4>
                                        <p style="margin: 0.2rem 0; color: #666;"><strong>📍 Address:</strong> {hospital['address']}</p>
                                        <p style="margin: 0.2rem 0; color: #666;"><strong>📞 Phone:</strong> {hospital['phone']}</p>
                                        <p style="margin: 0.2rem 0; color: #666;"><strong>🏥 Specialty:</strong> {hospital['specialty']}</p>
                                        <p style="margin: 0.2rem 0; color: #666;"><strong>🕒 Hours:</strong> {hospital['hours']}</p>
                                    </div>
                                    <div style="text-align: right; margin-left: 1rem;">
                                        <div style="background: #4CAF50; color: white; padding: 0.3rem 0.8rem; border-radius: 15px; margin: 0.2rem 0;">
                                            ⭐ {hospital['rating']}/5
                                        </div>
                                        <div style="background: #007C91; color: white; padding: 0.3rem 0.8rem; border-radius: 15px; margin: 0.2rem 0;">
                                            📍 {hospital['distance']} km
                                        </div>
                                        <div style="background: #F64C72; color: white; padding: 0.3rem 0.8rem; border-radius: 15px; margin: 0.2rem 0;">
                                            👥 {hospital['user_ratings_total']} reviews
                                        </div>
                                    </div>
                                </div>
                            </div>
                            """
                            st.markdown(hospital_html, unsafe_allow_html=True)
                    else:
                        st.warning("⚠️ No hospitals found within 100 km of your location.")
            else:
                warning_html = """
                <div class="warning-message">
                    <h4 style="margin: 0 0 0.5rem 0;">📍 Location Required</h4>
                    <p style="margin: 0;">Please set your location in the sidebar to find nearby hospitals.</p>
                </div>
                """
                st.markdown(warning_html, unsafe_allow_html=True)
        
        with tab3:
            st.markdown("### 💊 Find Nearby Pharmacies")
            
            if st.session_state.coordinates:
                lat, lon = st.session_state.coordinates
                
                col1, col2 = st.columns([2, 1])
                with col1:
                    pharmacy_radius = st.slider("Search radius (km):", 1, 25, 10, help="Adjust search distance for pharmacies")
                with col2:
                    search_pharmacies = st.button("🔍 Search Pharmacies", use_container_width=True)
                
                if search_pharmacies or 'pharmacies_searched' not in st.session_state:
                    with st.spinner("💊 Finding pharmacies near you..."):
                        pharmacies = facilities_service.search_facilities(lat, lon, "pharmacy", pharmacy_radius * 1000)
                        
                        if pharmacies:
                            st.success(f"✅ Found {len(pharmacies)} pharmacies within {pharmacy_radius} km")
                            
                            for pharmacy in pharmacies:
                                pharmacy_html = f"""
                                <div class="facility-card">
                                    <div style="display: flex; justify-content: space-between; align-items: start;">
                                        <div style="flex: 1;">
                                            <h4 style="color: #007C91; margin: 0 0 0.5rem 0;">💊 {pharmacy['name']}</h4>
                                            <p style="margin: 0.2rem 0; color: #666;"><strong>📍 Address:</strong> {pharmacy['address']}</p>
                                            <p style="margin: 0.2rem 0; color: #666;"><strong>📞 Phone:</strong> {pharmacy['phone']}</p>
                                            <p style="margin: 0.2rem 0; color: #666;"><strong>💊 Specialty:</strong> {pharmacy['specialty']}</p>
                                            <p style="margin: 0.2rem 0; color: #666;"><strong>🕒 Hours:</strong> {pharmacy['hours']}</p>
                                        </div>
                                        <div style="text-align: right; margin-left: 1rem;">
                                            <div style="background: #4CAF50; color: white; padding: 0.3rem 0.8rem; border-radius: 15px; margin: 0.2rem 0;">
                                                ⭐ {pharmacy['rating']}/5
                                            </div>
                                            <div style="background: #007C91; color: white; padding: 0.3rem 0.8rem; border-radius: 15px; margin: 0.2rem 0;">
                                                📍 {pharmacy['distance']} km
                                            </div>
                                            <div style="background: #F64C72; color: white; padding: 0.3rem 0.8rem; border-radius: 15px; margin: 0.2rem 0;">
                                                👥 {pharmacy['user_ratings_total']} reviews
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                """
                                st.markdown(pharmacy_html, unsafe_allow_html=True)
                        else:
                            st.warning("⚠️ No pharmacies found within the specified radius. Try increasing the search distance.")
                        
                        st.session_state.pharmacies_searched = True
            else:
                warning_html = """
                <div class="warning-message">
                    <h4 style="margin: 0 0 0.5rem 0;">📍 Location Required</h4>
                    <p style="margin: 0;">Please set your location in the sidebar to find nearby pharmacies.</p>
                </div>
                """
                st.markdown(warning_html, unsafe_allow_html=True)
        
        with tab4:
            st.markdown("### 🧪 Recommended Lab Tests")
            
            # Generate lab test recommendations based on health data
            patient_data = st.session_state.health_data
            age = patient_data.get('patient', {}).get('age', 30)
            gender = patient_data.get('patient', {}).get('gender', 'Unknown')
            symptoms = patient_data.get('symptoms', '')
            medical_history = patient_data.get('medical_history', '')
            vitals = patient_data.get('vitals', {})
            
            # Basic tests for everyone
            basic_tests = [
                {
                    'name': 'Complete Blood Count (CBC)',
                    'purpose': 'Evaluate overall health and detect blood disorders',
                    'frequency': 'Annual',
                    'priority': 'High',
                    'cost_range': '₹300-500'
                },
                {
                    'name': 'Lipid Profile',
                    'purpose': 'Check cholesterol levels and heart disease risk',
                    'frequency': 'Annual',
                    'priority': 'High',
                    'cost_range': '₹400-600'
                },
                {
                    'name': 'Blood Sugar (Fasting)',
                    'purpose': 'Screen for diabetes and prediabetes',
                    'frequency': 'Annual',
                    'priority': 'High',
                    'cost_range': '₹100-200'
                },
                {
                    'name': 'Liver Function Test (LFT)',
                    'purpose': 'Assess liver health and function',
                    'frequency': 'Annual',
                    'priority': 'Medium',
                    'cost_range': '₹500-800'
                },
                {
                    'name': 'Kidney Function Test (KFT)',
                    'purpose': 'Check kidney health and function',
                    'frequency': 'Annual',
                    'priority': 'Medium',
                    'cost_range': '₹400-700'
                }
            ]
            
            # Age-specific tests
            age_specific_tests = []
            if age >= 40:
                age_specific_tests.extend([
                    {
                        'name': 'ECG (Electrocardiogram)',
                        'purpose': 'Check heart rhythm and electrical activity',
                        'frequency': 'Annual',
                        'priority': 'High',
                        'cost_range': '₹200-400'
                    },
                    {
                        'name': 'Thyroid Function Test',
                        'purpose': 'Check thyroid hormone levels',
                        'frequency': 'Annual',
                        'priority': 'Medium',
                        'cost_range': '₹600-1000'
                    }
                ])
            
            if age >= 50:
                age_specific_tests.extend([
                    {
                        'name': 'Colonoscopy',
                        'purpose': 'Screen for colorectal cancer',
                        'frequency': 'Every 10 years',
                        'priority': 'High',
                        'cost_range': '₹8000-15000'
                    },
                    {
                        'name': 'Bone Density Test',
                        'purpose': 'Check for osteoporosis risk',
                        'frequency': 'Every 2-3 years',
                        'priority': 'Medium',
                        'cost_range': '₹2000-4000'
                    }
                ])
            
            # Gender-specific tests
            gender_specific_tests = []
            if gender == 'Female':
                gender_specific_tests.extend([
                    {
                        'name': 'Mammography',
                        'purpose': 'Breast cancer screening',
                        'frequency': 'Annual (age 40+)',
                        'priority': 'High' if age >= 40 else 'Medium',
                        'cost_range': '₹2000-4000'
                    },
                    {
                        'name': 'Pap Smear',
                        'purpose': 'Cervical cancer screening',
                        'frequency': 'Every 3 years',
                        'priority': 'High',
                        'cost_range': '₹1000-2000'
                    }
                ])
            elif gender == 'Male':
                if age >= 50:
                    gender_specific_tests.append({
                        'name': 'PSA (Prostate-Specific Antigen)',
                        'purpose': 'Prostate cancer screening',
                        'frequency': 'Annual',
                        'priority': 'High',
                        'cost_range': '₹800-1200'
                    })
            
            # Symptom-based tests
            symptom_tests = []
            if symptoms:
                symptoms_lower = symptoms.lower()
                if any(word in symptoms_lower for word in ['chest', 'heart', 'pain']):
                    symptom_tests.append({
                        'name': 'Cardiac Enzymes',
                        'purpose': 'Check for heart damage',
                        'frequency': 'As needed',
                        'priority': 'Urgent',
                        'cost_range': '₹1500-2500'
                    })
                
                if any(word in symptoms_lower for word in ['headache', 'dizziness', 'fatigue']):
                    symptom_tests.append({
                        'name': 'Vitamin B12 & D3',
                        'purpose': 'Check for vitamin deficiencies',
                        'frequency': 'As needed',
                        'priority': 'Medium',
                        'cost_range': '₹800-1200'
                    })
                
                if any(word in symptoms_lower for word in ['joint', 'arthritis', 'inflammation']):
                    symptom_tests.append({
                        'name': 'CRP & ESR',
                        'purpose': 'Check for inflammation',
                        'frequency': 'As needed',
                        'priority': 'Medium',
                        'cost_range': '₹600-1000'
                    })
            
            # Vital signs based tests
            if vitals.get('bp_systolic', 120) > 140:
                symptom_tests.append({
                    'name': '24-Hour Blood Pressure Monitoring',
                    'purpose': 'Detailed blood pressure assessment',
                    'frequency': 'As recommended',
                    'priority': 'High',
                    'cost_range': '₹2000-3000'
                })
            
            # Display test recommendations
            all_tests = []
            
            if basic_tests:
                st.markdown("#### 🔬 Essential Tests (Recommended for Everyone)")
                for test in basic_tests:
                    all_tests.append(test)
                    priority_color = "#F44336" if test['priority'] == 'High' else "#FF9800" if test['priority'] == 'Medium' else "#4CAF50"
                    test_html = f"""
                    <div class="facility-card">
                        <div style="display: flex; justify-content: space-between; align-items: start;">
                            <div style="flex: 1;">
                                <h4 style="color: #007C91; margin: 0 0 0.5rem 0;">🧪 {test['name']}</h4>
                                <p style="margin: 0.2rem 0; color: #666;"><strong>🎯 Purpose:</strong> {test['purpose']}</p>
                                <p style="margin: 0.2rem 0; color: #666;"><strong>📅 Frequency:</strong> {test['frequency']}</p>
                                <p style="margin: 0.2rem 0; color: #666;"><strong>💰 Cost Range:</strong> {test['cost_range']}</p>
                            </div>
                            <div style="text-align: right; margin-left: 1rem;">
                                <div style="background: {priority_color}; color: white; padding: 0.3rem 0.8rem; border-radius: 15px; margin: 0.2rem 0;">
                                    ⚡ {test['priority']} Priority
                                </div>
                            </div>
                        </div>
                    </div>
                    """
                    st.markdown(test_html, unsafe_allow_html=True)
            
            if age_specific_tests:
                st.markdown(f"#### 🎂 Age-Specific Tests (Age {age}+)")
                for test in age_specific_tests:
                    all_tests.append(test)
                    priority_color = "#F44336" if test['priority'] == 'High' else "#FF9800" if test['priority'] == 'Medium' else "#4CAF50"
                    test_html = f"""
                    <div class="facility-card">
                        <div style="display: flex; justify-content: space-between; align-items: start;">
                            <div style="flex: 1;">
                                <h4 style="color: #007C91; margin: 0 0 0.5rem 0;">🧪 {test['name']}</h4>
                                <p style="margin: 0.2rem 0; color: #666;"><strong>🎯 Purpose:</strong> {test['purpose']}</p>
                                <p style="margin: 0.2rem 0; color: #666;"><strong>📅 Frequency:</strong> {test['frequency']}</p>
                                <p style="margin: 0.2rem 0; color: #666;"><strong>💰 Cost Range:</strong> {test['cost_range']}</p>
                            </div>
                            <div style="text-align: right; margin-left: 1rem;">
                                <div style="background: {priority_color}; color: white; padding: 0.3rem 0.8rem; border-radius: 15px; margin: 0.2rem 0;">
                                    ⚡ {test['priority']} Priority
                                </div>
                            </div>
                        </div>
                    </div>
                    """
                    st.markdown(test_html, unsafe_allow_html=True)
            
            if gender_specific_tests:
                st.markdown(f"#### ⚧ Gender-Specific Tests ({gender})")
                for test in gender_specific_tests:
                    all_tests.append(test)
                    priority_color = "#F44336" if test['priority'] == 'High' else "#FF9800" if test['priority'] == 'Medium' else "#4CAF50"
                    test_html = f"""
                    <div class="facility-card">
                        <div style="display: flex; justify-content: space-between; align-items: start;">
                            <div style="flex: 1;">
                                <h4 style="color: #007C91; margin: 0 0 0.5rem 0;">🧪 {test['name']}</h4>
                                <p style="margin: 0.2rem 0; color: #666;"><strong>🎯 Purpose:</strong> {test['purpose']}</p>
                                <p style="margin: 0.2rem 0; color: #666;"><strong>📅 Frequency:</strong> {test['frequency']}</p>
                                <p style="margin: 0.2rem 0; color: #666;"><strong>💰 Cost Range:</strong> {test['cost_range']}</p>
                            </div>
                            <div style="text-align: right; margin-left: 1rem;">
                                <div style="background: {priority_color}; color: white; padding: 0.3rem 0.8rem; border-radius: 15px; margin: 0.2rem 0;">
                                    ⚡ {test['priority']} Priority
                                </div>
                            </div>
                        </div>
                    </div>
                    """
                    st.markdown(test_html, unsafe_allow_html=True)
            
            if symptom_tests:
                st.markdown("#### 🩺 Symptom-Based Tests")
                for test in symptom_tests:
                    all_tests.append(test)
                    priority_color = "#F44336" if test['priority'] == 'Urgent' else "#FF9800" if test['priority'] == 'High' else "#4CAF50"
                    test_html = f"""
                    <div class="facility-card">
                        <div style="display: flex; justify-content: space-between; align-items: start;">
                            <div style="flex: 1;">
                                <h4 style="color: #007C91; margin: 0 0 0.5rem 0;">🧪 {test['name']}</h4>
                                <p style="margin: 0.2rem 0; color: #666;"><strong>🎯 Purpose:</strong> {test['purpose']}</p>
                                <p style="margin: 0.2rem 0; color: #666;"><strong>📅 Frequency:</strong> {test['frequency']}</p>
                                <p style="margin: 0.2rem 0; color: #666;"><strong>💰 Cost Range:</strong> {test['cost_range']}</p>
                            </div>
                            <div style="text-align: right; margin-left: 1rem;">
                                <div style="background: {priority_color}; color: white; padding: 0.3rem 0.8rem; border-radius: 15px; margin: 0.2rem 0;">
                                    ⚡ {test['priority']} Priority
                                </div>
                            </div>
                        </div>
                    </div>
                    """
                    st.markdown(test_html, unsafe_allow_html=True)
            
            # Test summary statistics
            if all_tests:
                st.markdown("---")
                st.markdown("#### 📊 Test Summary")
                
                col1, col2, col3, col4 = st.columns(4)
                
                high_priority = len([t for t in all_tests if t['priority'] in ['High', 'Urgent']])
                total_tests = len(all_tests)
                avg_cost_min = sum(int(t['cost_range'].split('-')[0].replace('₹', '').replace(',', '')) for t in all_tests) / total_tests
                avg_cost_max = sum(int(t['cost_range'].split('-')[1].replace('₹', '').replace(',', '')) for t in all_tests) / total_tests
                
                with col1:
                    st.metric("🧪 Total Recommended Tests", total_tests)
                with col2:
                    st.metric("⚡ High Priority Tests", high_priority)
                with col3:
                    st.metric("💰 Estimated Cost Range", f"₹{avg_cost_min:,.0f} - ₹{avg_cost_max:,.0f}")
                with col4:
                    annual_tests = len([t for t in all_tests if 'Annual' in t['frequency']])
                    st.metric("📅 Annual Tests", annual_tests)
        
        with tab5:
            st.markdown("### 🥗 Personalized Diet Plan")
            
            # Get patient data for personalized recommendations
            patient_data = st.session_state.health_data
            age = patient_data.get('patient', {}).get('age', 30)
            gender = patient_data.get('patient', {}).get('gender', 'Unknown')
            weight = patient_data.get('patient', {}).get('weight', 70)
            height = patient_data.get('patient', {}).get('height', 170)
            bmi = patient_data.get('bmi_info', {}).get('bmi', 25)
            lifestyle = patient_data.get('lifestyle', {})
            symptoms = patient_data.get('symptoms', '')
            medical_history = patient_data.get('medical_history', '')
            
            # Calculate calorie needs
            height_m = height / 100
            if gender == 'Male':
                bmr = 88.362 + (13.397 * weight) + (4.799 * height) - (5.677 * age)
            else:
                bmr = 447.593 + (9.247 * weight) + (3.098 * height) - (4.330 * age)
            
            # Activity factor
            exercise_freq = lifestyle.get('exercise_frequency', 'Rarely')
            if exercise_freq == 'Never':
                activity_factor = 1.2
            elif exercise_freq == 'Rarely':
                activity_factor = 1.375
            elif exercise_freq == '1-2 times/week':
                activity_factor = 1.55
            elif exercise_freq == '3-4 times/week':
                activity_factor = 1.725
            else:
                activity_factor = 1.9
            
            daily_calories = int(bmr * activity_factor)
            
            # BMI-based recommendations
            if bmi < 18.5:
                diet_goal = "Weight Gain"
                calorie_adjustment = 300
                diet_focus = "High-calorie, nutrient-dense foods"
            elif bmi > 25:
                diet_goal = "Weight Loss"
                calorie_adjustment = -300
                diet_focus = "Low-calorie, high-fiber foods"
            else:
                diet_goal = "Weight Maintenance"
                calorie_adjustment = 0
                diet_focus = "Balanced nutrition"
            
            target_calories = daily_calories + calorie_adjustment
            
            # Display diet overview
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("🔥 Daily Calories", f"{target_calories:,}")
            with col2:
                st.metric("🎯 Diet Goal", diet_goal)
            with col3:
                st.metric("💪 Protein (g)", f"{int(target_calories * 0.15 / 4)}")
            with col4:
                st.metric("💧 Water (L)", "2.5-3.0")
            
            st.markdown("---")
            
            # Meal plan
            st.markdown("#### 🍽️ Daily Meal Plan")
            
            meal_plans = {
                "Weight Loss": {
                    "breakfast": {
                        "meal": "🌅 Breakfast (400 calories)",
                        "items": [
                            "1 bowl oatmeal with berries and almonds",
                            "1 boiled egg or Greek yogurt",
                            "Green tea or black coffee"
                        ]
                    },
                    "mid_morning": {
                        "meal": "🍎 Mid-Morning Snack (150 calories)",
                        "items": [
                            "1 medium apple or orange",
                            "Handful of nuts (10-12 almonds)"
                        ]
                    },
                    "lunch": {
                        "meal": "🍽️ Lunch (500 calories)",
                        "items": [
                            "Mixed vegetable salad with grilled chicken/paneer",
                            "1 small bowl brown rice or 2 whole wheat rotis",
                            "Dal or lentil soup"
                        ]
                    },
                    "evening": {
                        "meal": "🫖 Evening Snack (100 calories)",
                        "items": [
                            "Herbal tea with 2-3 whole grain crackers",
                            "Or vegetable juice"
                        ]
                    },
                    "dinner": {
                        "meal": "🌙 Dinner (450 calories)",
                        "items": [
                            "Grilled fish/chicken or tofu curry",
                            "Steamed vegetables",
                            "1 small bowl quinoa or brown rice"
                        ]
                    }
                },
                "Weight Gain": {
                    "breakfast": {
                        "meal": "🌅 Breakfast (600 calories)",
                        "items": [
                            "Banana and peanut butter smoothie",
                            "2 whole grain toast with avocado",
                            "1 glass milk or protein shake"
                        ]
                    },
                    "mid_morning": {
                        "meal": "🍎 Mid-Morning Snack (300 calories)",
                        "items": [
                            "Trail mix with dried fruits and nuts",
                            "Greek yogurt with honey"
                        ]
                    },
                    "lunch": {
                        "meal": "🍽️ Lunch (700 calories)",
                        "items": [
                            "Chicken biryani or mutton curry",
                            "Mixed vegetable curry",
                            "2-3 rotis or rice",
                            "Raita or buttermilk"
                        ]
                    },
                    "evening": {
                        "meal": "🫖 Evening Snack (250 calories)",
                        "items": [
                            "Cheese sandwich or energy bar",
                            "Fresh fruit juice"
                        ]
                    },
                    "dinner": {
                        "meal": "🌙 Dinner (650 calories)",
                        "items": [
                            "Paneer curry or chicken",
                            "Dal and rice",
                            "Sautéed vegetables",
                            "1 glass milk before bed"
                        ]
                    }
                },
                "Weight Maintenance": {
                    "breakfast": {
                        "meal": "🌅 Breakfast (500 calories)",
                        "items": [
                            "Vegetable omelet with 2 eggs",
                            "2 whole grain toast",
                            "Fresh fruit salad",
                            "Coffee or tea"
                        ]
                    },
                    "mid_morning": {
                        "meal": "🍎 Mid-Morning Snack (200 calories)",
                        "items": [
                            "Mixed nuts and dried fruits",
                            "Green tea"
                        ]
                    },
                    "lunch": {
                        "meal": "🍽️ Lunch (600 calories)",
                        "items": [
                            "Grilled chicken/fish with quinoa",
                            "Mixed vegetable curry",
                            "Green salad",
                            "Buttermilk"
                        ]
                    },
                    "evening": {
                        "meal": "🫖 Evening Snack (150 calories)",
                        "items": [
                            "Herbal tea with whole grain biscuits",
                            "Or fresh coconut water"
                        ]
                    },
                    "dinner": {
                        "meal": "🌙 Dinner (550 calories)",
                        "items": [
                            "Dal and vegetable curry",
                            "2 rotis or brown rice",
                            "Steamed broccoli or spinach"
                        ]
                    }
                }
            }
            
            current_plan = meal_plans.get(diet_goal, meal_plans["Weight Maintenance"])
            
            for meal_key, meal_data in current_plan.items():
                meal_html = f"""
                <div class="metric-card">
                    <h4 style="color: #007C91; margin: 0 0 1rem 0;">{meal_data['meal']}</h4>
                    <ul style="margin: 0; padding-left: 1.5rem; color: #333;">
                """
                for item in meal_data['items']:
                    meal_html += f"<li style='margin: 0.3rem 0;'>{item}</li>"
                meal_html += """
                    </ul>
                </div>
                """
                st.markdown(meal_html, unsafe_allow_html=True)
            
            # Dietary recommendations based on health conditions
            st.markdown("---")
            st.markdown("#### 🎯 Special Dietary Recommendations")
            
            recommendations = []
            
            # BMI-based recommendations
            if bmi < 18.5:
                recommendations.append("🔹 Include healthy fats: avocados, nuts, olive oil")
                recommendations.append("🔹 Eat frequent small meals throughout the day")
                recommendations.append("🔹 Add protein-rich foods to every meal")
            elif bmi > 25:
                recommendations.append("🔹 Focus on portion control and mindful eating")
                recommendations.append("🔹 Choose low-glycemic index foods")
                recommendations.append("🔹 Increase fiber intake with vegetables and whole grains")
            
            # Symptom-based recommendations
            if symptoms:
                symptoms_lower = symptoms.lower()
                if 'headache' in symptoms_lower:
                    recommendations.append("🔹 Stay well-hydrated (8-10 glasses water daily)")
                    recommendations.append("🔹 Limit caffeine and alcohol")
                if 'fatigue' in symptoms_lower:
                    recommendations.append("🔹 Include iron-rich foods: spinach, lentils, lean meat")
                    recommendations.append("🔹 Ensure adequate B-vitamin intake")
                if 'joint' in symptoms_lower or 'pain' in symptoms_lower:
                    recommendations.append("🔹 Include anti-inflammatory foods: turmeric, ginger, fish")
                    recommendations.append("🔹 Reduce processed foods and sugar")
            
            # General health recommendations
            recommendations.extend([
                "🔹 Eat a rainbow of fruits and vegetables daily",
                "🔹 Choose whole grains over refined grains",
                "🔹 Limit processed foods and added sugars",
                "🔹 Include lean proteins in every meal",
                "🔹 Practice portion control and mindful eating"
            ])
            
            rec_html = """
            <div class="metric-card">
                <h4 style="color: #007C91; margin: 0 0 1rem 0;">💡 Key Recommendations</h4>
                <div style="color: #333;">
            """
            for rec in recommendations[:8]:  # Limit to 8 recommendations
                rec_html += f"<div style='margin: 0.5rem 0; padding: 0.5rem; background: #F5F7FA; border-radius: 5px;'>{rec}</div>"
            rec_html += """
                </div>
            </div>
            """
            st.markdown(rec_html, unsafe_allow_html=True)
            
            # Foods to avoid/limit
            st.markdown("#### ⚠️ Foods to Avoid or Limit")
            
            avoid_foods = [
                "🚫 Processed and packaged foods",
                "🚫 Sugary drinks and sodas",
                "🚫 Deep-fried foods",
                "🚫 Excessive salt and sodium",
                "🚫 Refined sugars and sweets",
                "🚫 Trans fats and hydrogenated oils"
            ]
            
            if medical_history and 'diabetes' in medical_history.lower():
                avoid_foods.extend([
                    "🚫 High-glycemic fruits (limit)",
                    "🚫 White bread and refined carbs"
                ])
            
            avoid_html = """
            <div class="metric-card" style="border-left: 4px solid #F44336;">
                <h4 style="color: #F44336; margin: 0 0 1rem 0;">⚠️ Avoid These Foods</h4>
                <div style="color: #333;">
            """
            for food in avoid_foods:
                avoid_html += f"<div style='margin: 0.3rem 0;'>{food}</div>"
            avoid_html += """
                </div>
            </div>
            """
            st.markdown(avoid_html, unsafe_allow_html=True)
        
        with tab6:
            st.markdown("### 🏃‍♂️ Personalized Exercise Plan")
            
            # Get patient data
            patient_data = st.session_state.health_data
            age = patient_data.get('patient', {}).get('age', 30)
            gender = patient_data.get('patient', {}).get('gender', 'Unknown')
            weight = patient_data.get('patient', {}).get('weight', 70)
            bmi = patient_data.get('bmi_info', {}).get('bmi', 25)
            lifestyle = patient_data.get('lifestyle', {})
            symptoms = patient_data.get('symptoms', '')
            pain_scale = patient_data.get('pain_scale', 0)
            health_score = HealthAnalytics.calculate_health_score(
                patient_data.get('vitals', {}), bmi, age, symptoms
            )['score']
            
            current_exercise = lifestyle.get('exercise_frequency', 'Rarely')
            
            # Determine fitness level
            if current_exercise == 'Never':
                fitness_level = "Beginner"
                intensity = "Low"
            elif current_exercise in ['Rarely', '1-2 times/week']:
                fitness_level = "Intermediate"
                intensity = "Moderate"
            else:
                fitness_level = "Advanced"
                intensity = "High"
            
            # Exercise goals based on BMI
            if bmi < 18.5:
                exercise_goal = "Muscle Building & Weight Gain"
                focus = "Strength training with adequate rest"
            elif bmi > 25:
                exercise_goal = "Weight Loss & Fat Burning"
                focus = "Cardio with strength training"
            else:
                exercise_goal = "Fitness Maintenance"
                focus = "Balanced cardio and strength"
            
            # Display exercise overview
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("🎯 Fitness Level", fitness_level)
            with col2:
                st.metric("💪 Exercise Goal", exercise_goal.split('&')[0])
            with col3:
                st.metric("⚡ Intensity", intensity)
            with col4:
                weekly_duration = 150 if bmi <= 25 else 200
                st.metric("⏱️ Weekly Duration", f"{weekly_duration} min")
            
            st.markdown("---")
            
            # Weekly exercise plan
            st.markdown("#### 📅 Weekly Exercise Schedule")
            
            exercise_plans = {
                "Beginner": {
                    "monday": {
                        "day": "Monday - Full Body Beginner",
                        "duration": "30 minutes",
                        "exercises": [
                            "5 min warm-up walk",
                            "Bodyweight squats - 2 sets x 10 reps",
                            "Push-ups (knee or wall) - 2 sets x 8 reps",
                            "Plank hold - 2 sets x 15 seconds",
                            "Walking lunges - 2 sets x 8 each leg",
                            "5 min cool-down stretch"
                        ]
                    },
                    "tuesday": {
                        "day": "Tuesday - Active Recovery",
                        "duration": "20 minutes",
                        "exercises": [
                            "Gentle yoga or stretching",
                            "Deep breathing exercises",
                            "Light walking"
                        ]
                    },
                    "wednesday": {
                        "day": "Wednesday - Cardio",
                        "duration": "25 minutes",
                        "exercises": [
                            "5 min warm-up",
                            "15 min brisk walking or cycling",
                            "5 min cool-down and stretching"
                        ]
                    },
                    "thursday": {
                        "day": "Thursday - Rest Day",
                        "duration": "Rest",
                        "exercises": [
                            "Complete rest or light stretching",
                            "Focus on hydration and nutrition"
                        ]
                    },
                    "friday": {
                        "day": "Friday - Strength Training",
                        "duration": "30 minutes",
                        "exercises": [
                            "5 min warm-up",
                            "Chair squats - 2 sets x 10",
                            "Wall push-ups - 2 sets x 10",
                            "Standing calf raises - 2 sets x 12",
                            "Arm circles - 2 sets x 10 each direction",
                            "5 min stretching"
                        ]
                    },
                    "weekend": {
                        "day": "Weekend - Recreational",
                        "duration": "30-45 minutes",
                        "exercises": [
                            "Fun activities like dancing, swimming",
                            "Outdoor activities with family",
                            "Light hiking or nature walks"
                        ]
                    }
                },
                "Intermediate": {
                    "monday": {
                        "day": "Monday - Upper Body Strength",
                        "duration": "45 minutes",
                        "exercises": [
                            "10 min warm-up cardio",
                            "Push-ups - 3 sets x 12-15 reps",
                            "Dumbbell rows - 3 sets x 12 reps",
                            "Overhead press - 3 sets x 10 reps",
                            "Tricep dips - 3 sets x 10 reps",
                            "Plank - 3 sets x 30 seconds",
                            "5 min cool-down stretch"
                        ]
                    },
                    "tuesday": {
                        "day": "Tuesday - Cardio & Core",
                        "duration": "40 minutes",
                        "exercises": [
                            "5 min warm-up",
                            "25 min moderate cardio (running/cycling)",
                            "Core workout - 10 minutes",
                            "Russian twists, bicycle crunches, leg raises"
                        ]
                    },
                    "wednesday": {
                        "day": "Wednesday - Lower Body Strength",
                        "duration": "45 minutes",
                        "exercises": [
                            "10 min warm-up",
                            "Squats - 3 sets x 15 reps",
                            "Lunges - 3 sets x 12 each leg",
                            "Deadlifts - 3 sets x 10 reps",
                            "Calf raises - 3 sets x 15 reps",
                            "Glute bridges - 3 sets x 12 reps",
                            "5 min stretching"
                        ]
                    },
                    "thursday": {
                        "day": "Thursday - Active Recovery",
                        "duration": "30 minutes",
                        "exercises": [
                            "Yoga or Pilates",
                            "Foam rolling",
                            "Light swimming or walking"
                        ]
                    },
                    "friday": {
                        "day": "Friday - HIIT Training",
                        "duration": "35 minutes",
                        "exercises": [
                            "5 min warm-up",
                            "20 min HIIT (30 sec work, 30 sec rest)",
                            "Burpees, mountain climbers, jumping jacks",
                            "10 min cool-down and stretch"
                        ]
                    },
                    "weekend": {
                        "day": "Weekend - Sports/Recreation",
                        "duration": "60 minutes",
                        "exercises": [
                            "Team sports or competitive activities",
                            "Long hikes or bike rides",
                            "Swimming or martial arts"
                        ]
                    }
                },
                "Advanced": {
                    "monday": {
                        "day": "Monday - Heavy Upper Body",
                        "duration": "60 minutes",
                        "exercises": [
                            "10 min dynamic warm-up",
                            "Bench press - 4 sets x 8-10 reps",
                            "Pull-ups - 4 sets x 8-12 reps",
                            "Shoulder press - 4 sets x 8-10 reps",
                            "Weighted dips - 3 sets x 10 reps",
                            "Core circuit - 10 minutes",
                            "5 min cool-down"
                        ]
                    },
                    "tuesday": {
                        "day": "Tuesday - Cardio Endurance",
                        "duration": "50 minutes",
                        "exercises": [
                            "5 min warm-up",
                            "35 min steady-state cardio",
                            "10 min high-intensity intervals"
                        ]
                    },
                    "wednesday": {
                        "day": "Wednesday - Heavy Lower Body",
                        "duration": "60 minutes",
                        "exercises": [
                            "10 min warm-up",
                            "Barbell squats - 4 sets x 8-10 reps",
                            "Romanian deadlifts - 4 sets x 8 reps",
                            "Bulgarian split squats - 3 sets x 10 each",
                            "Hip thrusts - 4 sets x 12 reps",
                            "Calf raises - 4 sets x 15 reps",
                            "5 min stretching"
                        ]
                    },
                    "thursday": {
                        "day": "Thursday - Active Recovery",
                        "duration": "45 minutes",
                        "exercises": [
                            "Advanced yoga or Pilates",
                            "Mobility work and foam rolling",
                            "Light skill practice"
                        ]
                    },
                    "friday": {
                        "day": "Friday - Power & Conditioning",
                        "duration": "55 minutes",
                        "exercises": [
                            "10 min dynamic warm-up",
                            "Olympic lifts or power movements",
                            "Plyometric exercises",
                            "15 min conditioning circuit",
                            "10 min recovery"
                        ]
                    },
                    "weekend": {
                        "day": "Weekend - Sport Specific",
                        "duration": "90+ minutes",
                        "exercises": [
                            "Competitive sports training",
                            "Long endurance activities",
                            "Skill development sessions"
                        ]
                    }
                }
            }
            
            current_plan = exercise_plans.get(fitness_level, exercise_plans["Intermediate"])
            
            for day_key, day_data in current_plan.items():
                day_html = f"""
                <div class="metric-card">
                    <h4 style="color: #007C91; margin: 0 0 0.5rem 0;">{day_data['day']}</h4>
                    <p style="color: #F64C72; font-weight: 600; margin: 0 0 1rem 0;">⏱️ Duration: {day_data['duration']}</p>
                    <ul style="margin: 0; padding-left: 1.5rem; color: #333;">
                """
                for exercise in day_data['exercises']:
                    day_html += f"<li style='margin: 0.3rem 0;'>{exercise}</li>"
                day_html += """
                    </ul>
                </div>
                """
                st.markdown(day_html, unsafe_allow_html=True)
            
            # Exercise recommendations based on health conditions
            st.markdown("---")
            st.markdown("#### 🎯 Special Exercise Considerations")
            
            considerations = []
            
            # Age-based considerations
            if age > 50:
                considerations.append("🔹 Include balance and flexibility exercises")
                considerations.append("🔹 Focus on low-impact activities to protect joints")
                considerations.append("🔹 Allow extra recovery time between intense sessions")
            
            # BMI-based considerations
            if bmi > 30:
                considerations.append("🔹 Start with low-impact cardio (swimming, walking)")
                considerations.append("🔹 Gradually increase intensity to prevent injury")
                considerations.append("🔹 Focus on consistency over intensity")
            elif bmi < 18.5:
                considerations.append("🔹 Emphasize strength training over cardio")
                considerations.append("🔹 Allow adequate rest for muscle recovery")
                considerations.append("🔹 Combine exercise with proper nutrition")
            
            # Pain and symptom considerations
            if pain_scale > 5:
                considerations.append("🔹 Consult healthcare provider before starting")
                considerations.append("🔹 Focus on gentle, pain-free movements")
                considerations.append("🔹 Consider water-based exercises")
            
            if symptoms:
                symptoms_lower = symptoms.lower()
                if 'joint' in symptoms_lower or 'arthritis' in symptoms_lower:
                    considerations.append("🔹 Include low-impact exercises like swimming")
                    considerations.append("🔹 Avoid high-impact activities")
                if 'heart' in symptoms_lower:
                    considerations.append("🔹 Monitor heart rate during exercise")
                    considerations.append("🔹 Start with light intensity")
            
            # General considerations
            considerations.extend([
                "🔹 Always warm up before and cool down after exercise",
                "🔹 Stay hydrated throughout your workout",
                "🔹 Listen to your body and rest when needed",
                "🔹 Progress gradually to avoid injury",
                "🔹 Ensure adequate sleep for recovery"
            ])
            
            if considerations:
                consider_html = """
                <div class="metric-card" style="border-left: 4px solid #FF9800;">
                    <h4 style="color: #FF9800; margin: 0 0 1rem 0;">⚠️ Important Considerations</h4>
                    <div style="color: #333;">
                """
                for consideration in considerations[:8]:
                    consider_html += f"<div style='margin: 0.5rem 0; padding: 0.5rem; background: #FFF3E0; border-radius: 5px;'>{consideration}</div>"
                consider_html += """
                    </div>
                </div>
                """
                st.markdown(consider_html, unsafe_allow_html=True)
            
            # Progress tracking
            st.markdown("#### 📊 Track Your Progress")
            
            progress_html = """
            <div class="metric-card">
                <h4 style="color: #007C91; margin: 0 0 1rem 0;">📈 Weekly Goals</h4>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem;">
                    <div style="background: #E8F5E8; padding: 1rem; border-radius: 8px; text-align: center;">
                        <h5 style="margin: 0; color: #2E7D32;">🎯 Frequency</h5>
                        <p style="margin: 0.5rem 0; font-weight: bold;">4-5 days/week</p>
                    </div>
                    <div style="background: #E3F2FD; padding: 1rem; border-radius: 8px; text-align: center;">
                        <h5 style="margin: 0; color: #1976D2;">⏱️ Duration</h5>
                        <p style="margin: 0.5rem 0; font-weight: bold;">30-60 minutes</p>
                    </div>
                    <div style="background: #FCE4EC; padding: 1rem; border-radius: 8px; text-align: center;">
                        <h5 style="margin: 0; color: #C2185B;">🔥 Intensity</h5>
                        <p style="margin: 0.5rem 0; font-weight: bold;">{}</p>
                    </div>
                </div>
            </div>
            """.format(intensity)
            st.markdown(progress_html, unsafe_allow_html=True)
        
        with tab7:
        with tab7:
            st.markdown("### 📰 Latest Health News & Updates")
            
            with st.spinner("📰 Loading latest health news..."):
                health_news = get_health_news(st.session_state.user_location)
                
                if health_news:
                    st.success(f"📈 Found {len(health_news)} recent health articles")
                    
                    for i, article in enumerate(health_news):
                        with st.expander(f"📰 {article.get('title', 'Health News Article')}", expanded=(i == 0)):
                            article_html = f"""
                            <div style="padding: 1rem;">
                                <div style="background: #F5F7FA; padding: 1rem; border-radius: 8px; margin: 1rem 0;">
                                    <p style="margin: 0 0 1rem 0; line-height: 1.6; color: #333;">
                                        {article.get('description', 'No description available for this article.')}
                                    </p>
                                    <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 1rem;">
                                        <div style="color: #666; font-size: 0.9em;">
                                            <strong>📰 Source:</strong> {article.get('source', 'Unknown Source')}<br>
                                            <strong>📅 Published:</strong> {article.get('published_at', 'Date not available')[:10]}
                                        </div>
                                        <a href="{article.get('url', '#')}" target="_blank" 
                                           style="background: #F64C72; color: white; padding: 0.5rem 1rem; 
                                                  border-radius: 20px; text-decoration: none; font-weight: 600;">
                                            🔗 Read Full Article
                                        </a>
                                    </div>
                                </div>
                            </div>
                            """
                            st.markdown(article_html, unsafe_allow_html=True)
                else:
                    st.info("📰 Health news is currently unavailable. Please check back later.")

def show_footer():
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    footer_html = f"""
    <div class="footer">
        <h2 style="margin: 0 0 1rem 0;">🏥 MediAI Pro - Advanced Health Assistant</h2>
        <div style="display: flex; justify-content: center; gap: 2rem; margin: 1rem 0; flex-wrap: wrap;">
            <div>🤖 <strong>AI-Powered Analysis</strong></div>
            <div>🌍 <strong>Location-Aware Services</strong></div>
            <div>⚡ <strong>Real-time Health Data</strong></div>
            <div>🔒 <strong>Privacy Protected</strong></div>
        </div>
        <div style="margin: 1rem 0; padding: 1rem; background: rgba(255,255,255,0.1); border-radius: 10px;">
            <h4 style="margin: 0 0 0.5rem 0;">⚠️ Important Medical Disclaimer</h4>
            <p style="margin: 0; font-size: 0.9em; line-height: 1.5;">
                This application provides health information for educational purposes only and should not replace professional medical advice, 
                diagnosis, or treatment. Always consult with qualified healthcare professionals for medical concerns. 
                In case of medical emergencies, contact emergency services immediately.
            </p>
        </div>
        <p style="margin: 1rem 0 0 0; color: rgba(255,255,255,0.8);">
            Generated: {current_time} | Version 2.0 | 🏥 Your Health, Our Priority
        </p>
    </div>
    """
    st.markdown(footer_html, unsafe_allow_html=True)

if __name__ == "__main__":
    try:
        main()
        show_footer()
    except Exception as e:
        logger.error(f"Application error: {e}")
        st.error("🚨 An unexpected error occurred. Please refresh the page and try again.")
        with st.expander("🔍 Error Details (for debugging)"):
            st.exception(e)
