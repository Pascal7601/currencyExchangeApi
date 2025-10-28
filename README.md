# currencyExchangeApi
- A simple, scalable Django-based REST API for fetching and managing currency exchange rates, country data, and related metadata.

## Features
- Country Management: List all countries, fetch details by name, refresh country data, and generate summary images.
- Status Endpoint: Quick health check for API status.
- Exchange Rates: Integrated logic for currency conversion (via external API like ExchangeRate-API or similar—configure in views).
- Database Persistence: Uses MySQL for storing country/exchange data.
- Docker Support: Containerized with Dockerfile for easy local/prod deployment.
- RESTful Design: JSON responses, error handling, and class-based views for efficiency.

## Tech Stack
- Backend: Django 4.x / Python 3.12
- Database: MySQL 8.0
- Dependencies: mysqlclient, python-decouple (env vars), requests (for external APIs), Pillow (for image gen).
- Containerization: Docker & Docker Compose
- Deployment: Compatible with Railway

## Installation & Setup
- docker compose up --build