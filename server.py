from flask import Flask, render_template, request, redirect, g, session, flash, jsonify, url_for
import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import traceback

app = Flask(__name__)
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.secret_key = "Bila4EkX2X"
app.config["UPLOAD_FOLDER"] = "static/resumes"

os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

ALLOWED_RESUME_EXTENSIONS = {"pdf", "doc", "docx"}
ALLOWED_LOGO_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}


def allowed_file(filename, allowed_extensions):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed_extensions


def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect("main.db")
        db.row_factory = sqlite3.Row 
    return db


def get_approved_jobs(job_query, sort_by):
    sql_query = (
        "SELECT ID, JOB_TITLE, DESCRIPTION, COMPANY, LOGO FROM JOBS WHERE APPROVED=1"
    )
    params = []

    if job_query:
        sql_query += " AND (JOB_TITLE LIKE ? OR COMPANY LIKE ?)"
        params.extend(["%" + job_query + "%", "%" + job_query + "%"])

    if sort_by == "oldest":
        sql_query += " ORDER BY ID ASC"
    else:
        sql_query += " ORDER BY ID DESC"

    cursor = get_db().execute(sql_query, tuple(params))
    return cursor.fetchall()


@app.route("/student/dashboard")
def student_dashboard():
    if "user_id" not in session or session["user_type"] != "student":
        return redirect("/signin")

    user_id = session["user_id"]
    db = get_db()

    cursor = db.execute(
        "SELECT COUNT(*) FROM APPLICATIONS WHERE user_id = ?", (user_id,)
    )
    total_applied_jobs = cursor.fetchone()[0]

    cursor = db.execute("SELECT COUNT(*) FROM JOBS WHERE APPROVED = 1")
    total_available_jobs = cursor.fetchone()[0]

    cursor = db.execute(
        """
        SELECT COUNT(DISTINCT j.ID)
        FROM JOBS j
        JOIN APPLICATIONS a ON j.ID = a.job_id
        WHERE a.user_id = ? AND j.APPROVED = 1
    """,
        (user_id,),
    )
    pending_decisions = cursor.fetchone()[0]

    cursor = db.execute(
        """
        SELECT j.JOB_TITLE, j.COMPANY
        FROM APPLICATIONS a
        JOIN JOBS j ON a.job_id = j.ID
        WHERE a.user_id = ?
        ORDER BY a.ID DESC
        LIMIT 5
    """,
        (user_id,),
    )
    recent_applications = cursor.fetchall()

    cursor = db.execute(
        """
        SELECT j.ID, j.JOB_TITLE, j.COMPANY FROM JOBS j
        WHERE j.APPROVED = 1 AND j.ID NOT IN (SELECT job_id FROM APPLICATIONS WHERE user_id = ?)
        ORDER BY j.ID DESC
        LIMIT 3
    """,
        (user_id,),
    )
    recommended_jobs = cursor.fetchall()

    return render_template(
        "studentdashboard.html",
        total_applied_jobs=total_applied_jobs,
        total_available_jobs=total_available_jobs,
        pending_decisions=pending_decisions,
        recent_applications=recent_applications,
        recommended_jobs=recommended_jobs,
    )


@app.route("/student")
def student_home():
    if "user_id" not in session or session["user_type"] != "student":
        return redirect("/signin")

    job_query = request.args.get("query", "")
    sort_by = request.args.get("sort", "newest")
    data = get_approved_jobs(job_query, sort_by)

    user_id = session["user_id"]
    cursor = get_db().execute(
        "SELECT job_id FROM SAVED_JOBS WHERE user_id = ?", (user_id,)
    )
    saved_job_ids = {row[0] for row in cursor.fetchall()}

    return render_template(
        "studenthome.html",
        data=data,
        query=job_query,
        sort=sort_by,
        saved_job_ids=saved_job_ids,
    )


@app.route("/student/apply/<int:job_id>")
def student_apply(job_id):
    cursor = get_db().execute(
        "SELECT ID,JOB_TITLE,DESCRIPTION,COMPANY FROM JOBS WHERE ID=?", (job_id,)
    )
    data = cursor.fetchone()
    return render_template("studentapply.html", data=data)


