from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.openapi.docs import get_swagger_ui_html
import psycopg2
import os
import secrets

# ------------------ SWAGGER AUTH ------------------

security = HTTPBasic()

SWAGGER_USER = os.getenv("SWAGGER_USER")
SWAGGER_PASS = os.getenv("SWAGGER_PASS")

def swagger_auth(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = secrets.compare_digest(
        credentials.username, SWAGGER_USER
    )
    correct_password = secrets.compare_digest(
        credentials.password, SWAGGER_PASS
    )

    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
            headers={"WWW-Authenticate": "Basic"},
        )

# ------------------ APP SETUP ------------------

app = FastAPI(docs_url=None, redoc_url=None)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
        conn.close()

# ------------------ CUSTOM SWAGGER ------------------

@app.get("/docs", include_in_schema=False)
def custom_swagger_ui(credentials: HTTPBasicCredentials = Depends(swagger_auth)):
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title="HRM Admin API"
    )

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
        cur.execute(
            "SELECT 1 FROM Recruits WHERE regNo = %s",
            (regNo,)
        )
        if not cur.fetchone():
            raise HTTPException(status_code=400, detail="Invalid regNo")

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

# ------------------ ASSIGN VOLUNTEER (PROTECTED) ------------------

@app.post("/assign")
def assign_volunteer(
    company: str,
    slot: str,
    db=Depends(get_db),
    _: HTTPBasicCredentials = Depends(swagger_auth)
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
