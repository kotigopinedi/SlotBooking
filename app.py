from flask import Flask, render_template, request, redirect, url_for, flash
import psycopg2
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = "slot_booking_secret_key"


# ---------------- DATABASE CONNECTION ----------------
def get_db_connection():
    return psycopg2.connect(
        host=os.environ.get("DB_HOST"),
        database=os.environ.get("DB_NAME"),
        user=os.environ.get("DB_USER"),
        password=os.environ.get("DB_PASSWORD"),
        port=os.environ.get("DB_PORT")
    )


# ---------------- HOME ----------------
@app.route('/')
def home():
    return render_template('index.html')


# ---------------- AVAILABLE SLOTS ----------------
@app.route('/available')
def available_slots():
    db = get_db_connection()
    cursor = db.cursor()

    cursor.execute("SELECT * FROM slots WHERE is_booked = FALSE ORDER BY slot_time ASC")
    rows = cursor.fetchall()

    slots = []
    for row in rows:
        slots.append({
            "id": row[0],
            "slot_time": row[1]
        })

    cursor.close()
    db.close()

    return render_template('available_slots.html', slots=slots)


# ---------------- BOOK SLOT ----------------
@app.route('/book/<int:slot_id>', methods=['GET', 'POST'])
def book_slot(slot_id):
    db = get_db_connection()
    cursor = db.cursor()

    cursor.execute("SELECT * FROM slots WHERE id = %s", (slot_id,))
    row = cursor.fetchone()

    if not row:
        cursor.close()
        db.close()
        flash("Slot not found.", "error")
        return redirect(url_for('available_slots'))

    if row[2]:  # is_booked
        cursor.close()
        db.close()
        flash("This slot is already booked.", "error")
        return redirect(url_for('available_slots'))

    slot = {
        "id": row[0],
        "slot_time": row[1]
    }

    if request.method == 'POST':
        name = request.form.get('name', '').strip()

        if not name:
            flash("Name is required.", "error")
            return render_template('book_slot.html', slot=slot)

        cursor.execute("""
            UPDATE slots
            SET is_booked = TRUE, booked_by = %s, booked_at = %s
            WHERE id = %s AND is_booked = FALSE
        """, (name, datetime.now(), slot_id))

        db.commit()

        if cursor.rowcount == 0:
            cursor.close()
            db.close()
            flash("Slot already booked.", "error")
            return redirect(url_for('available_slots'))

        cursor.close()
        db.close()

        flash("Slot booked successfully!", "success")
        return redirect(url_for('booked_slots'))

    cursor.close()
    db.close()
    return render_template('book_slot.html', slot=slot)


# ---------------- BOOKED SLOTS ----------------
@app.route('/booked')
def booked_slots():
    db = get_db_connection()
    cursor = db.cursor()

    cursor.execute("SELECT * FROM slots WHERE is_booked = TRUE ORDER BY slot_time ASC")
    rows = cursor.fetchall()

    slots = []
    for row in rows:
        slots.append({
            "slot_time": row[1],
            "booked_by": row[3]
        })

    cursor.close()
    db.close()

    return render_template('booked_slots.html', slots=slots)


# ---------------- QUICK BOOK ----------------
@app.route('/quick-book')
def quick_book():
    db = get_db_connection()
    cursor = db.cursor()

    cursor.execute("""
        SELECT * FROM slots 
        WHERE is_booked = FALSE 
        ORDER BY slot_time ASC 
        LIMIT 1
    """)
    row = cursor.fetchone()

    cursor.close()
    db.close()

    if not row:
        flash("No slots available.", "error")
        return redirect(url_for('available_slots'))

    return redirect(url_for('book_slot', slot_id=row[0]))


# ---------------- CANCEL SLOT ----------------
@app.route('/cancel/<int:slot_id>', methods=['POST'])
def cancel_slot(slot_id):
    db = get_db_connection()
    cursor = db.cursor()

    cursor.execute("""
        UPDATE slots
        SET is_booked = FALSE,
            booked_by = NULL,
            booked_at = NULL
        WHERE id = %s
    """, (slot_id,))

    db.commit()

    cursor.close()
    db.close()

    flash("Slot cancelled successfully.", "success")
    return redirect(url_for('booked_slots'))


# ---------------- RUN ----------------
if __name__ == '__main__':
    app.run()