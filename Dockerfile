# Use multi-stage build for smaller final image
FROM node:18 AS frontend
WORKDIR /front-end

# Copy frontend files
COPY package.json package-lock.json vite.config.js tailwind.config.js postcss.config.js ./
COPY init.js eslint.config.js ./
COPY public ./public
COPY src ./src

# Install dependencies & build frontend
RUN npm install
RUN npm run build

# Backend setup
FROM python:3.9
WORKDIR /app

# Install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend files
COPY . ./

# Copy frontend build from previous stage
COPY --from=frontend /front-end/dist /app/front-end/dist

# Install `supervisord` and required dependencies
RUN apt-get update && apt-get install -y supervisor nodejs npm ffmpeg && rm -rf /var/lib/apt/lists/*
RUN npm install -g serve

# Create Supervisord config file
RUN echo "[supervisord]\nnodaemon=true\n" > /etc/supervisord.conf && \
    echo "[program:backend]\ncommand=gunicorn --bind 0.0.0.0:8080 --workers 2 -k gthread --threads 8 --timeout 600 app.server:app\nautostart=true\nautorestart=true\nstderr_logfile=/dev/stderr\nstdout_logfile=/dev/stdout\n" >> /etc/supervisord.conf && \
    echo "[program:frontend]\ncommand=serve -s /app/front-end/dist -l 8080\nautostart=true\nautorestart=true\nstderr_logfile=/dev/stderr\nstdout_logfile=/dev/stdout\n" >> /etc/supervisord.conf

# Expose only the backend port
EXPOSE 8080

# Start Supervisor to manage both backend & frontend
CMD ["supervisord", "-c", "supervisord.conf"]