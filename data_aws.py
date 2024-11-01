#!/usr/bin/env python3
import requests
import pandas as pd
from datetime import datetime
import os
import sys
import csv  # Import modul csv untuk konstanta quoting

def log_message(message):
    with open('/home/yoga/Documents/script_python_log_ecowitt.txt', 'a', encoding='utf-8') as log_file:
        log_file.write(f"{datetime.now()}: {message}\n")

try:
    current_dir = os.getcwd()
    log_message(f"Current working directory: {current_dir}")

    # Masukkan Application Key, API Key, dan MAC Address Anda di sini
    APPLICATION_KEY = '5EFEDE6355252FB8C1747968208DE504'  # Ganti dengan Application Key Anda
    API_KEY = 'b704a184-2465-48e1-884b-4acb1554dabb'       # Ganti dengan API Key Anda
    MAC_ADDRESS = 'C8:C9:A3:27:AD:40'                      # Ganti dengan MAC address perangkat Anda

    # Endpoint API Ecowitt
    url = 'https://api.ecowitt.net/api/v3/device/real_time'

    # Parameter untuk permintaan API
    params = {
        'application_key': APPLICATION_KEY,
        'api_key': API_KEY,
        'mac': MAC_ADDRESS,
        'call_back': 'all',
        'language': 'en',
        'format': 'json'
    }

    # Logging parameter yang dikirim
    log_message(f"Parameter yang dikirim: {params}")

    # Mengirim permintaan GET ke API
    response = requests.get(url, params=params)
    response.raise_for_status()  # Memeriksa kesalahan HTTP

    # Logging URL permintaan
    log_message(f"URL request: {response.url}")

    data = response.json()

    # Logging data yang diterima
    log_message(f"Data yang diterima dari API: {data}")

    # Memeriksa apakah respons sukses
    if data.get('code') != 0:
        log_message(f"Error dari API: {data.get('msg')}")
        sys.exit(1)

    # Mengambil data observasi
    obs = data['data']

    # Ekstraksi data yang diperlukan
    observation_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Fungsi untuk mengonversi string ke float dengan aman
    def safe_float(value):
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    # Mengambil nilai dan satuan
    temperature_data = obs.get('outdoor', {}).get('temperature', {})
    temperature = safe_float(temperature_data.get('value'))
    temperature_unit = temperature_data.get('unit')

    humidity_data = obs.get('outdoor', {}).get('humidity', {})
    humidity = safe_float(humidity_data.get('value'))
    humidity_unit = humidity_data.get('unit')

    pressure_data = obs.get('pressure', {}).get('relative', {})
    pressure = safe_float(pressure_data.get('value'))
    pressure_unit = pressure_data.get('unit')

    precip_data = obs.get('rainfall', {}).get('rain_rate', {})
    precip_rate = safe_float(precip_data.get('value'))
    precip_unit = precip_data.get('unit')

    wind_dir_data = obs.get('wind', {}).get('wind_direction', {})
    wind_dir = safe_float(wind_dir_data.get('value'))
    wind_dir_unit = wind_dir_data.get('unit')

    wind_speed_data = obs.get('wind', {}).get('wind_speed', {})
    wind_speed = safe_float(wind_speed_data.get('value'))
    wind_speed_unit = wind_speed_data.get('unit')

    solar_data = obs.get('solar_and_uvi', {}).get('solar', {})
    solar_radiation = safe_float(solar_data.get('value'))
    solar_unit = solar_data.get('unit')

    # Logging satuan yang diterima
    log_message(f"Temperature unit: {temperature_unit}")
    log_message(f"Pressure unit: {pressure_unit}")
    log_message(f"Wind speed unit: {wind_speed_unit}")
    log_message(f"Precipitation rate unit: {precip_unit}")

    # Melakukan konversi jika diperlukan
    if temperature is not None and temperature_unit == 'ºF':
        temperature = (temperature - 32) * 5.0 / 9.0  # Konversi ke Celsius
        temperature_unit = 'ºC'  # Ubah unit ke ºC

    if pressure is not None and pressure_unit == 'inHg':
        pressure = pressure * 33.8639  # Konversi ke hPa
        pressure_unit = 'hPa'  # Ubah unit ke hPa

    if wind_speed is not None and wind_speed_unit == 'mph':
        wind_speed = wind_speed * 1.60934  # Konversi ke km/h
        wind_speed_unit = 'km/h'  # Ubah unit ke km/h

    if precip_rate is not None and precip_unit == 'in/hr':
        precip_rate = precip_rate * 25.4  # Konversi ke mm/hr
        precip_unit = 'mm/hr'  # Ubah unit ke mm/hr

    # Membatasi angka desimal hingga satu digit di belakang koma
    def round_value(value):
        if value is not None:
            return round(value, 1)
        else:
            return None

    temperature = round_value(temperature)
    humidity = round_value(humidity)
    pressure = round_value(pressure)
    precip_rate = round_value(precip_rate)
    wind_dir = round_value(wind_dir)
    wind_speed = round_value(wind_speed)
    solar_radiation = round_value(solar_radiation)

    # Konversi arah angin menjadi arah mata angin (kompas)
    def degrees_to_compass(degrees):
        if degrees is None:
            return None
        val = (degrees / 22.5) + 0.5
        val = int(val) % 16
        arr = ["N", "NNE", "NE", "ENE",
               "E", "ESE", "SE", "SSE",
               "S", "SSW", "SW", "WSW",
               "W", "WNW", "NW", "NNW"]
        return arr[val]

    wind_dir_compass = degrees_to_compass(wind_dir)

    # Membuat baris data
    data_row = {
        'tanggal': observation_time.split(' ')[0],
        'jam': observation_time.split(' ')[1],
        'suhu (°C)': temperature,
        'kelembaban (%)': humidity,
        'tekanan udara (hPa)': pressure,
        'curah hujan (mm)': precip_rate,
        'arah angin': f"{wind_dir}° ({wind_dir_compass})",
        'kecepatan angin (km/h)': wind_speed,
        'radiasi matahari (W/m²)': solar_radiation
    }

    # Mengonversi ke DataFrame
    df = pd.DataFrame([data_row])

    # Nama file CSV dengan path absolut
    file_name = '/home/yoga/Documents/data_cuaca_ecowitt.csv'

    # Mengecek apakah file sudah ada
    if not os.path.isfile(file_name):
        # Jika tidak ada, tulis header
        df.to_csv(
            file_name,
            index=False,
            mode='w',
            encoding='utf-8-sig',
            sep=',',              # Menggunakan koma sebagai pemisah
            decimal='.',          # Menggunakan titik sebagai tanda desimal
            float_format='%.1f',
            quoting=csv.QUOTE_NONE,   # Tidak menggunakan tanda kutip
            escapechar='\\',          # Karakter escape jika diperlukan
            lineterminator='\n'       # Menggunakan 'lineterminator' tanpa underscore
        )
    else:
        # Jika ada, tambahkan data tanpa header
        df.to_csv(
            file_name,
            index=False,
            mode='a',
            header=False,
            encoding='utf-8-sig',
            sep=',',              # Menggunakan koma sebagai pemisah
            decimal='.',          # Menggunakan titik sebagai tanda desimal
            float_format='%.1f',
            quoting=csv.QUOTE_NONE,   # Tidak menggunakan tanda kutip
            escapechar='\\',          # Karakter escape jika diperlukan
            lineterminator='\n'       # Menggunakan 'lineterminator' tanpa underscore
        )

    log_message('Data berhasil disimpan.')

except Exception as e:
    log_message(f"Error terjadi: {e}")
    sys.exit(1)
