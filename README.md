# Smart OPD — Just-In-Time Predictive Queue Management System

[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-4169E1?style=flat&logo=postgresql&logoColor=white)](https://postgresql.org)
[![Next.js](https://img.shields.io/badge/Next.js-14-000000?style=flat&logo=nextdotjs&logoColor=white)](https://nextjs.org)
[![Gemini AI](https://img.shields.io/badge/Gemini_AI-Powered-4285F4?style=flat&logo=google&logoColor=white)](https://ai.google.dev)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat&logo=docker&logoColor=white)](https://docker.com)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat)](LICENSE)

---

## The Problem

In Indian government hospitals, over a hundred patients are given token numbers every morning. None of them know when their turn will actually come. So they all sit in the corridor and wait — for hours. Daily wage laborers lose an entire day's income. Elderly and illiterate patients endure physical discomfort with no information. When an emergency walks in, the queue collapses into panic. The poorest people pay the highest price for a broken system.

This is not a minor inconvenience. It is a systemic failure that penalizes the most vulnerable population for something as basic as seeing a doctor.

---

## The Solution

Smart OPD physically decouples patients from the doctor's corridor using **event-based triggers instead of time-based appointments**. The system does not tell a patient "come at 2:00 PM." It waits for the exact moment the previous patient finishes, calculates a fixed walking buffer, and sends a single SMS: **"Start Walking."**

By the time the patient walks from a distant waiting area, the room is ready. Only two people are ever near the corridor — the patient being seen, and the patient walking toward it.

The entire system runs on **SMS and missed calls**. No smartphone required. No app to download. No internet needed. It works on the simplest feature phone available in rural India.

---

## How It Works

```
Patient registers (name + phone) --> Gets token via SMS --> Waits anywhere (home, chai shop, ground)

                                    Doctor finishes Token N
                                          |
                                          v
                              System sends "Start Walking" to Token N+2
                                          |
                                          v
                              Token N+2 walks from waiting area
                                          |
                                          v
                              Token N+1 enters the room
```

The "Start Walking" trigger is fired only when the doctor clicks "Done" on the current patient. A fixed buffer (configurable, default 7 minutes) is enforced between triggers to prevent hallway bottlenecks. This is not a scheduling system — it is a real-time physical flow controller.

---

## AI-Powered Features

### Multilingual SMS Generation (Gemini)
Raw system data like `Token 45, Room 5, 7 mins` is passed to Gemini, which translates it into simple, spoken-style native language text. An illiterate patient can ask any bystander to read the SMS and understand exactly what to do. Supports Hindi, Tamil, Telugu, Bengali, Marathi, and English.

### Patient Reply Understanding (Gemini)
Patients send messy, unstructured messages from basic phones — "bus late coming", "outside now", "breakdown". Traditional keyword matching fails completely. Gemini parses these raw texts, extracts the exact intent, and updates the patient status without any human intervention.

### Emergency Delay Communication (Gemini)
When a walk-in emergency pauses the queue, robotic template messages cause panic. Gemini dynamically generates empathetic, calming messages that reassure patients their token is safe, explain the delay humanely, and instruct them to stay calm — preventing mob mentality at the door.

### Disease Surveillance Engine (Gemini + Scheduled Analysis)
Every 2 hours, the system aggregates all symptom data collected during patient registrations. Gemini analyzes the cluster for patterns — similar symptoms, geographic concentration, temporal spikes — and generates a structured summary of suspected disease outbreaks. Example output: "18 patients in the last 2 hours reporting high fever with severe body pain and joint pain — consistent with dengue cluster, 87% confidence." This gives hospital administrators early warning capability without any manual reporting.

---

## Disease Surveillance Radar

[![Surveillance](https://img.shields.io/badge/Feature-Epidemiological_Radar-red?style=flat)]()

One of the most impactful features of Smart OPD is its passive disease surveillance capability. Every patient booking captures a symptom description. The system:

- Collects symptom data continuously from all patient registrations
- Runs an AI-powered analysis every 2 hours automatically
- Detects disease clusters (e.g., 18 dengue-like cases in a 2-hour window)
- Generates health alerts with disease name, confidence percentage, and match count
- Presents a visual radar dashboard for hospital administrators
- Tracks alert status from ACTIVE to RESOLVED

This transforms a simple queue management system into a public health early warning tool — at zero additional cost or effort from staff.

---

## Core System Features

### Zero-App Interface
The entire patient experience runs through standard SMS delivery and cellular voice networks. Compatible with every phone sold in India since 2005. No data pack required.

### Missed Call Status Check
Patients give a missed call to a dedicated number. The system instantly recognizes the caller ID, looks up their active token, calculates current wait time, and sends an SMS reply with their status. Zero typing required on a basic phone.

### No-Show Detection and Auto-Skip
If a patient does not arrive within a strict timeout (configurable, default 10 minutes) after the "Start Walking" trigger, the system automatically marks them as a no-show and triggers the next patient. Zero downtime for the doctor.

### Emergency Protocol
When a doctor triggers an emergency: all walking commands freeze instantly, Gemini generates calming broadcast messages to all waiting patients, the queue enters paused state, and upon resumption all subsequent triggers are shifted forward by the exact delay duration.

### Late Arrival Re-Queuing
A patient marked as no-show (or whose delay was understood via AI text parsing) can be restored by staff, but is appended to the end of the queue — never injected mid-flow to prevent disruption.

### Strict Identity Enforcement
One phone number = one active token per doctor per day. A hard database constraint, not AI — simple and bulletproof.

### Daily Auto-Reset
All queues, tokens, and logs are archived and reset at a predefined time each night. Fresh state every morning.

---

## Interfaces

### Doctor's Screen
Minimal. Shows current patient name and token. Three buttons: "Mark Done and Call Next", "Skip Patient", "Trigger Emergency". Interaction time per patient: under 3 seconds.

### Clerk's Registration
Two fields: Name and Phone Number. That is it. Token generation, timestamping, and initial SMS are fully automatic. A color-coded live queue dashboard with single-click override buttons for edge cases.

### Patient's Experience
Register at counter or via web booking. Receive an SMS. Go home or sit under a tree. Get a "Start Walking" SMS at the right moment. Walk in. See the doctor. Leave.

---

## Technical Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Docker Compose                        │
│                                                              │
│  ┌──────────────┐    ┌──────────────────┐    ┌───────────┐  │
│  │  Next.js      │    │  FastAPI Backend │    │ PostgreSQL│  │
│  │  Frontend     │───>│  (Python 3.11)   │───>│  15       │  │
│  │  (Port 3000)  │    │  (Port 8000)     │    │ (Port 5433)│ │
│  └──────────────┘    └───────┬──────────┘    └───────────┘  │
│                               │                              │
│                    ┌──────────┼──────────┐                   │
│                    │          │          │                   │
│               ┌────┴───┐ ┌───┴───┐ ┌────┴────┐             │
│               │ Gemini  │ │ MSG91 │ │APScheduler│             │
│               │  AI     │ │  SMS  │ │ (30s / 2h)│             │
│               └────────┘ └───────┘ └─────────┘             │
└─────────────────────────────────────────────────────────────┘
```

### Backend
- **Framework**: FastAPI with async support
- **ORM**: SQLAlchemy 2.0 with PostgreSQL
- **AI**: Gemini via Groq API for multilingual generation, reply parsing, and surveillance analysis
- **SMS**: MSG91 for delivery and missed call webhooks
- **Scheduler**: APScheduler with two jobs — queue engine (every 30 seconds) and surveillance (every 2 hours)
- **Auth**: API key-based internal authentication for staff/doctor endpoints

### Database
- PostgreSQL 15 with custom ENUM types for registration and queue states
- Views for active queue and daily booking analytics
- Triggers for automatic `updated_at` timestamps
- Indexed on phone, token, status, and doctor for fast lookups

### Frontend
- Next.js 14 with server-side rendering
- Doctor dashboard, clerk registration panel, and admin surveillance radar
- Real-time queue state display

---

## Database Schema

| Table | Purpose |
|-------|---------|
| `patient_master` | Unique patient records keyed by phone number |
| `registration_queue` | Pre-doctor registration with token assignment |
| `doctor_config` | Doctor profiles, departments, buffer times, daily limits |
| `doctor_queue` | Active doctor queue with status, symptoms, AI messages, triage |
| `health_alerts` | Disease surveillance alerts with confidence and match counts |
| `simulation_logs` | Surveillance analysis run logs with progress and metrics |

### Queue State Machine

```
WAITING --> CALLED --> IN_ROOM --> COMPLETED
   |           |          |
   |           |          +--> NO_SHOW (auto, after timeout)
   |           |
   |           +--> EMERGENCY_PAUSED --> (resume) --> CALLED
   |
   +--> SKIP (manual by doctor)
```

---

## API Endpoints

### Public (No Auth)
| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/book` | Patient self-booking with AI triage and multilingual SMS |
| POST | `/webhook/missed-call` | Missed call status lookup |
| GET | `/public-queue-count` | Current queue length for a doctor |

### Clerk (API Key)
| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/clerk/add` | Register new patient |
| POST | `/clerk/call-next` | Call next waiting patient |
| POST | `/clerk/assign-doctor` | Assign patient to a doctor |
| GET | `/clerk/queue` | View full registration queue |

### Doctor (API Key)
| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/doctor/queue` | Get doctor's active queue |
| POST | `/doctor/done-next` | Mark current done, call next, trigger walking SMS |
| POST | `/doctor/emergency` | Pause queue, broadcast calming messages |
| POST | `/doctor/skip` | Skip current patient |

### Admin (API Key)
| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/admin/recent-symptoms` | Fetch recent symptom entries |
| GET | `/admin/alerts` | Get active disease alerts |
| POST | `/admin/run-surveillance` | Manually trigger surveillance analysis |

### System
| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/health` | Backend health check |

---

## Project Structure

```
smart-opd/
├── database/
│   ├── init.sql              # Schema, enums, indexes, views, triggers, seed
│   └── seed.sql              # Test data for development
├── smart-opd-backend/
│   ├── app/
│   │   ├── main.py           # FastAPI app, lifespan, scheduler, middleware
│   │   ├── core/
│   │   │   └── config.py     # Environment settings
│   │   ├── api/
│   │   │   ├── registration.py
│   │   │   ├── doctor.py
│   │   │   ├── patient.py
│   │   │   ├── admin.py
│   │   │   └── disaster_sim.py
│   │   └── services/
│   │       ├── queue_engine.py        # Buffer check, no-show detection
│   │       └── surveillance_service.py # AI-powered disease analysis
│   ├── .env
│   ├── Dockerfile
│   └── requirements.txt
├── smart-opd-frontend/
│   └── (Next.js 14 application)
├── demo/
│   ├── generate-demo-data.ps1    # 51 patients: dengue cluster + viral + normal
│   ├── reset-demo-data.ps1       # Clear all test data
│   └── trigger-surveillance.ps1  # Force immediate surveillance run
├── test_ai_backend.py            # Full test suite with multilingual validation
├── test_backend.py               # Quick workflow smoke test
├── docker-compose.yml            # PostgreSQL + Backend orchestration
└── .gitignore
```

---

## Quick Start

### Prerequisites
- Docker and Docker Compose
- MSG91 account (for SMS delivery)
- Gemini API key (via Groq)

### 1. Configure Environment
```bash
cd smart-opd/smart-opd-backend
cp .env .env.backup
# Edit .env with your actual API keys:
#   GEMINI_API_KEY=your_key
#   MSG91_AUTH_KEY=your_key
#   MSG91_SENDER_ID=your_sender_id
```

### 2. Start Services
```bash
cd smart-opd
docker-compose up --build
```
PostgreSQL initializes on first boot with schema and seed data. Backend starts with two scheduled jobs.

### 3. Generate Demo Data (Optional)
```powershell
# In a separate terminal, after backend is healthy:
cd smart-opd/demo
.\generate-demo-data.ps1
```
This creates 51 patients: 18 dengue-symptom cluster, 18 viral fever cluster, 15 normal cases.

### 4. Trigger Surveillance Manually (Optional)
```powershell
.\trigger-surveillance.ps1
```
Or wait 2 hours for the automatic scheduled run.

### 5. Run Tests
```bash
# Quick smoke test
python test_backend.py

# Full test suite with multilingual AI validation
python test_ai_backend.py
```

---

## Hackathon Alignment

**Competition**: Solution Challenge 2026 — Build with AI (GDG on Campus India x Hack2Skill)

**Track**: Smart Resource Allocation — Data-Driven Volunteer and Resource Coordination for Social Impact

**UN Sustainable Development Goals Addressed**:
- [![SDG 3](https://img.shields.io/badge/SDG_3-Good_Health--4C9F38?style=flat)]() — Reducing barriers to healthcare access for the poorest
- [![SDG 10](https://img.shields.io/badge/SDG_10-Reduced_Inequalities-DD1367?style=flat)]() — Serving the digitally excluded, illiterate, and economically vulnerable
- [![SDG 11](https://img.shields.io/badge/SDG_11-Sustainable_Cities-FD9D24?style=flat)]() — Decongesting public hospital infrastructure

**Why This Fits the Track**: Smart OPD does not just allocate tokens — it intelligently reallocates human time. Daily wage laborers get their hours back. Hospital staff spend zero time on phone calls. Doctors operate without crowd stress. And the surveillance engine converts passive symptom data into actionable public health intelligence, enabling resource pre-positioning before outbreaks overwhelm the system.

---

## What Makes This Different

Most queue management systems assume smartphones, internet connectivity, and literate users. They optimize for private hospitals where patients speak English and check apps. Smart OPD is built for the opposite extreme — the rural daily wage laborer with a 15-year-old Nokia who cannot read. Every design decision flows from that constraint:

- SMS instead of apps
- Missed calls instead of form submissions
- AI-translated simple language instead of English templates
- Event-based triggers instead of time slots
- Single-field clerk input instead of lengthy registration forms

The disease surveillance capability exists because the system already captures symptom data as a side effect of normal operation — no additional burden on staff or patients. The AI turns waste data into a public health tool.

---

## Built With

[![Python](https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-D71F00?style=flat&logo=postgresql&logoColor=white)](https://sqlalchemy.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=flat&logo=postgresql&logoColor=white)](https://postgresql.org)
[![Next.js](https://img.shields.io/badge/Next.js-000000?style=flat&logo=nextdotjs&logoColor=white)](https://nextjs.org)
[![Gemini](https://img.shields.io/badge/Gemini_AI-4285F4?style=flat&logo=google&logoColor=white)](https://ai.google.dev)
[![Groq](https://img.shields.io/badge/Groq_API-F55036?style=flat)](https://groq.com)
[![MSG91](https://img.shields.io/badge/MSG91_SMS-FF6B00?style=flat)](https://msg91.com)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat&logo=docker&logoColor=white)](https://docker.com)
[![APScheduler](https://img.shields.io/badge/APScheduler-3.10-2C3E50?style=flat)](https://apscheduler.readthedocs.io)

---

## Support

For queries related to this submission, contact the team through the Hack2Skill portal or email `solutionchallengesupport@hack2skill.com`.