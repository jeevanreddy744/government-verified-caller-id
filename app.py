from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import os

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "database.db")


# =========================================================
# DATABASE CONNECTION
# =========================================================

def get_connection():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


# =========================================================
# INITIALIZE DATABASE
# =========================================================

def init_database():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS callers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phone_number TEXT UNIQUE NOT NULL,
            caller_name TEXT NOT NULL,
            category TEXT NOT NULL,
            department TEXT,
            location TEXT,
            verification_status TEXT,
            source TEXT,
            verified_date TEXT,
            notes TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS call_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phone_number TEXT NOT NULL,
            caller_name TEXT NOT NULL,
            category TEXT NOT NULL,
            call_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    demo_callers = [
        (
            "8712662511",
            "Addagudur Police Station",
            "official_department",
            "Police",
            "Telangana",
            "Official Number Verified",
            "Demo / Official Source",
            "2026-09-07",
            "Prototype demonstration record"
        ),
        (
            "8712662522",
            "Telangana Fire Services",
            "official_department",
            "Fire Services",
            "Telangana",
            "Official Number Verified",
            "Demo / Official Source",
            "2026-09-07",
            "Prototype demonstration record"
        ),
        (
            "8712662533",
            "Revenue Department",
            "official_department",
            "Revenue",
            "Telangana",
            "Official Number Verified",
            "Demo / Official Source",
            "2026-09-07",
            "Prototype demonstration record"
        ),
        (
            "9876543211",
            "ABC Business",
            "business",
            "Business",
            "Hyderabad",
            "Business Number",
            "Demo Data",
            "2026-09-07",
            "Prototype demonstration record"
        ),
        (
            "9876543210",
            "Rahul",
            "personal",
            "",
            "Hyderabad",
            "Personal Number",
            "Demo Data",
            "2026-09-07",
            "Prototype demonstration record"
        ),
        (
            "9876543212",
            "Potential Spam",
            "spam",
            "",
            "",
            "Spam / Caution",
            "Demo Data",
            "2026-09-07",
            "Prototype demonstration record"
        )
    ]

    for caller in demo_callers:

        cursor.execute("""
            INSERT OR IGNORE INTO callers
            (
                phone_number,
                caller_name,
                category,
                department,
                location,
                verification_status,
                source,
                verified_date,
                notes
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, caller)

    connection.commit()
    connection.close()


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            id,
            phone_number,
            caller_name,
            category,
            call_time
        FROM call_history
        ORDER BY id DESC
        LIMIT 5
    """)

    recent_calls = cursor.fetchall()

    connection.close()

    return render_template(
        "index.html",
        recent_calls=recent_calls
    )


# =========================================================
# INCOMING CALL
# =========================================================

@app.route("/incoming/<phone_number>")
def incoming_call(phone_number):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT *
        FROM callers
        WHERE phone_number = ?
        """,
        (phone_number,)
    )

    caller = cursor.fetchone()

    if caller is None:

        caller = {
            "phone_number": phone_number,
            "caller_name": "Unknown Number",
            "category": "unknown",
            "department": "",
            "location": "",
            "verification_status": "Number Not Verified",
            "source": "",
            "verified_date": "",
            "notes": "This number is not currently verified in our database."
        }

    cursor.execute("""
        INSERT INTO call_history
        (
            phone_number,
            caller_name,
            category
        )
        VALUES (?, ?, ?)
    """, (
        caller["phone_number"],
        caller["caller_name"],
        caller["category"]
    ))

    connection.commit()
    connection.close()

    return render_template(
        "incoming_call.html",
        caller=caller
    )


# =========================================================
# CALLER API
# =========================================================

@app.route("/api/caller/<phone_number>")
def get_caller(phone_number):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT *
        FROM callers
        WHERE phone_number = ?
        """,
        (phone_number,)
    )

    caller = cursor.fetchone()

    connection.close()

    if caller is None:

        return {
            "found": False,
            "message": "Number not found in the database"
        }

    return {
        "found": True,
        "phone_number": caller["phone_number"],
        "caller_name": caller["caller_name"],
        "category": caller["category"],
        "department": caller["department"],
        "location": caller["location"],
        "verification_status": caller["verification_status"],
        "source": caller["source"],
        "verified_date": caller["verified_date"],
        "notes": caller["notes"]
    }


# =========================================================
# RECENT CALLS API
# =========================================================

@app.route("/api/recent-calls")
def recent_calls():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            id,
            phone_number,
            caller_name,
            category,
            call_time
        FROM call_history
        ORDER BY id DESC
        LIMIT 5
    """)

    calls = cursor.fetchall()

    connection.close()

    return {
        "success": True,
        "calls": [
            {
                "id": call["id"],
                "phone_number": call["phone_number"],
                "caller_name": call["caller_name"],
                "category": call["category"],
                "call_time": call["call_time"]
            }
            for call in calls
        ]
    }


# =========================================================
# GOVERNMENT NUMBER MANAGEMENT
# =========================================================

@app.route("/manage-numbers")
def manage_numbers():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM callers
        WHERE category = 'official_department'
        ORDER BY id DESC
    """)

    callers = cursor.fetchall()

    connection.close()

    return render_template(
        "manage_numbers.html",
        callers=callers
    )


# =========================================================
# ADD GOVERNMENT NUMBER
# =========================================================

@app.route("/add-number", methods=["POST"])
def add_number():

    phone_number = request.form.get(
        "phone_number",
        ""
    ).strip()

    caller_name = request.form.get(
        "caller_name",
        ""
    ).strip()

    department = request.form.get(
        "department",
        ""
    ).strip()

    location = request.form.get(
        "location",
        ""
    ).strip()

    verification_status = request.form.get(
        "verification_status",
        "Official Number Verified"
    ).strip()

    source = request.form.get(
        "source",
        ""
    ).strip()

    verified_date = request.form.get(
        "verified_date",
        ""
    ).strip()

    notes = request.form.get(
        "notes",
        ""
    ).strip()

    if not phone_number or not caller_name:

        return redirect(
            url_for("manage_numbers")
        )

    if not phone_number.isdigit() or len(phone_number) != 10:

        return redirect(
            url_for("manage_numbers")
        )

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT OR REPLACE INTO callers
        (
            phone_number,
            caller_name,
            category,
            department,
            location,
            verification_status,
            source,
            verified_date,
            notes
        )
        VALUES (?, ?, 'official_department', ?, ?, ?, ?, ?, ?)
    """, (
        phone_number,
        caller_name,
        department,
        location,
        verification_status,
        source,
        verified_date,
        notes
    ))

    connection.commit()
    connection.close()

    return redirect(
        url_for("manage_numbers")
    )


# =========================================================
# DELETE GOVERNMENT NUMBER
# =========================================================

@app.route("/delete-number/<int:caller_id>", methods=["POST"])
def delete_number(caller_id):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        DELETE FROM callers
        WHERE id = ?
        AND category = 'official_department'
        """,
        (caller_id,)
    )

    connection.commit()
    connection.close()

    return redirect(
        url_for("manage_numbers")
    )


# =========================================================
# DATABASE TEST
# =========================================================

@app.route("/api/test-history")
def test_history():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM call_history
    """)

    total = cursor.fetchone()["total"]

    connection.close()

    return {
        "database": DATABASE,
        "total_calls_saved": total
    }


# =========================================================
# START SERVER
# =========================================================

if __name__ == "__main__":

    init_database()

    print("")
    print("========================================")
    print(" Government Verified Caller ID")
    print("========================================")
    print("Database:", DATABASE)
    print("Server: http://127.0.0.1:5000")
    print("========================================")
    print("")

    app.run(debug=True)