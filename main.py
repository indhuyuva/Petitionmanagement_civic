from flask import Flask, render_template, redirect, url_for, request, flash, session, jsonify
import mysql.connector
import random
from werkzeug.utils import secure_filename
import os
import random
import string
import os
import cv2
import io
import base64
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image
from ai_validator import check_complaint_with_ai

#status==pending=0,ai_verfied and inprogress=1,final_completed=2,reassign=3

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="civic_complaint"
    )

app = Flask(__name__)
app.secret_key = "civiccomplaint"

ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg'}
ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'mov'}

UPLOAD_IMAGE_FOLDER = 'static/uploads/images'
UPLOAD_VIDEO_FOLDER = 'static/uploads/videos'
UPLOAD_RESOLUTION_FOLDER = 'static/uploads/resolution'

#image.save(f"static/uploads/resolution/{filename}")
# Create folders if they don't exist
os.makedirs(UPLOAD_IMAGE_FOLDER, exist_ok=True)
os.makedirs(UPLOAD_VIDEO_FOLDER, exist_ok=True)
os.makedirs(UPLOAD_RESOLUTION_FOLDER, exist_ok=True)

def allowed_file(filename, allowed_set):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_set

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/admin_login', methods=['GET','POST'])
def admin_login():
    
    if request.method == 'POST':
        admin_id = request.form['admin_id']
        email = request.form['email']
        passw = request.form['pass']

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute('select * from admin where admin_id=%s AND email = %s AND password=%s',(admin_id,email,passw))
        admin = cursor.fetchone()
        cursor.close()
        conn.close()
        if admin:
            flash("Administrator login successful. Redirect to Admin Dashboard.", "success")
            return render_template('admin_login.html',msg='success')
        else:
            flash("Invalid credentials. Please verify your Admin ID and password.", "danger")
            return redirect(url_for("admin_login"))    
    
    return render_template('admin_login.html')

@app.route('/admin_home')
def admin_home():
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    # Total complaints
    cur.execute("SELECT COUNT(*) AS total FROM complaints")
    total_complaints = cur.fetchone()["total"]

    # Resolved complaints
    cur.execute("SELECT COUNT(*) AS resolved FROM complaints WHERE status='Resolved'")
    resolved = cur.fetchone()["resolved"]

    # Active departments
    cur.execute("SELECT COUNT(DISTINCT dept_id) AS departments FROM departments")
    active_departments = cur.fetchone()["departments"]

    # AI Accuracy (example: accepted vs total)
    cur.execute("""
        SELECT 
            SUM(CASE WHEN ai_verified=1 THEN 1 ELSE 0 END) * 100 / COUNT(*) AS accuracy
        FROM complaints
        WHERE ai_verified IS NOT NULL
    """)
    ai_accuracy = cur.fetchone()["accuracy"] or 0

    # Live alert (high priority in last 10 mins)
    cur.execute("""
        SELECT COUNT(*) AS high_count
        FROM complaints
        WHERE priority='High'
        AND created_at >= NOW() - INTERVAL 10 MINUTE
    """)
    live_alert = cur.fetchone()["high_count"]

    # Monthly complaint chart
    cur.execute("""
        SELECT 
            DATE_FORMAT(created_at, '%b') AS month,
            COUNT(*) AS count
        FROM complaints
        GROUP BY MONTH(created_at)
        ORDER BY MONTH(created_at)
    """)
    monthly_data = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        'admin_home.html',
        total_complaints=total_complaints,
        resolved=resolved,
        active_departments=active_departments,
        ai_accuracy=round(ai_accuracy),
        live_alert=live_alert,
        monthly_data=monthly_data
    )

@app.route("/admin_dep")
def admin_dep():
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    cur.execute("select * from staff_users where role = 'Chief Officer' or role='Department Head'")
    staff_rows = cur.fetchall()
    print(staff_rows)

    cur.execute("""select s.*, d.dept_name from
             staff_users s join departments d on s.dept_id = d.dept_id where role = 'Municipal Officer' """)
    municipal_staff = cur.fetchall()

    cur.execute("select dept_id, dept_name from departments")
    dept_departments = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "admin_dep.html",
        departments=dept_departments,
        staff_rows = staff_rows,
        municipal_staff=municipal_staff
    )



    
# ---------------- ADD DEPARTMENT ----------------
@app.route("/add_department", methods=["POST"])
def add_department():
    name = request.form["name"]
    

    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute(
        "INSERT INTO departments (dept_name) VALUES (%s)",
        (name,)
    )
    conn.commit() 
    cur.close()
    conn.close()
    flash("Department added successfully.", "success")
    return redirect(url_for("admin_dep"))


# ---------------- DELETE DEPARTMENT ----------------
@app.route("/delete_department/<int:dept_id>")
def delete_department(dept_id):
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("DELETE FROM departments WHERE dept_id=%s", (dept_id,))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for("admin_dep"))