@app.route("/student/apply/submit/<int:job_id>", methods=["POST"])
def submit_application(job_id):
    if "user_id" not in session or session["user_type"] != "student":
        return redirect("/signin")

    user_id = session["user_id"]
    experience = request.form.get("applicant_experience")
    phone = request.form.get("phone_number")
    email = request.form.get("email")

    resume_filename = None
    if "resume" in request.files and request.files["resume"].filename != "":
        resume_file = request.files["resume"]
        if resume_file and allowed_file(
            resume_file.filename, ALLOWED_RESUME_EXTENSIONS
        ):
            filename = secure_filename(resume_file.filename)
            resume_file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
            resume_filename = filename
        else:
            flash("Invalid resume file type. Allowed types are: pdf, doc, docx", "error")
            return redirect(request.url)

    db = get_db()
    db.execute(
        """
        INSERT INTO APPLICATIONS 
        (user_id, job_id, experience_summary, phone_number, contact_email, resume_filename) 
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (user_id, job_id, experience, phone, email, resume_filename),
    )
    db.commit()

    flash("Your application has been submitted successfully!", "success")
    return redirect("/student/myapplications")


@app.route("/student/myapplications")
def my_applications():
    if "user_id" not in session or session["user_type"] != "student":
        return redirect("/signin")

    user_id = session["user_id"]
    job_query = request.args.get("query", "")
    sort_by = request.args.get("sort", "newest")

    sql_query = """
        SELECT j.ID, j.JOB_TITLE, j.DESCRIPTION, j.COMPANY, j.LOGO
        FROM JOBS j
        JOIN APPLICATIONS a ON j.ID = a.job_id
        WHERE a.user_id = ?
    """
    params = [user_id]

    if job_query:
        sql_query += " AND (j.JOB_TITLE LIKE ? OR j.COMPANY LIKE ?)"
        params.extend(["%" + job_query + "%", "%" + job_query + "%"])

    if sort_by == "oldest":
        sql_query += " ORDER BY j.ID ASC"
    else:
        sql_query += " ORDER BY j.ID DESC"

    cursor = get_db().execute(sql_query, tuple(params))
    data = cursor.fetchall()

    return render_template(
        "myapplications.html", data=data, query=job_query, sort=sort_by
    )


@app.route("/student/saved")
def saved_jobs():
    if "user_id" not in session or session["user_type"] != "student":
        return redirect("/signin")

    user_id = session["user_id"]
    job_query = request.args.get("query", "")
    sort_by = request.args.get("sort", "newest")

    sql_query = """
        SELECT j.ID, j.JOB_TITLE, j.DESCRIPTION, j.COMPANY, j.LOGO
        FROM JOBS j
        JOIN SAVED_JOBS s ON j.ID = s.job_id
        WHERE s.user_id = ?
    """
    params = [user_id]

    if job_query:
        sql_query += " AND (j.JOB_TITLE LIKE ? OR j.COMPANY LIKE ?)"
        params.extend(["%" + job_query + "%", "%" + job_query + "%"])

    if sort_by == "oldest":
        sql_query += " ORDER BY j.ID ASC"
    else:
        sql_query += " ORDER BY j.ID DESC"

    cursor = get_db().execute(sql_query, tuple(params))
    data = cursor.fetchall()

    return render_template("saveds.html", data=data, query=job_query, sort=sort_by)


@app.route("/student/save/<int:job_id>", methods=["POST"])
def save_job(job_id):
    if "user_id" not in session or session["user_type"] != "student":
        return jsonify({"success": False, "error": "Authentication required"}), 401

    user_id = session["user_id"]
    db = get_db()
    try:
        db.execute(
            "INSERT INTO SAVED_JOBS (user_id, job_id) VALUES (?, ?)", (user_id, job_id)
        )
        db.commit()
        return jsonify({"success": True})
    except sqlite3.IntegrityError:
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/student/unsave/<int:job_id>", methods=["POST"])
def unsave_job(job_id):
    if "user_id" not in session or session["user_type"] != "student":
        return jsonify({"success": False, "error": "Authentication required"}), 401

    user_id = session["user_id"]
    db = get_db()
    try:
        db.execute(
            "DELETE FROM SAVED_JOBS WHERE user_id = ? AND job_id = ?", (user_id, job_id)
        )
        db.commit()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/employer")
def employer_home():
    job_query = request.args.get("query", "")
    sort_by = request.args.get("sort", "newest")
    data = get_approved_jobs(job_query, sort_by)
    return render_template(
        "employerhome.html", data=data, query=job_query, sort=sort_by
    )


@app.route("/employer/dashboard")
def employer_dashboard():
    if "user_id" not in session or session["user_type"] != "employer":
        return redirect("/signin")

    user_id = session["user_id"]
    db = get_db()

    cursor = db.execute(
        "SELECT COUNT(*) FROM JOBS WHERE USER_ID = ? AND APPROVED = 1", (user_id,)
    )
    total_active_listings = cursor.fetchone()[0]

    cursor = db.execute(
        "SELECT COUNT(*) FROM JOBS WHERE USER_ID = ? AND APPROVED = 0", (user_id,)
    )
    total_pending_listings = cursor.fetchone()[0]

    cursor = db.execute(
        """
        SELECT COUNT(a.ID)
        FROM APPLICATIONS a
        JOIN JOBS j ON a.job_id = j.ID
        WHERE j.USER_ID = ?
    """,
        (user_id,),
    )
    total_applications_received = cursor.fetchone()[0]

    cursor = db.execute(
        """
        SELECT u.username, j.JOB_TITLE
        FROM APPLICATIONS a
        JOIN JOBS j ON a.job_id = j.ID
        JOIN USERS u ON a.user_id = u.ID
        WHERE j.USER_ID = ?
        ORDER BY a.ID DESC
        LIMIT 5
    """,
        (user_id,),
    )
    recent_applications_employer = cursor.fetchall()

    return render_template(
        "employerdashboard.html",
        total_active_listings=total_active_listings,
        total_pending_listings=total_pending_listings,
        total_applications_received=total_applications_received,
        recent_applications_employer=recent_applications_employer,
    )


@app.route("/employer/post")
def go_employ():
    return render_template("employerpost.html")


@app.route("/employer/post", methods=["POST"])
def employer_post():
    if "user_id" not in session or session["user_type"] != "employer":
        flash("You must be logged in as an employer to post a job.", "error")
        return redirect("/signin")

    job_title = request.form.get("job-title")
    job_desc = request.form.get("job-description")
    company = request.form.get("company")
    email = request.form.get("email")
    user_id = session.get("user_id")

    file_name = "placeholder.webp"
    if "logo" in request.files and request.files["logo"].filename != "":
        logo_file = request.files["logo"]
        if logo_file and allowed_file(logo_file.filename, ALLOWED_LOGO_EXTENSIONS):
            filename = secure_filename(logo_file.filename)
            logo_file.save(os.path.join("static/images", filename))
            file_name = filename
        else:
            flash("Invalid logo file type. Allowed types are: png, jpg, jpeg, gif", "error")
            return redirect(request.url)

    db = get_db()
    try:
        db.execute(
            "INSERT INTO JOBS (JOB_TITLE, DESCRIPTION, COMPANY, LOGO, USER_ID, EMAIL) VALUES (?, ?, ?, ?, ?, ?)",
            (
                job_title,
                job_desc,
                company,
                file_name,
                user_id,
                email,
            ),
        )
        db.commit()
        flash(
            "Your job posting has been submitted for review and will be public once approved.", "success"
        )
    except Exception as e:
        flash(f"An error occurred: {e}", "error")
        db.rollback()

    return redirect("/employer/mypostings")


@app.route("/employer/mypostings")
def my_postings():
    if "user_id" not in session or session["user_type"] != "employer":
        return redirect("/signin")

    user_id = session["user_id"]
    job_query = request.args.get("query", "")
    job_filter = request.args.get("filter", "all")

    sql_query = "SELECT ID, JOB_TITLE, DESCRIPTION, COMPANY, LOGO, APPROVED FROM JOBS WHERE USER_ID = ?"
    params = [user_id]

    if job_filter == "approved":
        sql_query += " AND APPROVED = 1"
    elif job_filter == "pending":
        sql_query += " AND APPROVED = 0"

    if job_query:
        sql_query += " AND (JOB_TITLE LIKE ? OR COMPANY LIKE ?)"
        params.extend(["%" + job_query + "%", "%" + job_query + "%"])

    sql_query += " ORDER BY ID DESC"

    cursor = get_db().execute(sql_query, tuple(params))
    data = cursor.fetchall()

    return render_template(
        "employermypostings.html", data=data, query=job_query, filter=job_filter
    )

@app.route("/employer/viewapplications")
def view_applications():
    if "user_id" not in session or session["user_type"] != "employer":
        flash("You must be logged in as an employer to view applications.", "error")
        return redirect("/signin")

    user_id = session["user_id"]
    sort_by = request.args.get('sort', 'newest')
    db = get_db()

    cursor = db.execute("SELECT ID, JOB_TITLE FROM JOBS WHERE USER_ID = ? ORDER BY ID DESC", (user_id,))
    jobs = cursor.fetchall()

    jobs_with_applications = {}
    for job in jobs:
        order_clause = "ORDER BY a.ID DESC" if sort_by == 'newest' else "ORDER BY a.ID ASC"
        
        app_cursor = db.execute(f"""
            SELECT u.username, a.experience_summary, a.phone_number, a.contact_email, a.resume_filename
            FROM APPLICATIONS a
            JOIN USERS u ON a.user_id = u.ID
            WHERE a.job_id = ?
            {order_clause}
        """, (job['ID'],))
        applications = app_cursor.fetchall()
        
        jobs_with_applications[job] = applications

    return render_template("employerviewapplications.html", jobs_with_applications=jobs_with_applications, sort=sort_by)


@app.route("/admin")
def admin_home():
    job_query = request.args.get("query", "")
    sort_by = request.args.get("sort", "newest")
    data = get_approved_jobs(job_query, sort_by)
    return render_template("adminhome.html", data=data, query=job_query, sort=sort_by)


@app.route("/admin/dashboard")
def admin_dashboard():
    if "user_id" not in session or session["user_type"] != "admin":
        return redirect("/signin")

    db = get_db()

    cursor = db.execute("SELECT COUNT(*) FROM USERS")
    total_users = cursor.fetchone()[0]

    cursor = db.execute("SELECT COUNT(*) FROM JOBS WHERE APPROVED = 1")
    total_active_listings_admin = cursor.fetchone()[0]

    cursor = db.execute("SELECT COUNT(*) FROM JOBS WHERE APPROVED = 0")
    total_pending_jobs = cursor.fetchone()[0]

    cursor = db.execute(
        """
        SELECT u.username, j.JOB_TITLE, a.ID AS application_id
        FROM APPLICATIONS a
        JOIN USERS u ON a.user_id = u.ID
        JOIN JOBS j ON a.job_id = j.ID
        ORDER BY a.ID DESC
        LIMIT 5
    """
    )
    recent_job_applications = cursor.fetchall()

    cursor = db.execute("SELECT user_type, COUNT(*) FROM USERS GROUP BY user_type")
    user_stats = dict(cursor.fetchall())

    cursor = db.execute(
        "SELECT username, user_type FROM USERS ORDER BY ID DESC LIMIT 5"
    )
    recent_users = cursor.fetchall()

    return render_template(
        "admindashboard.html",
        total_users=total_users,
        total_active_listings_admin=total_active_listings_admin,
        total_pending_jobs=total_pending_jobs,
        recent_job_applications=recent_job_applications,
        user_stats=user_stats,
        recent_users=recent_users,
    )


@app.route("/admin/delete", methods=["POST"])
def delete_job():

    if "user_id" not in session or session["user_type"] != "admin":
        flash("You do not have permission to perform this action.")
        return redirect("/signin")

    post_id = request.form.get("post-id")

    if post_id:
        cursor = get_db().execute(
            "DELETE FROM JOBS WHERE ID=?",
            (post_id,),
        )

        if cursor.rowcount > 0:
            get_db().commit()
            flash("Job deleted successfully!")
        else:
            flash("Job not found or could not be deleted.")
    else:
        flash("No job ID provided for deletion.")

    return redirect("/admin")


@app.route("/admin/review")
def admin_review():
    job_query = request.args.get("query", "")
    sort_by = request.args.get("sort", "newest")

    sql_query = (
        "SELECT ID,JOB_TITLE,DESCRIPTION,COMPANY,LOGO FROM JOBS WHERE APPROVED=0"
    )
    params = []

    if job_query:
        sql_query += " AND (JOB_TITLE LIKE ? OR COMPANY LIKE ?)"
        params.extend(["%" + job_query + "%", "%" + job_query + "%"])

    if sort_by == "oldest":
        sql_query += " ORDER BY ID ASC"
    else:
        sql_query += " ORDER BY ID DESC"

    cursor = get_db().execute(sql_query, tuple(params))
    data = cursor.fetchall()
    return render_template(
        "adminapprove.html", data=data, query=job_query, sort=sort_by
    )


@app.route("/admin/deny", methods=["POST"])
def deny_job():

    if "user_id" not in session or session["user_type"] != "admin":
        flash("You do not have permission to perform this action.", "error")
        return redirect("/signin")

    post_id = request.form.get("deny-id")

    if post_id:
        cursor = get_db().execute("DELETE FROM JOBS WHERE ID=?", (post_id,))
        if cursor.rowcount > 0:
            get_db().commit()
            flash("Job denied and deleted successfully!", "success")
        else:
            flash("Job not found or could not be denied.", "error")
    else:
        flash("No job ID provided for denial.", "error")

    return redirect("/admin/review")


@app.route("/admin/approve", methods=["POST"])
def approve_job():

    if "user_id" not in session or session["user_type"] != "admin":
        flash("You do not have permission to perform this action.", "error")
        return redirect("/signin")

    post_id = request.form.get("approve-id")

    if post_id:
        cursor = get_db().execute(
            "UPDATE JOBS SET APPROVED=1 WHERE ID=?",
            (post_id,),
        )
        get_db().commit()
        flash("Job approved successfully!", "success")
    else:
        flash("No job ID provided for approval.", "error")

    return redirect("/admin/review")


@app.route("/")
def go_sign():
    return redirect("/signin")


@app.route("/signin", methods=["GET", "POST"])
def get_in():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        db = get_db()
        user = db.execute(
            "SELECT * FROM USERS WHERE username = ?", (username,)
        ).fetchone()

        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["ID"]
            session["username"] = user["username"]
            session["user_type"] = user["user_type"]

            if session["user_type"] == "student":
                return redirect("/student/dashboard")
            elif session["user_type"] == "employer":
                return redirect("/employer/dashboard")
            elif session["user_type"] == "admin":
                return redirect("/admin/dashboard")
        else:
            flash("Invalid username or password. Please try again.")
            return redirect("/signin")

    return render_template("signin.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "GET":
        return render_template("signup.html")

    username = request.form.get("username")
    password = request.form.get("password")
    repeated_password = request.form.get("repeat-password")
    user_type = request.form.get("user_type")

    if password != repeated_password:
        flash("Password doesn't match repeated password! Try again.")
        return redirect("/signup")

    assert user_type in ["employer", "student"]

    hashed_password = generate_password_hash(password)

    db = get_db()
    try:
        cur = db.execute(
            "INSERT INTO USERS (username, password, user_type) VALUES (?, ?, ?)",
            (username, hashed_password, user_type),
        )
        user_id = cur.lastrowid
        db.commit()
    except sqlite3.IntegrityError:
        flash("Username already taken. Please go back and try another.")
        return redirect("/signup")

    session.clear()
    session["user_id"] = user_id
    session["username"] = username
    session["user_type"] = user_type

    return redirect(f"/{user_type}/dashboard")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/signin")


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()


if __name__ == "__main__":
    app.run(debug=True)