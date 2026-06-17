# CareSync — Patient Care Gap Analysis & Risk Stratification Platform

## Overview
CareSync is a full-stack healthcare platform built for population health management. It identifies critical preventive care gaps based on clinical guidelines (HEDIS/USPSTF) and stratifies patient risk using a weighted clinical algorithm.

## Tech Stack
- **Backend**: Python 3.10+, FastAPI, SQLAlchemy, SQLite
- **Frontend**: Vite, React, Recharts, Lucide Icons, Vanilla CSS
- **Auth**: JWT with bcrypt

## Setup Instructions

### 1. Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```
*Note: The backend will automatically seed 50 synthetic patients on first run.*

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

### 3. Demo Credentials
- **Provider Account**: `provider@caresync.com` / `demo123`
- **Admin Account**: `admin@caresync.com` / `demo123`

## Features
- **Dashboard**: High-level KPIs and risk distribution.
- **Patient Profiles**: Detailed views of conditions, medications, history, and active care gaps.
- **Care Gap Engine**: Automated analysis of missing preventive care.
- **Risk Stratification**: 0-100 scoring based on clinical factors.
- **Analytics**: Provider performance and population health metrics.