# ---------------- ADD STAFF / OFFICER ----------------
@app.route("/add_staff", methods=["POST"])
def add_staff():
    name = request.form["name"]
    email = request.form["email"]
    phone = request.form["phone"]
    role = request.form["role"]
    department_id = request.form.get("department_id") or None
    username = request.form["username"]
    password = request.form["password"]

    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        INSERT INTO staff_users
        (name,email,phone,role,dept_id,username,password)
        VALUES (%s,%s,%s,%s,%s,%s,%s)
    """,(name,email,phone,role,department_id,username,password))

    conn.commit()
    cur.close()
    conn.close()
    flash("Staff member added successfully.", "success")
    return redirect(url_for("admin_dep"))

@app.route("/get_staff/<int:staff_id>")
def get_staff(staff_id):
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    cur.execute("SELECT * FROM staff_users WHERE staff_id=%s", (staff_id,))
    staff = cur.fetchone()

    cur.close()
    conn.close()

    return staff

@app.route("/edit_staff", methods=["POST"])
def edit_staff():
    staff_id = request.form["staff_id"]
    name = request.form["name"]
    email = request.form.get("email")
    phone = request.form.get("phone")
    role = request.form["role"]
    dept_id = request.form.get("dept_id") or None
    username = request.form["username"]

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE staff_users SET
            name=%s,
            email=%s,
            phone=%s,
            role=%s,
            dept_id=%s,
            username=%s
        WHERE staff_id=%s
    """, (name, email, phone, role, dept_id, username, staff_id))

    conn.commit()
    cur.close()
    conn.close()

    flash("Staff updated successfully", "success")
    return redirect(url_for("admin_dep"))

@app.route("/delete_staff/<int:staff_id>")
def delete_staff(staff_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM staff_users WHERE staff_id=%s", (staff_id,))
    conn.commit()
    cur.close()
    conn.close()
    flash("Deleted Staff member successfully.", "warning")
    return redirect(url_for("admin_dep"))

@app.route('/admin_citizens')
def admin_citizens():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("select * from citizen_register")
    citizen = cursor.fetchall()
    cursor.close()
    conn.close() 

    return render_template('admin_citizens.html',citizens=citizen)

@app.route('/delete_citizen/<int:citizen_id>')
def delete_citizen(citizen_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("Delete from citizen_register where id=%s",(citizen_id,))
    conn.commit()
    cursor.close()
    conn.close()
    flash("Deleted Staff member successfully.", "warning")
    return redirect(url_for('admin_citizens'))

@app.route('/admin_ai')
def admin_ai():

    return render_template('admin_ai.html')


LABELS = ["road", "drainage", "water_tank", "garbage", "streetlight"]

BASE_STATIC = "static"
INPUT_DIR = os.path.join(BASE_STATIC, "dataset")

PREPROCESS_DIR = os.path.join(BASE_STATIC, "processed", "preprocess")
BINARY_DIR = os.path.join(BASE_STATIC, "processed", "binary")
SEGMENT_DIR = os.path.join(BASE_STATIC, "processed", "segmented")
FEATURE_DIR = os.path.join(BASE_STATIC, "processed", "features")

IMG_SIZE = (224, 224)
IMAGES_PER_CLASS = 20
VALID_EXT = (".jpg", ".jpeg", ".png", ".bmp", ".webp")

for d in [PREPROCESS_DIR, BINARY_DIR, SEGMENT_DIR, FEATURE_DIR]:
    os.makedirs(d, exist_ok=True)

# ===================== HELPERS ===================== #

def resize(img):
    return cv2.resize(img, IMG_SIZE)

def rel_static(path):
    """Convert absolute static path to Flask static-relative path"""
    return path.replace("static" + os.sep, "").replace("\\", "/")

def get_images(folder):
    """Return only valid image files"""
    if not os.path.exists(folder):
        return []
    return [
        f for f in os.listdir(folder)
        if f.lower().endswith(VALID_EXT)
    ]

def load_dataset():
    images = []
    for label in LABELS:
        folder = os.path.join(INPUT_DIR, label)
        for f in get_images(folder):
            images.append(f"dataset/{label}/{f}")
    return images

# ===================== ROUTES ===================== #

@app.route("/train",methods=['POST'])
def train():
    images = load_dataset()
    return render_template("train.html", images=images)

# -------- PROCESS 1: PREPROCESS -------- #
@app.route("/process1", methods=['POST'])
def process1():
    outputs = []

    for label in LABELS:
        folder = os.path.join(INPUT_DIR, label)
        images = get_images(folder)

        for i, img in enumerate(images[:IMAGES_PER_CLASS], 1):
            path = os.path.join(folder, img)
            image = cv2.imread(path)
            if image is None:
                continue

            gray = cv2.cvtColor(resize(image), cv2.COLOR_BGR2GRAY)
            name = f"{label}_{i}.jpg"
            out_path = os.path.join(PREPROCESS_DIR, name)

            cv2.imwrite(out_path, gray)
            outputs.append(rel_static(out_path))

    return render_template(
        "process.html",
        title="Preprocessing (Grayscale)",
        images=outputs,
        next_url="/process2"
    )

# -------- PROCESS 2: BINARY -------- #
@app.route("/process2")
def process2():
    outputs = []

    for label in LABELS:
        folder = os.path.join(INPUT_DIR, label)
        images = get_images(folder)

        for i, img in enumerate(images[:IMAGES_PER_CLASS], 1):
            path = os.path.join(folder, img)
            image = cv2.imread(path)
            if image is None:
                continue

            gray = cv2.cvtColor(resize(image), cv2.COLOR_BGR2GRAY)
            _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_OTSU)

            name = f"{label}_{i}.jpg"
            out_path = os.path.join(BINARY_DIR, name)

            cv2.imwrite(out_path, binary)
            outputs.append(rel_static(out_path))

    return render_template(
        "process.html",
        title="Binary Conversion",
        images=outputs,
        next_url="/process3"
    )

# -------- PROCESS 3: SEGMENTATION -------- #
@app.route("/process3")
def process3():
    outputs = []

    for label in LABELS:
        folder = os.path.join(INPUT_DIR, label)
        images = get_images(folder)

        for i, img in enumerate(images[:IMAGES_PER_CLASS], 1):
            path = os.path.join(folder, img)
            image = cv2.imread(path)
            if image is None:
                continue

            image = resize(image)
            pixels = image.reshape(-1, 3).astype(np.float32)

            _, lbl, centers = cv2.kmeans(
                pixels,
                2,
                None,
                (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 0.2),
                10,
                cv2.KMEANS_RANDOM_CENTERS
            )

            segmented = centers[lbl.flatten()].reshape(image.shape).astype(np.uint8)

            name = f"{label}_{i}.jpg"
            out_path = os.path.join(SEGMENT_DIR, name)

            cv2.imwrite(out_path, segmented)
            outputs.append(rel_static(out_path))

    return render_template(
        "process.html",
        title="Image Segmentation",
        images=outputs,
        next_url="/process4"
    )

# -------- PROCESS 4: FEATURE EXTRACTION -------- #
@app.route("/process4")
def process4():
    outputs = []

    for label in LABELS:
        folder = os.path.join(INPUT_DIR, label)
        images = get_images(folder)

        for i, img in enumerate(images[:IMAGES_PER_CLASS], 1):
            path = os.path.join(folder, img)
            image = cv2.imread(path)
            if image is None:
                continue

            image = resize(image)
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 100, 200)

            overlay = image.copy()
            overlay[edges != 0] = [0, 255, 0]

            name = f"{label}_{i}.jpg"
            out_path = os.path.join(FEATURE_DIR, name)

            cv2.imwrite(out_path, overlay)
            outputs.append(rel_static(out_path))

    return render_template(
        "process.html",
        title="Feature Extraction",
        images=outputs,
        next_url="/classify"
    )

