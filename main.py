from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
import os

# ------------------ APP SETUP ------------------

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],      # tighten later if needed
    allow_methods=["*"],
    allow_headers=["*"],
)

FORM_OPEN = True
DATABASE_URL = os.environ.get("DATABASE_URL")

# ------------------ DB DEPENDENCY ------------------

def get_db():
    conn = psycopg2.connect(DATABASE_URL)
    try:
        yield conn
    finally:
        conn.close()   # 🔑 prevents locks

# ------------------ HEALTH ------------------

@app.get("/")
def health():
    return {"status": "API running"}

# ------------------ SUBMIT FORM ------------------

@app.post("/submit")
def submit_form(
    regNo: str,
    name: str,
    phone: str,
    company: str,
    slot: str,
    db=Depends(get_db)
):
    if not FORM_OPEN:
        raise HTTPException(status_code=403, detail="Form is closed")

    cur = db.cursor()

    try:
        # Check regNo exists
        cur.execute(
            "SELECT 1 FROM Recruits WHERE regNo = %s",
            (regNo,)
        )
        if not cur.fetchone():
            raise HTTPException(status_code=400, detail="Invalid regNo")

        # Prevent duplicate submission
        cur.execute(
            """
            SELECT 1
            FROM Submissions_v2
            WHERE regNo = %s
              AND company = %s
              AND status = 'Pending'
            """,
            (regNo, company)
        )

        if cur.fetchone():
            raise HTTPException(
                status_code=400,
                detail="You have already submitted for this company"
            )

        # Insert submission
        cur.execute(
            """
            INSERT INTO Submissions_v2 (regNo, name, phone, company, slot)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (regNo, name, phone, company, slot)
        )

        db.commit()
        return {"message": "Submission successful"}

    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        cur.close()

# ------------------ ASSIGN VOLUNTEER ------------------

@app.post("/assign")
def assign_volunteer(
    company: str,
    slot: str,
    db=Depends(get_db)
):
    cur = db.cursor()

    try:
        cur.execute(
            """
            SELECT r.regNo, r.name, r.email, r.phone, r.volcount
            FROM Recruits r
            JOIN Submissions_v2 s ON r.regNo = s.regNo
            WHERE s.status = 'Pending'
              AND s.company = %s
              AND s.slot = %s
            ORDER BY r.volcount ASC, s.time ASC
            LIMIT 1
            """,
            (company, slot)
        )

        row = cur.fetchone()
        if not row:
            return {"message": "No eligible candidates for this company and slot"}

        regNo, name, email, phone, volcount = row

        cur.execute(
            """
            INSERT INTO Volunteering
            (regNo, name, email, phone, company, slot, type)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (regNo, name, email, phone, company, slot, "HRM Volunteering")
        )

        cur.execute(
            """
            UPDATE Submissions_v2
            SET status = 'Assigned'
            WHERE regNo = %s AND status = 'Pending'
            """,
            (regNo,)
        )

        cur.execute(
            """
            UPDATE Recruits
            SET volcount = volcount + 1
            WHERE regNo = %s
            """,
            (regNo,)
        )

        db.commit()

        return {
            "message": "Volunteer assigned",
            "regNo": regNo,
            "name": name,
            "company": company,
            "slot": slot
        }

    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Assignment failed")
    finally:
        cur.close()
