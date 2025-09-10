from tkinter import *
from tkinter import ttk, messagebox
import requests
from datetime import datetime, timedelta
from PIL import Image, ImageTk
from io import BytesIO
import urllib.request
import json
import os
import threading
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np

class WeatherApp:
    def __init__(self):
        self.api_key = "0d27bc58cf01f42c5f252b8be54f115f"  
        self.favorites_file = "weather_favorites.json"
        self.favorites = self.load_favorites()
        self.setup_ui()
        
    def setup_ui(self):
        self.win = Tk()
        self.win.title("🌤 Advanced Weather App")
        self.win.geometry("800x900")
        self.win.config(bg="#E8F6F3")
        
        # Configure styles
        style = ttk.Style()
        style.configure("TButton", font=("Segoe UI", 12), padding=6)
        style.configure("Title.TLabel", font=("Segoe UI", 16, "bold"))
        
        self.create_header()
        self.create_search_section()
        self.create_tabs()
        self.auto_detect_location()

    def create_header(self):
        header_frame = Frame(self.win, bg="#1ABC9C", height=80)
        header_frame.pack(fill=X)
        header_frame.pack_propagate(False)
        
        title = Label(header_frame, text="🌍Weather Forecast", 
                     font=("Segoe UI", 24, "bold"), bg="#1ABC9C", fg="white")
        title.pack(expand=True)
        
        # Current time (updates every second)
        self.time_label = Label(header_frame, font=("Segoe UI", 12), bg="#1ABC9C", fg="white")
        self.time_label.pack()
        self.update_time()

    def create_search_section(self):
        search_frame = Frame(self.win, bg="#E8F6F3", pady=15)
        search_frame.pack(fill=X)
        
        # City input with autocomplete
        input_frame = Frame(search_frame, bg="#E8F6F3")
        input_frame.pack()
        
        # Location input methods
        location_methods = Frame(input_frame, bg="#E8F6F3")
        location_methods.pack()
        
        # City name input
        city_frame = Frame(location_methods, bg="#E8F6F3")
        city_frame.pack(pady=5)
        
        Label(city_frame, text="🏙️ City/Location:", font=("Segoe UI", 12), bg="#E8F6F3").pack(side=LEFT, padx=5)
        
        self.city_name = StringVar()
        self.city_entry = ttk.Combobox(city_frame, textvariable=self.city_name, 
                                      font=("Segoe UI", 11), width=30)
        self.city_entry['values'] = self.get_city_suggestions()
        self.city_entry.pack(side=LEFT, padx=5)
        
        # Coordinates input
        coord_frame = Frame(location_methods, bg="#E8F6F3")
        coord_frame.pack(pady=5)
        
        Label(coord_frame, text="🗺️ Coordinates:", font=("Segoe UI", 12), bg="#E8F6F3").pack(side=LEFT, padx=5)
        
        self.latitude = StringVar()
        self.longitude = StringVar()
        
        lat_entry = ttk.Entry(coord_frame, textvariable=self.latitude, font=("Segoe UI", 11), width=12)
        lat_entry.pack(side=LEFT, padx=2)
        lat_entry.insert(0, "Latitude")
        lat_entry.bind("<FocusIn>", lambda e: self.clear_placeholder(e, "Latitude"))
        lat_entry.bind("<FocusOut>", lambda e: self.restore_placeholder(e, "Latitude"))
        
        Label(coord_frame, text=",", font=("Segoe UI", 12), bg="#E8F6F3").pack(side=LEFT)
        
        lon_entry = ttk.Entry(coord_frame, textvariable=self.longitude, font=("Segoe UI", 11), width=12)
        lon_entry.pack(side=LEFT, padx=2)
        lon_entry.insert(0, "Longitude")
        lon_entry.bind("<FocusIn>", lambda e: self.clear_placeholder(e, "Longitude"))
        lon_entry.bind("<FocusOut>", lambda e: self.restore_placeholder(e, "Longitude"))
        
        # Buttons
        button_frame = Frame(input_frame, bg="#E8F6F3")
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, text="🔍 Search by Name", command=self.search_weather).pack(side=LEFT, padx=5)
        ttk.Button(button_frame, text="📍 Search by Coordinates", command=self.search_by_coordinates).pack(side=LEFT, padx=5)
        ttk.Button(button_frame, text="🌐 Auto Detect", command=self.auto_detect_location).pack(side=LEFT, padx=5)
        ttk.Button(button_frame, text="⭐ Add to Favorites", command=self.add_to_favorites).pack(side=LEFT, padx=5)
        
        # Favorites dropdown
        if self.favorites:
            fav_frame = Frame(search_frame, bg="#E8F6F3")
            fav_frame.pack(pady=10)
            Label(fav_frame, text="Favorites:", font=("Segoe UI", 12), bg="#E8F6F3").pack(side=LEFT, padx=5)
            
            self.fav_var = StringVar()
            fav_combo = ttk.Combobox(fav_frame, textvariable=self.fav_var, 
                                   values=list(self.favorites.keys()), width=20)
            fav_combo.pack(side=LEFT, padx=5)
            fav_combo.bind('<<ComboboxSelected>>', self.load_favorite)

    def create_tabs(self):
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.win)
        self.notebook.pack(fill=BOTH, expand=True, padx=10, pady=10)
        
        # Current Weather Tab
        self.current_frame = Frame(self.notebook, bg="#E8F6F3")
        self.notebook.add(self.current_frame, text="Current Weather")
        self.create_current_weather_tab()
        
        # 5-Day Forecast Tab
        self.forecast_frame = Frame(self.notebook, bg="#E8F6F3")
        self.notebook.add(self.forecast_frame, text="5-Day Forecast")
        self.create_forecast_tab()
        
        # Charts Tab
        self.charts_frame = Frame(self.notebook, bg="#E8F6F3")
        self.notebook.add(self.charts_frame, text="Weather Charts")
        self.create_charts_tab()
        
        # Additional Info Tab
        self.info_frame = Frame(self.notebook, bg="#E8F6F3")
        self.notebook.add(self.info_frame, text="Additional Info")
        self.create_additional_info_tab()

    def create_current_weather_tab(self):
        # Weather icon
        self.icon_label = Label(self.current_frame, bg="#E8F6F3")
        self.icon_label.pack(pady=10)
        
        # Main weather info
        main_info_frame = Frame(self.current_frame, bg="#E8F6F3")
        main_info_frame.pack(pady=10)
        
        # Temperature display (large)
        self.temp_main = Label(main_info_frame, font=("Segoe UI", 36, "bold"), 
                              bg="#E8F6F3", fg="#E74C3C")
        self.temp_main.pack()
        
        self.weather_desc = Label(main_info_frame, font=("Segoe UI", 16), 
                                 bg="#E8F6F3", fg="#34495E")
        self.weather_desc.pack()
        
        # Weather details grid
        details_frame = Frame(self.current_frame, bg="#E8F6F3")
        details_frame.pack(pady=20)
        
        # Create StringVars for dynamic updates
        self.weather_vars = {
            'feels_like': StringVar(),
            'humidity': StringVar(),
            'pressure': StringVar(),
            'wind_speed': StringVar(),
            'visibility': StringVar(),
            'uv_index': StringVar()
        }
        
        # Create info cards
        self.create_info_cards(details_frame)

    def create_info_cards(self, parent):
        cards_frame = Frame(parent, bg="#E8F6F3")
        cards_frame.pack()
        
        card_data = [
            ("Feels Like", self.weather_vars['feels_like'], "🌡️"),
            ("Humidity", self.weather_vars['humidity'], "💧"),
            ("Pressure", self.weather_vars['pressure'], "📊"),
            ("Wind Speed", self.weather_vars['wind_speed'], "💨"),
            ("Visibility", self.weather_vars['visibility'], "👁️"),
            ("UV Index", self.weather_vars['uv_index'], "☀️")
        ]
        
        for i, (label, var, emoji) in enumerate(card_data):
            row = i // 3
            col = i % 3
            
            card = Frame(cards_frame, bg="white", relief=RAISED, bd=1)
            card.grid(row=row, column=col, padx=10, pady=10, sticky="ew")
            
            Label(card, text=f"{emoji} {label}", font=("Segoe UI", 12, "bold"), 
                 bg="white", fg="#2C3E50").pack(pady=5)
            Label(card, textvariable=var, font=("Segoe UI", 14), 
                 bg="white", fg="#E74C3C").pack(pady=5)

    def create_forecast_tab(self):
        # Header
        Label(self.forecast_frame, text="5-Day Weather Forecast", 
              font=("Segoe UI", 18, "bold"), bg="#E8F6F3").pack(pady=10)
        
        # Scrollable frame for forecast
        canvas = Canvas(self.forecast_frame, bg="#E8F6F3")
        scrollbar = ttk.Scrollbar(self.forecast_frame, orient="vertical", command=canvas.yview)
        self.forecast_content = Frame(canvas, bg="#E8F6F3")
        
        self.forecast_content.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.forecast_content, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def create_charts_tab(self):
        Label(self.charts_frame, text="Weather Trends", 
              font=("Segoe UI", 18, "bold"), bg="#E8F6F3").pack(pady=10)
        
        # Placeholder for matplotlib chart
        self.chart_frame = Frame(self.charts_frame, bg="#E8F6F3")
        self.chart_frame.pack(fill=BOTH, expand=True, padx=20, pady=20)

    def create_additional_info_tab(self):
        Label(self.info_frame, text="Additional Weather Information", 
              font=("Segoe UI", 18, "bold"), bg="#E8F6F3").pack(pady=10)
        
        # Sunrise/Sunset info
        sun_frame = LabelFrame(self.info_frame, text="☀️ Sun Information", 
                              font=("Segoe UI", 14, "bold"), bg="#E8F6F3")
        sun_frame.pack(fill=X, padx=20, pady=10)
        
        self.sunrise_var = StringVar()
        self.sunset_var = StringVar()
        
        Label(sun_frame, text="Sunrise:", font=("Segoe UI", 12), bg="#E8F6F3").grid(row=0, column=0, sticky=W, padx=10, pady=5)
        Label(sun_frame, textvariable=self.sunrise_var, font=("Segoe UI", 12), bg="#E8F6F3").grid(row=0, column=1, sticky=W, padx=10, pady=5)
        
        Label(sun_frame, text="Sunset:", font=("Segoe UI", 12), bg="#E8F6F3").grid(row=1, column=0, sticky=W, padx=10, pady=5)
        Label(sun_frame, textvariable=self.sunset_var, font=("Segoe UI", 12), bg="#E8F6F3").grid(row=1, column=1, sticky=W, padx=10, pady=5)

    def get_weather(self, location, is_coordinates=False):
        """Enhanced weather data fetching with global location support"""
        try:
            # Build URL based on search type
            if is_coordinates:
                lat, lon = location
                url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={self.api_key}&units=metric"
                forecast_url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={self.api_key}&units=metric"
            else:
                # Enhanced city search with country code support
                url = f"https://api.openweathermap.org/data/2.5/weather?q={location}&appid={self.api_key}&units=metric"
                forecast_url = f"https://api.openweathermap.org/data/2.5/forecast?q={location}&appid={self.api_key}&units=metric"
            
            # Current weather API call
            response = requests.get(url, timeout=10)
            data = response.json()
            
            if data.get("cod") != 200:
                # Try alternative search methods
                if not is_coordinates:
                    self.try_alternative_search(location)
                    return
                else:
                    raise ValueError(data.get("message", "Location not found"))
            
            self.current_location_data = data  # Store for forecast calls
            self.update_current_weather(data)
            self.get_forecast_by_url(forecast_url)  # Get 5-day forecast
            
        except requests.exceptions.Timeout:
            messagebox.showerror("Error", "Request timed out. Please check your internet connection.")
        except requests.exceptions.RequestException:
            messagebox.showerror("Error", "Network error. Please check your internet connection.")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")

    def try_alternative_search(self, location):
        """Try alternative search methods for global locations"""
        try:
            # Method 1: Try with geocoding API first
            geo_url = f"https://api.openweathermap.org/geo/1.0/direct?q={location}&limit=5&appid={self.api_key}"
            geo_response = requests.get(geo_url, timeout=10)
            geo_data = geo_response.json()
            
            if geo_data:
                # Use first result
                lat = geo_data[0]["lat"]
                lon = geo_data[0]["lon"]
                country = geo_data[0].get("country", "")
                state = geo_data[0].get("state", "")
                
                # Show location confirmation
                full_name = f"{geo_data[0]['name']}"
                if state:
                    full_name += f", {state}"
                if country:
                    full_name += f", {country}"
                
                result = messagebox.askyesno("Location Found", 
                    f"Found: {full_name}\nDo you want to get weather for this location?")
                
                if result:
                    self.get_weather((lat, lon), is_coordinates=True)
                    return
            
            # Method 2: Try common variations
            variations = self.get_location_variations(location)
            for variation in variations:
                try:
                    url = f"https://api.openweathermap.org/data/2.5/weather?q={variation}&appid={self.api_key}&units=metric"
                    response = requests.get(url, timeout=5)
                    data = response.json()
                    
                    if data.get("cod") == 200:
                        self.current_location_data = data
                        self.update_current_weather(data)
                        forecast_url = f"https://api.openweathermap.org/data/2.5/forecast?q={variation}&appid={self.api_key}&units=metric"
                        self.get_forecast_by_url(forecast_url)
                        return
                except:
                    continue
            
            # If all methods fail
            messagebox.showerror("Location Not Found", 
                f"Could not find weather data for '{location}'.\n\n"
                "Tips:\n"
                "• Try including country code (e.g., 'Paris, FR')\n"
                "• Use full city names\n"
                "• Try coordinates (lat, lon)\n"
                "• Check spelling")
                
        except Exception as e:
            messagebox.showerror("Search Error", f"Error during location search: {str(e)}")

    def get_location_variations(self, location):
        """Generate common variations of location names"""
        variations = []
        
        # Basic variations
        variations.append(location)
        variations.append(location.title())
        variations.append(location.lower())
        variations.append(location.upper())
        
        # Add common country codes if not present
        if "," not in location:
            common_countries = ["US", "GB", "CA", "AU", "DE", "FR", "IT", "ES", "IN", "CN", "JP", "BR"]
            for country in common_countries:
                variations.append(f"{location},{country}")
                variations.append(f"{location}, {country}")
        
        return variations

    def update_current_weather(self, data):
        """Update current weather display with enhanced location info"""
        try:
            # Basic weather info
            main_weather = data["weather"][0]["main"]
            description = data["weather"][0]["description"].title()
            temp = round(data["main"]["temp"])
            feels_like = round(data["main"]["feels_like"])
            pressure = data["main"]["pressure"]
            humidity = data["main"]["humidity"]
            wind = data["wind"]["speed"]
            visibility = data.get("visibility", 0) / 1000  # Convert to km
            
            # Enhanced location info
            city_name = data["name"]
            country = data["sys"]["country"]
            coordinates = f"{data['coord']['lat']:.2f}, {data['coord']['lon']:.2f}"
            
            # Update main display with location
            self.temp_main.config(text=f"{temp}°C")
            location_text = f"{city_name}, {country}\n{main_weather} - {description}\n📍 {coordinates}"
            self.weather_desc.config(text=location_text)
            
            # Update detail cards
            self.weather_vars['feels_like'].set(f"{feels_like}°C")
            self.weather_vars['humidity'].set(f"{humidity}%")
            self.weather_vars['pressure'].set(f"{pressure} hPa")
            self.weather_vars['wind_speed'].set(f"{wind} m/s")
            self.weather_vars['visibility'].set(f"{visibility:.1f} km")
            
            # Get additional weather data
            self.get_additional_weather_data(data['coord']['lat'], data['coord']['lon'])
            
            # Update weather icon
            icon_code = data["weather"][0]["icon"]
            self.update_weather_icon(icon_code)
            
            # Update sun info
            sunrise = datetime.fromtimestamp(data["sys"]["sunrise"]).strftime("%H:%M")
            sunset = datetime.fromtimestamp(data["sys"]["sunset"]).strftime("%H:%M")
            self.sunrise_var.set(sunrise)
            self.sunset_var.set(sunset)
            
            # Update city entry with proper format
            self.city_name.set(f"{city_name}, {country}")
            
        except Exception as e:
            print(f"Error updating weather display: {e}")

    def get_additional_weather_data(self, lat, lon):
        """Get additional weather data using coordinates"""
        try:
            # UV Index (requires separate API call)
            uvi_url = f"https://api.openweathermap.org/data/2.5/uvi?lat={lat}&lon={lon}&appid={self.api_key}"
            uvi_response = requests.get(uvi_url, timeout=5)
            uvi_data = uvi_response.json()
            
            if 'value' in uvi_data:
                uv_value = round(uvi_data['value'], 1)
                uv_level = self.get_uv_level(uv_value)
                self.weather_vars['uv_index'].set(f"{uv_value} ({uv_level})")
            else:
                self.weather_vars['uv_index'].set("N/A")
                
        except Exception as e:
            self.weather_vars['uv_index'].set("N/A")
            print(f"Error getting additional weather data: {e}")

    def get_uv_level(self, uv_value):
        """Convert UV index to descriptive level"""
        if uv_value <= 2:
            return "Low"
        elif uv_value <= 5:
            return "Moderate"
        elif uv_value <= 7:
            return "High"
        elif uv_value <= 10:
            return "Very High"
        else:
            return "Extreme"

    def update_weather_icon(self, icon_code):
        """Update weather icon with better error handling"""
        try:
            icon_url = f"http://openweathermap.org/img/wn/{icon_code}@2x.png"
            image_byt = urllib.request.urlopen(icon_url, timeout=10).read()
            image_buf = BytesIO(image_byt)
            image = Image.open(image_buf)
            image = image.resize((100, 100), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(image)
            self.icon_label.config(image=photo)
            self.icon_label.image = photo
        except Exception as e:
            print(f"Error loading weather icon: {e}")
            self.icon_label.config(image='', text="🌤️")

    def get_forecast_by_url(self, forecast_url):
        """Get forecast data using provided URL"""
        try:
            response = requests.get(forecast_url, timeout=10)
            data = response.json()
            
            if data.get("cod") != "200":
                print("Forecast data not available")
                return
            
            self.update_forecast_display(data)
            self.create_weather_chart(data)
            
        except Exception as e:
            print(f"Error getting forecast: {e}")

    def search_by_coordinates(self):
        """Search weather using latitude and longitude"""
        try:
            lat_str = self.latitude.get().strip()
            lon_str = self.longitude.get().strip()
            
            # Validate coordinates
            if lat_str in ["", "Latitude"] or lon_str in ["", "Longitude"]:
                messagebox.showwarning("Warning", "Please enter both latitude and longitude")
                return
            
            lat = float(lat_str)
            lon = float(lon_str)
            
            # Validate coordinate ranges
            if not (-90 <= lat <= 90):
                messagebox.showerror("Error", "Latitude must be between -90 and 90")
                return
            
            if not (-180 <= lon <= 180):
                messagebox.showerror("Error", "Longitude must be between -180 and 180")
                return
            
            self.get_weather((lat, lon), is_coordinates=True)
            
        except ValueError:
            messagebox.showerror("Error", "Please enter valid numeric coordinates")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")

    def clear_placeholder(self, event, placeholder):
        """Clear placeholder text when entry gets focus"""
        if event.widget.get() == placeholder:
            event.widget.delete(0, END)

    def restore_placeholder(self, event, placeholder):
        """Restore placeholder text when entry loses focus and is empty"""
        if not event.widget.get():
            event.widget.insert(0, placeholder)

    def update_forecast_display(self, data):
        """Update 5-day forecast display"""
        # Clear previous forecast
        for widget in self.forecast_content.winfo_children():
            widget.destroy()
        
        # Group forecasts by day
        daily_forecasts = {}
        for item in data["list"][:40]:  # 5 days * 8 forecasts per day
            date = datetime.fromtimestamp(item["dt"]).date()
            if date not in daily_forecasts:
                daily_forecasts[date] = []
            daily_forecasts[date].append(item)
        
        # Create forecast cards
        for i, (date, forecasts) in enumerate(list(daily_forecasts.items())[:5]):
            day_frame = Frame(self.forecast_content, bg="white", relief=RAISED, bd=2)
            day_frame.pack(fill=X, padx=10, pady=5)
            
            # Day header
            day_name = date.strftime("%A, %B %d")
            Label(day_frame, text=day_name, font=("Segoe UI", 14, "bold"), 
                 bg="white").pack(pady=5)
            
            # Get daily summary
            temps = [f["main"]["temp"] for f in forecasts]
            min_temp = round(min(temps))
            max_temp = round(max(temps))
            
            # Most common weather condition
            conditions = [f["weather"][0]["main"] for f in forecasts]
            main_condition = max(set(conditions), key=conditions.count)
            
            temp_label = Label(day_frame, text=f"{min_temp}°C / {max_temp}°C", 
                             font=("Segoe UI", 12), bg="white")
            temp_label.pack()
            
            condition_label = Label(day_frame, text=main_condition, 
                                  font=("Segoe UI", 10), bg="white", fg="gray")
            condition_label.pack(pady=(0, 5))

    def create_weather_chart(self, data):
        """Create temperature trend chart"""
        try:
            # Clear previous chart
            for widget in self.chart_frame.winfo_children():
                widget.destroy()
            
            # Extract data for chart
            times = []
            temps = []
            
            for item in data["list"][:24]:  # 24 hours
                times.append(datetime.fromtimestamp(item["dt"]).strftime("%H:%M"))
                temps.append(item["main"]["temp"])
            
            # Create matplotlib figure
            fig, ax = plt.subplots(figsize=(10, 4))
            ax.plot(times, temps, marker='o', linewidth=2, markersize=4)
            ax.set_title("24-Hour Temperature Trend")
            ax.set_ylabel("Temperature (°C)")
            ax.grid(True, alpha=0.3)
            plt.xticks(rotation=45)
            plt.tight_layout()
            
            # Embed chart in tkinter
            canvas = FigureCanvasTkAgg(fig, self.chart_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=BOTH, expand=True)
            
        except Exception as e:
            print(f"Error creating chart: {e}")

    def auto_detect_location(self):
        """Auto-detect user location with enhanced global support"""
        def detect():
            try:
                # Get detailed location info
                location = requests.get("https://ipinfo.io", timeout=10).json()
                detected_city = location.get("city", "Delhi")
                country = location.get("country", "IN")
                
                # Try to get coordinates for more accurate weather
                if "loc" in location:
                    lat, lon = location["loc"].split(",")
                    self.latitude.set(lat.strip())
                    self.longitude.set(lon.strip())
                    full_location = f"{detected_city}, {country}"
                    self.city_name.set(full_location)
                    self.get_weather((float(lat), float(lon)), is_coordinates=True)
                else:
                    # Fallback to city name
                    full_location = f"{detected_city}, {country}"
                    self.city_name.set(full_location)
                    self.get_weather(full_location)
                    
            except Exception as e:
                print(f"Auto-detection error: {e}")
                # Ultimate fallback
                self.city_name.set("Delhi, IN")
                self.get_weather("Delhi, IN")
        
        # Run in separate thread to prevent UI blocking
        threading.Thread(target=detect, daemon=True).start()

    def search_weather(self):
        """Search weather for entered city with enhanced global support"""
        location = self.city_name.get().strip()
        if location:
            # Clear coordinate fields when searching by name
            self.latitude.set("Latitude")
            self.longitude.set("Longitude")
            self.get_weather(location)
        else:
            messagebox.showwarning("Warning", "Please enter a city name or coordinates")

    def add_to_favorites(self):
        """Add current city to favorites"""
        city = self.city_name.get().strip()
        if city and city not in self.favorites:
            self.favorites[city] = {"added_date": datetime.now().isoformat()}
            self.save_favorites()
            messagebox.showinfo("Success", f"{city} added to favorites!")
            self.refresh_favorites_dropdown()

    def load_favorite(self, event):
        """Load weather for selected favorite city"""
        selected = self.fav_var.get()
        if selected:
            self.city_name.set(selected)
            self.get_weather(selected)

    def load_favorites(self):
        """Load favorites from file"""
        try:
            if os.path.exists(self.favorites_file):
                with open(self.favorites_file, 'r') as f:
                    return json.load(f)
        except:
            pass
        return {}

    def save_favorites(self):
        """Save favorites to file"""
        try:
            with open(self.favorites_file, 'w') as f:
                json.dump(self.favorites, f)
        except Exception as e:
            print(f"Error saving favorites: {e}")

    def refresh_favorites_dropdown(self):
        """Refresh the favorites dropdown"""
        # This would need to be implemented to update the combobox values
        pass

    def get_city_suggestions(self):
        """Get comprehensive list of global city suggestions"""
        return [
            # Asia
            "Delhi, IN", "Mumbai, IN", "Bangalore, IN", "Chennai, IN", "Kolkata, IN", 
            "Tokyo, JP", "Seoul, KR", "Beijing, CN", "Shanghai, CN", "Bangkok, TH",
            "Singapore, SG", "Hong Kong, HK", "Manila, PH", "Jakarta, ID", "Kuala Lumpur, MY",
            "Dubai, AE", "Riyadh, SA", "Tehran, IR", "Istanbul, TR", "Tel Aviv, IL",
            
            # Europe
            "London, GB", "Paris, FR", "Berlin, DE", "Madrid, ES", "Rome, IT",
            "Amsterdam, NL", "Vienna, AT", "Prague, CZ", "Warsaw, PL", "Stockholm, SE",
            "Oslo, NO", "Copenhagen, DK", "Helsinki, FI", "Brussels, BE", "Zurich, CH",
            "Athens, GR", "Lisbon, PT", "Dublin, IE", "Budapest, HU", "Moscow, RU",
            
            # North America
            "New York, US", "Los Angeles, US", "Chicago, US", "Houston, US", "Phoenix, US",
            "Philadelphia, US", "San Francisco, US", "Miami, US", "Seattle, US", "Boston, US",
            "Toronto, CA", "Vancouver, CA", "Montreal, CA", "Mexico City, MX", "Guadalajara, MX",
            
            # South America
            "São Paulo, BR", "Rio de Janeiro, BR", "Buenos Aires, AR", "Lima, PE", "Bogotá, CO",
            "Santiago, CL", "Caracas, VE", "Quito, EC", "La Paz, BO", "Montevideo, UY",
            
            # Africa
            "Cairo, EG", "Lagos, NG", "Cape Town, ZA", "Johannesburg, ZA", "Nairobi, KE",
            "Casablanca, MA", "Algiers, DZ", "Tunis, TN", "Accra, GH", "Addis Ababa, ET",
            
            # Oceania
            "Sydney, AU", "Melbourne, AU", "Brisbane, AU", "Perth, AU", "Auckland, NZ",
            "Wellington, NZ", "Christchurch, NZ", "Adelaide, AU", "Darwin, AU", "Hobart, AU"
        ]

    def update_time(self):
        """Update current time display"""
        current_time = datetime.now().strftime("%A, %d %B %Y | %I:%M:%S %p")
        self.time_label.config(text=current_time)
        self.win.after(1000, self.update_time)

    def run(self):
        """Start the application"""
        self.win.mainloop()

# Create and run the application
if __name__ == "__main__":
    app = WeatherApp()
    app.run()