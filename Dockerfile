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

# Set PYTHONPATH to include /app so you can import modules easily
ENV PYTHONPATH=/app

# Copy frontend build from previous stage
COPY --from=frontend /front-end/dist /app/front-end/dist

# Install `concurrently`
RUN apt-get update && apt-get install -y nodejs npm && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*
RUN npm install -g concurrently serve

# Expose required ports
EXPOSE 8080 5173

# Start both frontend and backend using `concurrently`
CMD concurrently "serve -s /app/front-end/dist -l 5173" "gunicorn --bind 0.0.0.0:8080 --workers 2 -k gthread --threads 8 --timeout 600 app.server:app"