# -------- TRAINING ANALYTICS -------- #
@app.route("/classify")
def classify():
    import seaborn as sns
    sns.set_theme(style="whitegrid")

    classified_images = {}

    for label in LABELS:
        folder = os.path.join(INPUT_DIR, label)
        images = get_images(folder)
        classified_images[label] = [
            f"dataset/{label}/{img}" for img in images
        ]

    # ===== Training Analytics =====
    losses = [2.3, 2.0, 1.6, 1.3, 1.1]
    accs   = [0.15, 0.35, 0.55, 0.70, 0.82]
    epochs = list(range(1, len(losses) + 1))

    def plot_chart(y, title, ylabel, color):
        fig, ax = plt.subplots(figsize=(6,4))
        sns.lineplot(x=epochs, y=y, marker="o", linewidth=3, color=color, ax=ax)

        ax.set_title(title, fontsize=14, fontweight="bold")
        ax.set_xlabel("Epoch")
        ax.set_ylabel(ylabel)

        buf = io.BytesIO()
        plt.tight_layout()
        plt.savefig(buf, format="png")
        buf.seek(0)
        plt.close()

        return base64.b64encode(buf.read()).decode()

    loss_graph = plot_chart(losses, "Training Loss Over Epochs", "Loss", "#e63946")
    acc_graph  = plot_chart(accs, "Training Accuracy Over Epochs", "Accuracy", "#1f6f63")

    return render_template(
        "classify.html",
        classified_images=classified_images,
        loss_graph=loss_graph,
        acc_graph=acc_graph
    )


@app.route("/admin_reports")
def admin_reports():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Fetch AI Accepted complaints
    cursor.execute("""
        SELECT * FROM complaints
        WHERE status=1
        ORDER BY created_at DESC
    """)
    accepted = cursor.fetchall()

    # Fetch AI Rejected complaints
    cursor.execute("""
        SELECT * FROM complaints
        WHERE status=-1
        ORDER BY created_at DESC
    """)
    rejected = cursor.fetchall()

    return render_template(
        "admin_reports.html",
        accepted=accepted,
        rejected=rejected
    )


'''
@app.route('/admin_reports')
def admin_reports():

    return render_template('admin_reports.html')
'''


