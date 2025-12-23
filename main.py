FORM_OPEN = True


from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException
import psycopg2
import os

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # allow all origins (safe for this use case)
    allow_methods=["*"],
    allow_headers=["*"],
)


DATABASE_URL = os.environ.get("DATABASE_URL")

def get_db():
    return psycopg2.connect(DATABASE_URL)

@app.get("/")
def health():
    return {"status": "API running"}





@app.post("/submit")

def submit_form(
    regNo: str,
    name: str,
    phone: str,
    company: str,
    slot: str
):
    if not FORM_OPEN:
    	raise HTTPException(status_code=403, detail="Form is closed")
    conn = get_db()
    cur = conn.cursor()

    # Check regNo exists
    cur.execute(
        "SELECT 1 FROM Recruits WHERE regNo = %s",
        (regNo,)
    )
    if not cur.fetchone():
        raise HTTPException(status_code=400, detail="Invalid regNo")

    # Check duplicate submission for same company
    cur.execute(
    	"""
    	SELECT 1
    	FROM Submissions
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
        INSERT INTO Submissions (regNo, name, phone, company, slot)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (regNo, name, phone, company, slot)
    )

    conn.commit()
    cur.close()
    conn.close()

    return {"message": "Submission successful"}












@app.post("/assign")
def assign_volunteer(company: str, slot: str):
    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT r.regNo, r.name, r.email, r.phone, r.volcount
        FROM Recruits r
        JOIN Submissions s ON r.regNo = s.regNo
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
        INSERT INTO Volunteering (regNo, name, email, phone, company, slot, type)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """,
        (regNo, name, email, phone, company, slot, "HRM Volunteering")
    )

    cur.execute(
        """
        UPDATE Submissions
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

    conn.commit()
    cur.close()
    conn.close()

    return {
        "message": "Volunteer assigned",
        "regNo": regNo,
        "name": name,
        "company": company,
        "slot": slot
    }



