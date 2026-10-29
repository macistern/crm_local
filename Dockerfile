FROM node:20-alpine AS assets
WORKDIR /build
COPY package.json ./
RUN npm install
COPY tailwind.config.js ./
COPY templates ./templates
COPY static/src ./static/src
RUN npm run build:css
RUN cp node_modules/htmx.org/dist/htmx.min.js static/js-htmx.min.js

FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
COPY --from=assets /build/static/css/tailwind.css ./static/css/tailwind.css
COPY --from=assets /build/static/js-htmx.min.js ./static/js/htmx.min.js
RUN chmod +x manage.py
EXPOSE 8000
CMD ["sh", "-c", "python manage.py migrate --noinput && python manage.py setup_roles && python manage.py bootstrap_users && python manage.py collectstatic --noinput && gunicorn crm_local.wsgi:application --bind 0.0.0.0:8000"]