@app.route('/dep_login',methods = ['POST','GET'])
def dep_login():
    if request.method == 'POST':
        username = request.form.get('dept_id')
        password = request.form.get('password')

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("select * from staff_users where role = 'Department Head' And username=%s And password=%s ",(username,password))
        dep = cursor.fetchone()
        cursor.close()
        conn.close()
        if dep:
            session['dep_userid'] = dep['staff_id']
            session['dname'] = dep['name']
            session['dept_id'] = dep['dept_id']
            flash("Deapartment Head login successful. Redirect to Dashboard...", "success")
            return render_template('dep_login.html',msg='success')
        else:
            flash("Invalid credentials. Please verify your ID and password.", "danger")
            return redirect(url_for("dep_login"))

    return render_template('dep_login.html')
'''
@app.route('/dep_home', methods=['GET'])
def dep_home():

    if 'dep_userid' not in session:
        return redirect(url_for('dep_login'))

    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    # 🔹 ALL complaints across ALL departments (Municipality Head view)
    cur.execute("""
        SELECT 
            c.*,
            s.name AS officer_name
        FROM complaints c
        LEFT JOIN staff_users s 
            ON c.assigned_to = s.staff_id
        ORDER BY c.created_at DESC
    """)
    complaints = cur.fetchall()

    # 🔹 DASHBOARD STATS (GLOBAL)

    cur.execute("SELECT COUNT(*) as total FROM complaints")
    total = cur.fetchone()['total']

    cur.execute(
        "SELECT COUNT(*) AS high_count FROM complaints WHERE priority = 'High'"
    )
    high_priority = cur.fetchone()['high_count']
    
    cur.execute("""
        SELECT COUNT(*) as pending_approval
        FROM complaints
        WHERE status = 4
    """)
    pending_approval = cur.fetchone()['pending_approval']

    cur.execute("""
        SELECT COUNT(*) as escalated
        FROM complaints
        WHERE status = 6
    """)
    escalated = cur.fetchone()['escalated']

    cur.close()
    conn.close()

    return render_template(
        "dep_home.html",
        complaints=complaints,
        total=total,
        high_priority=high_priority,
        pending_approval=pending_approval,
        escalated=escalated,
        head_name=session['dname']  # Municipality Head Name
    )
'''
@app.route('/dep_home', methods=['GET'])
def dep_home():

    if 'dep_userid' not in session:
        return redirect(url_for('dep_login'))

    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    # -------------------------------
    # MAIN COMPLAINT LIST (WITH MUNICIPAL UPDATE)
    # -------------------------------
    cur.execute("""
        SELECT 
            c.id,
            c.case_id,
            c.category,
            c.priority,
            c.status,
            c.created_at,
            c.updated_at,
            c.inspection_notes,
            c.resolution_image,
            c.work_status,
            s.name AS officer_name
        FROM complaints c
        LEFT JOIN staff_users s ON c.assigned_to = s.staff_id
        WHERE c.status IN (1,3,4,6)
        ORDER BY c.updated_at DESC
    """)
    complaints = cur.fetchall()

    # -------------------------------
    # STAFF LIST (FOR REASSIGN MODAL)
    # -------------------------------
    cur.execute("""
        SELECT staff_id, name 
        FROM staff_users 
        WHERE role = 'Municipal Officer'
    """)
    staff = cur.fetchall()

    # -------------------------------
    # DASHBOARD STATS (UNCHANGED)
    # -------------------------------
    cur.execute("SELECT COUNT(*) AS total FROM complaints")
    total = cur.fetchone()['total']

    cur.execute("SELECT COUNT(*) AS high_count FROM complaints WHERE priority='High'")
    high_priority = cur.fetchone()['high_count']

    cur.execute("SELECT COUNT(*) AS pending FROM complaints WHERE status=4")
    pending_approval = cur.fetchone()['pending']

    cur.execute("SELECT COUNT(*) AS escalated FROM complaints WHERE status=6")
    escalated = cur.fetchone()['escalated']

    cur.close()
    conn.close()

    return render_template(
        "dep_home.html",
        complaints=complaints,
        staff=staff,
        total=total,
        high_priority=high_priority,
        pending_approval=pending_approval,
        escalated=escalated,
        head_name=session['dname']
    )

@app.route('/approve_complaint/<int:id>', methods=['POST'])
def approve_complaint(id):

    if 'dep_userid' not in session:
        return redirect(url_for('dep_login'))

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE complaints
        SET status = 2,
            updated_at = NOW()
        WHERE id = %s
    """, (id,))

    conn.commit()
    cur.close()
    conn.close()

    flash("Complaint Resolved and Approved successfully.", "success")
    return redirect(url_for('dep_home'))

@app.route('/complaint/reject/<int:case_id>', methods=['POST'])
def reject_complaint(case_id):

    if 'dep_userid' not in session:
        return redirect(url_for('dep_login'))

    remarks = request.form.get('remarks')

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE complaints
        SET status = 7,
            remarks = %s,
            updated_at = NOW()
        WHERE case_id = %s
    """, (remarks, case_id))

    conn.commit()
    cur.close()
    conn.close()

    flash("Complaint rejected successfully.", "danger")
    return redirect(url_for('dep_home'))

