# Menggunakan image Python yang ringan
FROM python:3.10-slim

# Menentukan direktori kerja di dalam container
WORKDIR /app

# Menyalin file requirements dan menginstalnya
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Menyalin seluruh kode proyek ke dalam container
COPY . .

# (Command eksekusi akan diatur oleh docker-compose)