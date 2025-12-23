# HRM Volunteering Allocation System

A full-stack web application designed to manage and allocate HRM volunteers efficiently during placement and recruitment drives. The system allows students to submit volunteering preferences through a public form, while administrators can securely assign volunteers based on fairness and availability.


## 🚀 Live Project

* **Frontend (Form)**: Hosted on Netlify
* **Backend API**: FastAPI deployed on Render
* **Database**: PostgreSQL (Supabase)

## 🧩 Problem Statement

During placement drives, managing volunteers manually often leads to:

* duplicate registrations
* unfair allocation

This project automates the entire process with a clean submission flow, secure admin actions, and database-level safeguards.


# ⚙️ Tech Stack

**Frontend**

* HTML, CSS, JavaScript
* Mobile-responsive UI
* Hosted on Netlify

**Backend**

* FastAPI (Python)
* REST APIs
* Swagger UI (admin only)

**Database**

* PostgreSQL (Supabase)
* Foreign key constraints
* Unique partial indexes

**Deployment**

* Render (backend hosting)
* Netlify (frontend hosting)


# System Flow

# Student Flow

1. Student opens the public form link
2. Submits details (regNo, name, company, slot, etc.)
3. Data is validated and stored in PostgreSQL

# Admin Flow

1. Admin accesses password-protected Swagger UI
2. Triggers volunteer assignment for a company + slot
3. System assigns the least-used eligible volunteer fairly


## 🛡️ Key Features

* ✅ Public submission form (no login required)
* 🔐 Password-protected admin access (Swagger UI)
* ⚖️ Fair volunteer allocation using volunteer count + timestamp
* 🚫 Prevention of duplicate pending submissions
* 🧱 Database-level integrity using constraints
* 📱 Mobile-responsive frontend
* ☁️ Fully deployed and live



Just tell me 👍