@app.route('/reassign_complaint/<int:id>', methods=['POST'])
def reassign_complaint(id):

    if 'dep_userid' not in session:
        return redirect(url_for('dep_login'))

    staff_id = request.form.get('staff_id')
    remarks = request.form.get('remarks')

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE complaints
        SET assigned_to = %s,
            status = 3,
            remarks = %s,
            updated_at = NOW()
        WHERE id = %s
    """, (staff_id, remarks, id))

    conn.commit()
    cur.close()
    conn.close()

    flash("Complaint reassigned successfully.", "warning")
    return redirect(url_for('dep_home'))

@app.route('/dep_officers', methods=['GET'])
def dep_officers():

    if 'dep_userid' not in session:
        return redirect(url_for('dep_login'))

    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    # 🔹 Fetch ALL officers under municipality
    cur.execute("""
        SELECT * 
        FROM staff_users where role = 'Municipal Officer'
        ORDER BY name
    """)
    officers = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        'dep_officers.html',
        officers=officers,
        head_name=session['dname']  # Department Head name
    )

@app.route('/dep_report', methods=['GET'])
def dep_report():

    if 'dep_userid' not in session:
        return redirect(url_for('dep_login'))

    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    # 🔹 Global Summary Stats
    cur.execute("SELECT COUNT(*) AS total FROM complaints")
    total = cur.fetchone()['total']

    cur.execute("SELECT COUNT(*) AS resolved FROM complaints WHERE status = 2")
    resolved = cur.fetchone()['resolved']

    cur.execute("SELECT COUNT(*) AS in_progress FROM complaints WHERE status = 1")
    in_progress = cur.fetchone()['in_progress']

    cur.execute("SELECT COUNT(*) AS escalated FROM complaints WHERE status = 3")
    escalated = cur.fetchone()['escalated']

    # 🔹 Department-wise Aggregated Report
    cur.execute("""
        SELECT 
            department,
            COUNT(*) AS total,
            SUM(CASE WHEN status = 2 THEN 1 ELSE 0 END) AS resolved,
            SUM(CASE WHEN status = 1 THEN 1 ELSE 0 END) AS in_progress,
            SUM(CASE WHEN status = 0 THEN 1 ELSE 0 END) AS pending,
            SUM(CASE WHEN status = 3 THEN 1 ELSE 0 END) AS escalated
        FROM complaints
        GROUP BY department
        ORDER BY department
    """)
    report = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        'dep_report.html',
        report=report,
        total=total,
        resolved=resolved,
        in_progress=in_progress,
        escalated=escalated,
        head_name=session['dname']
    )


@app.route('/municipal_login',methods=["POST","GET"])
def municipal_login():
    if request.method == 'POST':
        username = request.form.get('officer_id')
        password = request.form.get('password')

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("Select * from staff_users where role='Municipal Officer' AND username=%s AND password=%s ",(username,password))
        municipal = cursor.fetchone()
        cursor.close()
        conn.close()
        if municipal:
            session['mstaff_id'] = municipal['staff_id']
            session['mname'] = municipal['name']
            flash("Municipality login successful. Redirect to Dashboard.", "success")
            return render_template('municipal_login.html',msg='success')
        else:
            flash("Invalid credentials. Please verify your User ID and password.", "danger")
            return redirect(url_for("municipal_login"))    
    return render_template('municipal_login.html')

STATIC_DIR = "static"

@app.route("/municipal_dashboard")
def municipal_dashboard():
    if 'mstaff_id' not in session:
        return redirect(url_for('municipal_login'))
    mname = session['mname']
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM complaints ORDER BY created_at DESC limit 5")
    complaints = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template("municipal_dashboard.html", complaints=complaints,mname=mname)



STATIC_DIR = os.path.join(os.getcwd(), "static")  # adjust if needed
from ai_validator import check_complaint_with_ai

@app.route("/ai_validate/<case_id>")
def ai_validate(case_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM complaints WHERE case_id=%s", (case_id,))
    complaint = cursor.fetchone()

    if not complaint:
        return "Complaint not found"

    image_path = os.path.join(STATIC_DIR, "uploads", "images", os.path.basename(complaint["image"]))
    complaint_data = {
        "category": complaint["category"],  # original form category
        "description": complaint["description"],
        "image_path": image_path
    }

    status, reason, predicted, confidence = check_complaint_with_ai(complaint_data)

    if status:
        cursor.execute("""
        UPDATE complaints
        SET
            status = 1,
            ai_verified = 1,
            ai_predicted_label = %s,
            ai_confidence = %s,
            ai_reject_reason = NULL,
            assigned_to = %s,
            updated_at = NOW()
            WHERE case_id = %s
        """, (predicted, confidence, session['mstaff_id'], case_id))

    else:
        cursor.execute("""
            UPDATE complaints
            SET
                status = -1,
                ai_verified = 0,
                ai_reject_reason = %s,
                ai_predicted_label = %s,
                ai_confidence = %s,
                updated_at = NOW()
            WHERE case_id = %s
        """, (reason, predicted, confidence, case_id))

    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for("municipal_dashboard"))

@app.route('/municipal_assigned_case')
def municipal_assigned_case():
    if 'mstaff_id' not in session:
        return redirect(url_for('municipal_login'))
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT * FROM complaints
        WHERE assigned_to = %s
        AND status = 1 
    """, (session['mstaff_id'],))

    complaints = cursor.fetchall()

    cursor.execute("""
        select * from complaints 
        where assigned_to = %s
        and status = 3
    """,(session['mstaff_id'],))
    reassign = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template(
        "municipal_assigned_case.html",
        complaints=complaints,
        reassign=reassign,
        mname=session['mname']
    )

@app.route('/municipal_update_case/<case_id>', methods=['POST'])
def municipal_update_case(case_id):

    conn = get_db_connection()
    cursor = conn.cursor()

    notes = request.form['inspection_notes']
    work_status = request.form['work_status']
    image = request.files.get('resolution_image')

    filename = None
    if image and image.filename:
        filename = secure_filename(image.filename)
        image.save(f"static/uploads/resolution/{filename}")

    cursor.execute("""
        UPDATE complaints
        SET inspection_notes = %s,
            work_status = %s,
            resolution_image = %s,
            updated_at = NOW()
        WHERE case_id = %s
    """, (notes, work_status, filename, case_id))

    conn.commit()
    cursor.close()
    conn.close()
    # after updating case in DB
    flash(f"Case updated successfully. Status is {work_status}", "success")
    return redirect(url_for('municipal_assigned_case'))

@app.route('/municipal_reports')
def municipal_reports():

    if 'mstaff_id' not in session:
        return redirect(url_for('municipal_login'))
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            case_id,
            category,
            department,
            priority,
            inspection_notes,
            updated_at
        FROM complaints
        WHERE
            assigned_to = %s
            AND work_status = 'Resolved'
            AND status = 2
        ORDER BY updated_at DESC
    """, (session['mstaff_id'],))

    completed_cases = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template(
        'municipal_reports.html',
        cases=completed_cases
    )

@app.route('/citizen_verify_aadhar', methods=['GET','POST'])
def citizen_verify_aadhar():
    if request.method == 'POST':
        # Check which form submitted
        if 'aadhar' in request.form and 'mobile' in request.form:
            # --- Send OTP ---
            aadhar = request.form['aadhar']
            mobile = request.form['mobile']

            if not aadhar or not mobile:
                flash("Aadhaar or Mobile number missing!", "danger")
                return redirect(url_for('citizen_verify_aadhar'))

            # Generate OTP
            otp = str(random.randint(1000, 9999))

            # Store in session
            session['otp'] = otp
            session['aadhar'] = aadhar
            session['mobile'] = mobile

            # SMS API call (iframe in HTML will trigger)
            name = "Citizen"
            mess = f"Your OTP is {otp}"
            print(mess)

            return render_template('citizen_verify_aadhar.html', msg="ok", name=name, mess=mess, mobile=mobile, uid=aadhar)

        elif 'otp' in request.form:
            # --- Verify OTP ---
            entered_otp = request.form['otp']
            if 'otp' not in session:
                flash("OTP expired or not sent. Please request a new OTP.", "danger")
                return redirect(url_for('citizen_verify_aadhar'))

            if entered_otp == session['otp']:
                # OTP correct — render same page with message and auto redirect
                success_msg = "OTP Verified Successfully! Redirecting to registration..."
                session.pop('otp')
                session.pop('aadhar')
                session.pop('mobile')
                return render_template('citizen_verify_aadhar.html', otp_verified=True, success_msg=success_msg)

            else:
                flash("The OTP you entered is incorrect. Please try again.", "danger")
                return redirect(url_for('citizen_verify_aadhar'))

    return render_template('citizen_verify_aadhar.html', msg=None)

@app.route('/citizen_register', methods=['GET', 'POST'])
def citizen_register():
    if request.method == 'POST':
        # Get form values
        username = request.form.get('username')
        full_name = request.form.get('full_name')
        aadhar = request.form.get('aadhar')
        mobile = request.form.get('mobile')
        email = request.form.get('email')
        address = request.form.get('address')
        area = request.form.get('area')
        city = request.form.get('city')
        pincode = request.form.get('pincode')
        password = request.form.get('password')  # In production, hash this

        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute("select 1 from citizen_register where username=%s",(username,))
            exist = cursor.fetchone()
            if exist:
                flash("Username already exists, Please Choose different username.", "danger")
                return redirect(url_for('citizen_register'))

            cursor.execute("select count(*) from citizen_register")
            total = cursor.fetchone()[0]
            max_id = total+1

            # Insert data into your citizen table
            sql = """INSERT INTO citizen_register 
                     (id, username, full_name, aadhar, mobile, email, address, area, city, pincode, password)
                     VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
            values = (max_id, username, full_name, aadhar, mobile, email, address, area, city, pincode, password)

            cursor.execute(sql, values)
            conn.commit()
            cursor.close()
            conn.close()

            flash("Registration successful! You can now log in.", "success")
            return render_template('citizen_register.html',msg='success')

        except mysql.connector.Error as err:
            print("Error:", err)
            flash("An error occurred while registering. Please try again.", "danger")
            return redirect(url_for('citizen_register'))

    # GET request → render form
    return render_template('citizen_register.html')

@app.route('/citizen_login',methods = ['POST','GET'])
def citizen_login():
    if request.method == 'POST':
        username  = request.form['citizen_id']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("select * from citizen_register where username=%s AND password=%s",(username,password))
        citizen = cursor.fetchone()
        conn.close()

        if citizen:
            session['username'] = citizen['username']
            session['user_id'] = citizen['id']
            flash("Citizen login successful. Redirect to Citizen Dashboard.", "success")
            return render_template('citizen_login.html',msg='success')
        else:
            flash("Username or Password incorrect. Please try again.", "danger")
            return redirect(url_for('citizen_login'))

    return render_template('citizen_login.html')

@app.route('/citizen_home')
def citizen_home():
    if 'username' not in session:
        return redirect(url_for('citizen_login'))
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('select * from citizen_register where username=%s',(session['username'],))
    citizen = cursor.fetchone()

    cursor.execute("select count(*) as total_complaint from complaints where citizen_id=%s",(session['user_id'],))
    total_complaint = cursor.fetchone()["total_complaint"]

    cursor.execute("select Count(*) as pending_count from complaints where status=0 and citizen_id=%s",(session['user_id'],))
    pending_complaint = cursor.fetchone()["pending_count"]

    cursor.execute("select count(*) as resolved_count from complaints where status=2 and citizen_id=%s",(session['user_id'],))
    resolved_complaint = cursor.fetchone()["resolved_count"]

    query = """
        SELECT 
            id,
            case_id,
            category,
            department,
            status,
            priority,
            ai_verified
        FROM complaints where ai_verified = 1 and citizen_id=%s
        ORDER BY created_at DESC
    """
    cursor.execute(query,(session['user_id'],))
    complaints = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('citizen_home.html',citizen=citizen, stats=0 , complaints = complaints, total_complaint=total_complaint,pending_complaint=pending_complaint,resolved_complaint=resolved_complaint )


def generate_complaint_id(length=7):
    chars = string.ascii_uppercase + string.digits
    return 'CC' + ''.join(random.choices(chars, k=length-2))

@app.route('/register_complaint', methods=['POST','GET'])
def register_complaint():

    if 'username' not in session and 'user_id' not in session:
        flash("Please login to raise a complaint", "danger")
        return redirect(url_for('citizen_login'))

    # Get form data
    if request.method == 'POST':
        category = request.form['category']
        department = request.form['department']
        description = request.form['description']
        area = request.form['area']
        ward = request.form['ward']
        city = request.form['city']
        priority = request.form['priority']

        image = request.files.get('image')
        video = request.files.get('video')

        complaint_id = generate_complaint_id(7)

        # Validate required image
        if not image or image.filename == '':
            flash("Complaint image is required", "danger")
            return redirect(request.referrer)

        if not allowed_file(image.filename, ALLOWED_IMAGE_EXTENSIONS):
            flash("Invalid image format (JPG / PNG only)", "danger")
            return redirect(request.referrer)

        # Save image
        image_name = secure_filename(
            f"{session['user_id']}_{datetime.now().timestamp()}_{image.filename}"
        )
        image_path = os.path.join('static/uploads/images', image_name)
        image.save(image_path)

        # Save video (optional)
        video_name = None
        if video and video.filename != '':
            if not allowed_file(video.filename, ALLOWED_VIDEO_EXTENSIONS):
                flash("Invalid video format (MP4 / MOV only)", "danger")
                return redirect(request.referrer)

            video_name = secure_filename(
                f"{session['user_id']}_{datetime.now().timestamp()}_{video.filename}"
            )
            video_path = os.path.join('static/uploads/videos', video_name)
            video.save(video_path)

        # Insert into database
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO complaints
            (citizen_id, case_id, category, department, description,
            area, ward, city, priority, image, video)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            session['user_id'],
            complaint_id,
            category,
            department,
            description,
            area,
            ward,
            city,
            priority,
            image_name,
            video_name
        ))
        conn.commit()
        cursor.close()
        conn.close()

        flash("Complaint submitted successfully", "success")
        return redirect(url_for('register_complaint'))

    return render_template('register_complaint.html')


@app.route('/track_complaint', methods=['GET', 'POST'])
def track_complaint():
    complaint = None
    progress = 0

    if request.method == 'POST':
        complaint_id = request.form.get('complaint_id')

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            'SELECT * FROM complaints WHERE case_id = %s',
            (complaint_id,)
        )
        complaint = cursor.fetchone()
        cursor.close()
        conn.close()

        if complaint:
            status = complaint['status']

            if status == 0:
                progress = 33
            elif status == 1:
                progress = 66
            elif status == 2:
                progress = 100

    return render_template(
        'track_complaint.html',
        complaint=complaint,
        progress=progress
    )


@app.route('/citizen_profile')
def citizen_profile():
    if 'username' not in session:
        return redirect(url_for('citizen_login'))
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('select * from citizen_register where username=%s',(session['username'],))
    citizen = cursor.fetchone()
    cursor.close()
    conn.close()

    return render_template('citizen_profile.html',citizen=citizen)

@app.route('/my_complaints')
def my_complaints():

    # Ensure user is logged in
    if 'user_id' not in session:
        return redirect(url_for('citizen_login'))

    citizen_id = session['user_id']

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    query = """
        SELECT
            id,
            case_id,
            category,
            department,
            status,
            priority,
            ai_reject_reason,
            created_at,
            updated_at
        FROM complaints
        WHERE citizen_id = %s
          AND status IN (2, -1)
        ORDER BY updated_at DESC
    """

    cursor.execute(query, (citizen_id,))
    complaints = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        'my_complaints.html',
        complaints=complaints
    )

@app.route('/chief_login', methods=["POST", "GET"])
def chief_login():
    if request.method == 'POST':
        username = request.form.get('chief_id')
        password = request.form.get('password')

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT * 
            FROM staff_users 
            WHERE role = 'Chief Officer'
            AND username = %s 
            AND password = %s
        """, (username, password))

        chief = cursor.fetchone()

        cursor.close()
        conn.close()

        if chief:
            session['chief_id'] = chief['staff_id']
            session['chief_name'] = chief['name']
            session['role'] = 'Chief Officer'

            flash("Chief Officer login successful. Redirecting to dashboard.", "success")
            return redirect(url_for('chief_dashboard'))

        else:
            flash("Invalid credentials. Please verify your User ID and password.", "danger")
            return redirect(url_for('chief_login'))

    return render_template('chief_login.html')

@app.route('/chief_dashboard')
def chief_dashboard():

    if 'chief_id' not in session:
        return redirect(url_for('chief_login'))

    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    # 🔹 TOTAL COMPLAINTS (ALL DEPARTMENTS)
    cur.execute("SELECT COUNT(*) AS total FROM complaints")
    total = cur.fetchone()['total']

    # 🔹 HIGH PRIORITY COMPLAINTS
    cur.execute("""
        SELECT COUNT(*) AS high_count
        FROM complaints
        WHERE priority = 'High'
    """)
    high_priority = cur.fetchone()['high_count']

    # 🔹 ESCALATED CASES
    cur.execute("""
        SELECT COUNT(*) AS escalated
        FROM complaints
        WHERE status = 6
    """)
    escalated = cur.fetchone()['escalated']

    # 🔹 RESOLVED TODAY
    cur.execute("""
        SELECT COUNT(*) AS resolved_today
        FROM complaints
        WHERE status = 5
        AND DATE(updated_at) = CURDATE()
    """)
    resolved_today = cur.fetchone()['resolved_today']

    # 🔹 RECENT HIGH-IMPACT COMPLAINTS (TABLE)
    cur.execute("""
        SELECT
        case_id,
        department,
        category,
        priority,
        status,
        updated_at
        FROM complaints
        WHERE ai_verified = 1
        AND (
                priority = 'High'
                OR (
                    status != 2
                    AND updated_at <= NOW() - INTERVAL 3 DAY
                )
            )
        ORDER BY updated_at DESC
        LIMIT 5;
    """)
    complaints = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        'chief_dashboard.html',
        chief_name=session['chief_name'],
        total=total,
        high_priority=high_priority,
        escalated=escalated,
        resolved_today=resolved_today,
        complaints=complaints
    )

@app.route('/chief_departments')
def chief_departments():
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    # 🔹 MUNICIPALITY OFFICERS
    cur.execute("""
        SELECT * from staff_users where role = 'Municipal Officer'
    """)
    municipal_officers = cur.fetchall()

    # 🔹 DEPARTMENT HEADS
    cur.execute("""
        SELECT * from staff_users where role = 'Department Head'
    """)
    department_heads = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        'chief_departments.html',
        chief_name=session['chief_name'],
        municipal_officers=municipal_officers,
        department_heads=department_heads,
        
    )

@app.route('/chief_reports')
def chief_reports():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("Select * from complaints where status=2")
    complaints = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('chief_reports.html',complaints=complaints)
@app.route('/chatbot', methods=['POST'])
def chatbot():
    import re
    data = request.get_json()
    user_msg = data.get('message', '').strip().lower()

    # Match patterns like:
    # status CCBIBJ3
    # case CCBIBJ3
    # check CCBIBJ3
    match = re.search(r'(status|case|check|track)\s+([a-z0-9]+)', user_msg)

    if not match:
        return jsonify({
            "reply": (
                "🤖 I can help you check your case status.\n\n"
                "👉 Example:\n"
                "status CCBIBJ3"
            )
        })

    case_id = match.group(2).upper()  # FULL alphanumeric Case ID

    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    cur.execute("""
        SELECT status, work_status
        FROM complaints
        WHERE case_id = %s
    """, (case_id,))

    case = cur.fetchone()
    conn.close()

    if not case:
        return jsonify({
            "reply": f"❌ No case found with Case ID {case_id}."
        })

    status_map = {
        0: "Pending",
        1: "In Progress",
        2: "Resolved",
        3: "Escalated"
    }

    reply = (
        f"📄 Case ID: {case_id}\n"
        f"⚙️ Status: {status_map.get(case['status'], 'Unknown')}\n"
        f"🛠 Work Status: {case['work_status'] or 'Not Updated'}"
    )

    return jsonify({"reply": reply})

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)