from flask import Flask, render_template, request, redirect, url_for, make_response, session
from weasyprint import HTML, CSS
from datetime import datetime
import secrets  # For generating secure tokens
import smtplib
import ssl
from email.mime.text import MIMEText

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Dummy user credentials (replace with a secure method in a real application)
USERS = {
    'user': {'password': 'Hkay@1993', 'reset_token': None, 'reset_token_expiry': None, 'email': 'sharmaganesh40@gmail.com'} # Assuming user has this email
}

# Email configuration
SENDER_EMAIL = 'sharmaganesh40@gmail.com'  # Replace with your Gmail address
SENDER_PASSWORD = 'Akay@1993'  # Replace with your Gmail app password
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 465  # For SSL

# Normal ranges for CBC test
NORMAL_RANGES = {
    "Hemoglobin": {"value": 15, "unit": "g/dl", "range": "Male: 13 - 17, Female: 12 - 15"},
    "Total Leukocyte Count": {"value": "5,100", "unit": "cumm", "range": "4,800 - 10,800"},
    "Neutrophils": {"value": 79, "unit": "%", "range": "40 - 80"},
    "Lymphocytes": {"value": 18, "unit": "%", "range": "20 - 40"},
    "Eosinophils": {"value": 1, "unit": "%", "range": "1 - 6"},
    "Monocytes": {"value": 1, "unit": "%", "range": "2 - 10"},
    "Basophils": {"value": 1, "unit": "%", "range": "<2"},
    "Platelet Count": {"value": "3.5", "unit": "lakhs/cumm", "range": "1.5 - 4.1"},
    "Total RBC Count": {"value": 5, "unit": "million/cumm", "range": "Male: 4.5 - 5.5, Female: 4.0 - 5.0"},
    "HCT": {"value": 42, "unit": "%", "range": "Male: 40 - 50, Female: 35 - 45"},
    "MCV": {"value": 84.0, "unit": "fL", "range": "83 - 101"},
    "MCH": {"value": 30.0, "unit": "Pg", "range": "27 - 32"},
    "MCHC": {"value": 35.7, "unit": "%", "range": "31.5 - 34.5"},
}

# Normal ranges for LFT test
NORMAL_RANGES_LFT = {
    "SERUM BILIRUBIN (TOTAL)": {"unit": "mg/dl", "range": "0.2 - 1.2"},
    "SERUM BILIRUBIN (DIRECT)": {"unit": "mg/dl", "range": "0 - 0.3"},
    "SERUM BILIRUBIN (INDIRECT)": {"unit": "mg/dl", "range": "0.2 - 1"},
    "SGPT (ALT)": {"unit": "U/I", "range": "Male: 10 - 40, Female: 7 - 35"},
    "SGOT (AST)": {"unit": "U/I", "range": "Male: 10 - 34, Female: 8 - 30"},
    "SERUM ALKALINE PHOSPHATASE": {"unit": "U/I", "range": "Male: 44 - 147, Female: 33 - 131"},
    "SERUM PROTEIN": {"unit": "g/dl", "range": "6.4 - 8.3"},
    "SERUM ALBUMIN": {"unit": "g/dl", "range": "3.5 - 5.2"},
    "GLOBULIN": {"unit": "g/dl", "range": "1.8 - 3.6"},
    "A/G RATIO": {"unit": "N/A", "range": "1.1 - 2.1"}
}

NORMAL_RANGES_KFT = {
    "BUN": {"unit": "mg/dl", "range": "7 - 25"}, # General adult range, some sources don't show significant gender difference
    "SERUM UREA": {"unit": "mg/dl", "range": "20 - 40"}, # General adult range
    "SERUM CREATININE": {"unit": "mg/dl", "range": "Male: 0.6 - 1.2, Female: 0.5 - 1.1"},
    "EGFR": {"unit": "ml/min/1.73m^2", "range": "> 90"}, # Generally the same for both, but calculation considers gender
    "SERUM CALCIUM": {"unit": "mg/dl", "range": "Male: 8.8 - 10.8, Female: 8.5 - 10.5"},
    "SERUM POTASSIUM": {"unit": "mmol/L", "range": "3.5 - 5.1"},
    "SERUM SODIUM": {"unit": "mmol/L", "range": "135 - 145"},
    "SERUM URIC ACID": {"unit": "mg/dl", "range": "Male: 3.5 - 7.2, Female: 2.6 - 6.0"},
    "UREA / CREATININE RATIO": {"unit": "N/A", "range": "Male: 12 - 20, Female: 10 - 15"}, # Approximate ranges, can vary
    "BUN / CREATININE RATIO": {"unit": "N/A", "range": "Male: 10 - 20, Female: 10 - 15"} # Approximate ranges, can vary
}
# Assuming you have this dictionary defined
NORMAL_RANGES_LIPID = {
    "TOTAL CHOLESTEROL": {"unit": "mg/dl", "range": "125-200"}, # General adult range
    "TRIGLYCERIDES": {"unit": "mg/dl", "range": "Male: 40-160, Female: 35-135"}, # Ranges can vary based on age
    "HDL CHOLESTEROL": {"unit": "mg/dl", "range": "Male: >40, Female: >50"},
    "LDL CHOLESTEROL": {"unit": "mg/dl", "range": "<100"}, # Target levels vary based on risk factors
    "VLDL CHOLESTEROL": {"unit": "mg/dl", "range": "5-40"}, # Calculated value
    "LDL / HDL": {"unit": "", "range": "Male: <3.5, Female: <3.0"}, # Target levels vary
    "TOTAL CHOLESTEROL / HDL": {"unit": "", "range": "Male: <5.0, Female: <4.5"}, # Target levels vary
    "TG / HDL": {"unit": "", "range": ""}, # Ratio, interpretation depends on individual values
    "NON - HDL CHOLESTEROL": {"unit": "", "range": "<130"} # Target levels vary based on risk factors
}

viral_marker_normal_ranges = {
    "HIV-1 (CARD TEST)": {"value": "NEGATIVE"},
    "HIV-2 (CARD TEST)": {"value": "NEGATIVE"},
    "VDRL": {"value": "NON - REACTIVE"},
    "HEPATITIS C VIRUS, HCV": {"value": "NEGATIVE"},
    "HBsAg": {"value": "NEGATIVE"}
}

# Normal ranges for Blood Sugar Fasting and PP
BLOOD_SUGAR_NORMAL_RANGES = {
    "Blood Sugar Fasting": {
        "Normal": {
            "range_mg_dL": "80 - 120"  # Based on the report format
        }
    },
    "Blood Sugar PP": {
        "Normal": {
            "range_mg_dL": "< 140"  # Based on the report format
        }
    }
}
# Normal ranges for BT & CT (Based on the report format)
BT_CT_NORMAL_RANGES = {
    "BLEEDING TIME": {"unit": "min", "range": "2 - 7"},
    "CLOTTING TIME": {"unit": "min", "range": "4 - 9"}
}

NORMAL_RANGES_BILIRUBIN = {
    "SERUM BILIRUBIN (TOTAL)": {"unit": "mg/dl", "range": "0.2 - 1.2"},
    "SERUM BILIRUBIN (DIRECT)": {"unit": "mg/dl", "range": "0 - 0.3"},
    "SERUM BILIRUBIN (INDIRECT)": {"unit": "mg/dl", "range": "0.2 - 1"}
}

NORMAL_RANGES_MP_CARD = {
    "MALARIA PARASITE (CARD TEST)": {"unit": "", "reference": "NEGATIVE"},
    "PLASMODIUM FALCIPARUM 'Pf'": {"unit": "", "reference": "NEGATIVE"},
    "PLASMODIUM VIVAX 'Pv'": {"unit": "", "reference": "NEGATIVE"}
}

# Define normal ranges and interpretations for Dengue tests
dengue_normal_ranges = {
    "DENGUE FEVER ANTIGEN, NS1": {
        "unit": "Index",
        "reference": "< 0.90",
        "interpretation_map": {
            "Negative (< 0.90)": "No detectable Dengue NS1 antigen. The Result does not rule out Dengue infection. An additional sample should be tested for IgG & IgM serology in 7-14 days.",
            "Equivocal (0.90 - 1.10)": "Repeat sample after 1 week",
            "Positive (> 1.10)": "Presence of detectable dengue NS1 antigen. Dengue IgG & IgM serology assay should be performed on follow up samples after 5-7 days of onset of fever, to confirm dengue infection."
        }
    }
    # Add other Dengue parameters here if needed in the future
}
# Normal ranges for Urine Report
NORMAL_RANGES_URINE = {
    "QUANTITY": {"unit": "ml", "reference": "Pale Yellow"}, # Reference here is for color, not quantity range
    "COLOUR": {"unit": "", "reference": "Pale Yellow"},
    "TRANSPARENCY": {"unit": "", "reference": "Clear"},
    "SPECIFIC GRAVITY": {"unit": "", "reference": "1.005 - 1.03"},
    "PH": {"unit": "", "reference": "5 - 7"},
    "LEUKOCYTES": {"unit": "", "reference": "Absent"},
    "BLOOD": {"unit": "", "reference": "Absent"},
    "PROTEIN / ALBUMIN": {"unit": "", "reference": "Absent"},
    "SUGAR / GLUCOSE": {"unit": "", "reference": "Absent"},
    "KETONE BODIES": {"unit": "", "reference": "Absent"},
    "BILIRUBIN": {"unit": "", "reference": "Absent"},
    "NITRITE": {"unit": "", "reference": "Absent"},
    "R.B.C.": {"unit": "/HPF", "reference": "Absent"},
    "PUS CELLS": {"unit": "/HPF", "reference": "Absent"},
    "EPITHELIAL CELLS": {"unit": "/HPF", "reference": "Absent"},
    "CASTS": {"unit": "", "reference": "Absent"},
    "CRYSTALS": {"unit": "", "reference": "Absent"},
    "BACTERIA": {"unit": "", "reference": "Absent"},
    "OTHERS": {"unit": "", "reference": "Absent"},
}





# Configure report types with their respective data
cbc_reports = {}  # In-memory storage
lft_reports ={}
kft_reports = {}
lipid_reports={}
viral_marker_reports={}
blood_sugar_reports = {}
bt_ct_reports={}
bilirubin_reports={}
mp_card_reports={}
dengue_reports ={}
urine_reports = {}



REPORT_CONFIG = {
    'cbc': {
        'storage': cbc_reports,
        'normal_ranges': NORMAL_RANGES,
        'template': 'report.html'
    },
    'lft': {
        'storage': lft_reports,
        'normal_ranges': NORMAL_RANGES_LFT,
        'template': 'lft.html'
    },
    'kft': {
            'storage': kft_reports,
            'normal_ranges': NORMAL_RANGES_KFT,
            'template': 'kftreport.html'
        },
    'lipid': {
                'storage': lipid_reports,
                'normal_ranges': NORMAL_RANGES_LIPID,
                'template': 'lipidprofilereport.html'
            },
    'viral': {
                    'storage': viral_marker_reports,
                    'normal_ranges': viral_marker_normal_ranges,
                    'template': 'viralmarkerreport.html'
                },
    'blood_sugar': {
                    'storage': blood_sugar_reports,
                    'normal_ranges': BLOOD_SUGAR_NORMAL_RANGES,
                    'template': 'blood_sugar_report.html'
                },
    'bt_ct': {
                    'storage': bt_ct_reports,
                    'normal_ranges': BT_CT_NORMAL_RANGES,
                    'template': 'bt_ct_report.html'
                },
    'bilirubin': {
                    'storage': bilirubin_reports,
                    'normal_ranges': NORMAL_RANGES_BILIRUBIN,
                    'template': 'bilirubin_report.html'
                },
    'mp_card': {
                        'storage': mp_card_reports,
                        'normal_ranges': NORMAL_RANGES_MP_CARD,
                        'template': 'mp_card_report.html'
                    },
    'dengue':    {
                        'storage': dengue_reports,
                        'normal_ranges': dengue_normal_ranges,
                        'template': 'dengu_report.html'
                    },
    'urine':  {  # New entry for urine report
            'storage': urine_reports,
            'normal_ranges': NORMAL_RANGES_URINE,
            'template': 'urinereport.html'
        }



}

# Common lab information
LAB_INFO = {
    'reg_no': 'XXXX54826XX',
    'name': 'S.D PATHOLOGICAL LABORATORY & X-RAY CLINIC',
    'phone': '8294959563,6299618711',
    'email': 'slab8985@gmail.com',
    'Address': 'Near by Thakurbari Temple Taraiya Saran'
}

# Common dates
DATES = {
    'registered': '17/10/2024 05:13 PM',
    'collected': '17/10/2024',
    'received': '17/10/2024',
    'reported': '17/10/2024 05:13 PM'
}

def generate_reset_token(username):
    token = secrets.token_urlsafe(32)
    USERS[username]['reset_token'] = token
    USERS[username]['reset_token_expiry'] = datetime.utcnow().timestamp() + 3600  # Token valid for 1 hour
    return token

def is_reset_token_valid(username, token):
    user = USERS.get(username)
    if user and user['reset_token'] == token and user['reset_token_expiry'] > datetime.utcnow().timestamp():
        return True
    return False

def send_reset_email(recipient_email, reset_link):
    subject = 'Password Reset Request'
    body = f"""
    You have requested a password reset for your account.

    Please click on the following link to reset your password:
    {reset_link}

    This link will expire in 1 hour. If you did not request a password reset, please ignore this email.

    Sincerely,
    Your Application Team
    """
    message = MIMEText(body)
    message['Subject'] = subject
    message['From'] = SENDER_EMAIL
    message['To'] = recipient_email

    context = ssl.create_default_context()
    try:
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=context) as server:
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, recipient_email, message.as_string())
        print(f"Password reset email sent to {recipient_email}")
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

@app.route('/', methods=['GET'])
def index():
    if 'username' in session:
        return redirect(url_for('home'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in USERS and USERS[username]['password'] == password:
            session['username'] = username
            return redirect(url_for('home'))
        else:
            return render_template('login.html', error='Invalid username or password')
    return render_template('login.html')

@app.route('/home')
def home():
    if 'username' in session:
        return render_template('home.html')
    return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        username = request.form['username']
        if username in USERS:
            token = generate_reset_token(username)
            reset_link = url_for('reset_password', token=token, _external=True)
            user_email = USERS[username]['email']
            if send_reset_email(user_email, reset_link):
                return render_template('forgot_password_success.html', username=username)
            else:
                return render_template('forgot_password.html', error='Failed to send reset email. Please try again.')
        else:
            return render_template('forgot_password.html', error='Username not found')
    return render_template('forgot_password.html')

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    for username, user_data in USERS.items():
        if user_data['reset_token'] == token:
            if user_data['reset_token_expiry'] > datetime.utcnow().timestamp():
                if request.method == 'POST':
                    new_password = request.form['new_password']
                    confirm_password = request.form['confirm_password']
                    if new_password == confirm_password:
                        USERS[username]['password'] = new_password
                        USERS[username]['reset_token'] = None
                        USERS[username]['reset_token_expiry'] = None
                        return render_template('reset_password_success.html')
                    else:
                        return render_template('reset_password_form.html', token=token, error='Passwords do not match')
                return render_template('reset_password_form.html', token=token)
            else:
                return render_template('reset_password_expired.html')
    return render_template('reset_password_invalid.html')

@app.route('/cbc')
def cbc_report():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('index.html')  # Your existing CBC form template

@app.route('/lft')
def lft_report():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('lftindex.html')

@app.route('/kft')
def kft_report():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('kftindex.html')

@app.route('/lipid')
def lipid_report():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('lipidprofileindex.html')


@app.route('/viral')
def viral_report():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('viralmarkerindex.html')

@app.route('/blood_sugar', methods=['GET'])
def blood_sugar_form():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('blood_sugar_index.html')

# BT & CT Report Routes
@app.route('/bt_ct', methods=['GET'])
def bt_ct_form():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('bt_ct_index.html')

@app.route('/bilirubin', methods=['GET'])
def bilirubin_form():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('bilirubin_index.html')

@app.route('/mp_card', methods=['GET'])
def mp_card_form():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('mp_card_index.html')
@app.route('/dengue', methods=['GET'])
def dengu_form():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('dengu_index.html')

@app.route('/urine', methods=['GET']) # New route for urine report form
def urine_report_form():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('urineindex.html')

@app.route('/generate_report', methods=['POST'])
def generate_report():
    if 'username' not in session:
        return redirect(url_for('login'))

    # Extract common report data from the form
    report_data = {
        "patient_name": request.form['patient_name'],
        "patient_id": request.form['patient_id'],
        "Age": request.form['age'],
        "Gender": request.form['gender'],
        "referedby": request.form['referedby'],
        "phonenumber": request.form['phonenumber'],
        "collection_date": request.form.get('collection_date'),
        "report_date": datetime.now().strftime('%d/%m/%Y %I:%M %p'),
        "selected_test": request.form['selected_test'],  # Get the selected test type
    }

    selected_test = report_data['selected_test']

    if selected_test == 'CBC':
        selected_cbc_parameters = request.form.getlist('selected_cbc_parameters')
        cbc_results = {}
        for param_name in selected_cbc_parameters:
            print(param_name)
            # if ' ' in param :
            #     param_name = param.replace(' ','')
            #     print(param_name)
            # else:
            #     param_name =param
            #     print(param_name)
            value = request.form.get(param_name)
            normal_range_value = request.form.get(param_name + '_normal_range')  # Get user-input normal range
            if value is not None:
                try:
                    # Handle the comma in "Total Leukocyte Count" during conversion
                    if param_name == "Total Leukocyte Count":
                        cbc_results[param_name] = float(value.replace(',', ''))
                    elif ',' in param_name:
                         paramele=param_name.split(',')[1].strip()
                         cbc_results[paramele]= float(value)
                    else:
                        cbc_results[param_name] = float(value)
                except ValueError:
                    cbc_results[param_name] = value  # Store as string if conversion fails

                # Store the user-provided normal range, if provided
                if normal_range_value:
                    print(normal_range_value)
                    report_data[param_name + '_normal_range'] = normal_range_value  # Store within cbc_results

        report_data['cbc_results'] = cbc_results

        # Generate unique report ID
        report_id = len(cbc_reports) + 1
        cbc_reports[report_id] = report_data

        # Redirect to the report display route
        return redirect(url_for('show_report', report_id=report_id))

    else:
        return "Invalid report type!"



@app.route('/generate_lft_report', methods=['POST'])
def generate_lft_report():
    if 'username' not in session:
        return redirect(url_for('login'))
    # Extract data from form
    report_data = {
        "patient_name": request.form['patient_name'],
        "patient_id": request.form['patient_id'],
        "Age": request.form['age'],
        "Gender": request.form['gender'],  # Capture gender from the form
        "referedby": request.form['referedby'],  # Corrected the form field name
        "phonenumber": request.form['phonenumber'],
        "collection_date": request.form.get('collection_date'),
        "report_date": datetime.now().strftime('%d/%m/%Y %I:%M %p'),
        "selected_test": 'LFT' # <--- IMPORTANT: Ensure this is set for the HTML template
    }

    selected_lft_test = request.form['selected_lft_test'] # This is likely 'LFT' from your form
    # report_data['selected_lft_test'] = selected_lft_test # This line is redundant if 'selected_test' is already set above

    if selected_lft_test == 'LFT':
        selected_lft_parameters = request.form.getlist('selected_lft_parameters')

        lft_results = {}
        for param in selected_lft_parameters:
            value = request.form.get(param)
            # Normalize param name for normal_range_value lookup
            # Use .replace(' ', '_').replace('/', '_') to match potential form field name changes
            # param_for_key = param.replace(' ', '_').replace('/', '_')
            normal_range_value = request.form.get(param + '_normal_range')

            if value is not None:
                try:
                    # Attempt to convert to float, keep as string if not possible
                    lft_results[param] = float(value)
                except ValueError:
                    lft_results[param] = value  # Store as string if conversion fails

                # Store the user-provided normal range, if provided and not empty
                if normal_range_value: # Ensure it's not an empty string
                    report_data[param + '_normal_range'] = normal_range_value # Use the normalized key

        report_data['lft_results'] = lft_results

        # Generate unique report ID for LFT
        report_id = len(lft_reports) + 1
        lft_reports[report_id] = report_data
        print("LFT Results stored:", lft_reports) # Debugging print

        # Redirect to LFT report page with the new ID
        return redirect(url_for('show_lft_report', report_id=report_id))

    return "Error: Invalid test selected"

@app.route('/generate_kft_report', methods=['POST'])
def generate_kft_report():
    if 'username' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        # Extract patient information
        report_data = {
            "patient_name": request.form['patient_name'],
            "patient_id": request.form['patient_id'],
            "Age": request.form['age'],
            "Gender": request.form['gender'],
            "referedby": request.form['referedby'],
            "phonenumber": request.form['phonenumber'],
            "collection_date": request.form.get('collection_date'),
            "report_date": datetime.now().strftime('%d/%m/%Y %I:%M %p'),

        }
        selected_kft_test = request.form['selected_kft_test']
        report_data['selected_kft_test'] = selected_kft_test

        if report_data['selected_kft_test'] == 'KFT':
            selected_kft_parameters = request.form.getlist('selected_kft_parameters')
            kft_results = {}
            for param in selected_kft_parameters:
                value = request.form.get(param)

                normal_range_value = request.form.get(param + '_normal_range')
                if value is not None:
                    try:
                        if param == 'EGFR':
                            kft_results[param] = {
                                'value': float(value),
                                'category': request.form.get('EGFR_category', '')
                            }
                        else:
                            kft_results[param] = float(value)
                    except ValueError:
                        kft_results[param] = value  # Store as string if conversion fails

                    # Store the user-provided normal range, if provided and not empty
                    if normal_range_value:  # Ensure it's not an empty string
                        report_data[param + '_normal_range'] = normal_range_value  # Use the

            report_data['kft_results'] = kft_results

            # Generate unique report ID for KFT
            report_id = len(kft_reports) + 1
            kft_reports[report_id] = report_data
            print("KFT Results:", kft_reports)

            # Redirect to KFT report page with the new ID
            return redirect(url_for('show_kft_report', report_id=report_id))

        return "Error: Invalid test selected"

@app.route('/generate_lipid_report', methods=['POST'])
def generate_lipid_report():
    if 'username' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        # Extract patient information
        report_data = {
            "patient_name": request.form['patient_name'],
            "patient_id": request.form['patient_id'],
            "Age": request.form['age'],
            "Gender": request.form['gender'],
            "referedby": request.form['referedby'],
            "phonenumber": request.form['phonenumber'],
            "collection_date": request.form.get('collection_date'),
            "report_date": datetime.now().strftime('%d/%m/%Y %I:%M %p'),

        }
        selected_lipid_test = request.form['selected_lipid_test']
        report_data['selected_lipid_test'] = selected_lipid_test

        if report_data['selected_lipid_test'] == 'LipidProfile':
            selected_lipid_parameters = request.form.getlist('selected_lipid_parameters')

            lipid_results = {}
            for param in selected_lipid_parameters:
                value = request.form.get(param)
                normal_range_value = request.form.get(param + '_normal_range')
                if value:
                    try:
                        lipid_results[param] = float(value)
                    except ValueError:
                        lipid_results[param] = value

                    # Store the user-provided normal range, if provided and not empty
                    if normal_range_value:  # Ensure it's not an empty string
                        report_data[param + '_normal_range'] = normal_range_value

            report_data['lipid_results'] = lipid_results

            # Generate unique report ID for Lipid Profile
            report_id = len(lipid_reports) + 1
            lipid_reports[report_id] = report_data
            print("Lipid Profile Results:", lipid_reports)

            # Redirect to Lipid Profile report page
            return redirect(url_for('show_lipid_report', report_id=report_id))

        return "Error: Invalid test selected"

@app.route('/generate_viral_marker_report', methods=['POST'])
def generate_viral_marker_report():
    if 'username' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        report_data = {
            "patient_name": request.form['patient_name'],
            "Age": request.form['age'],
            "Gender": request.form['gender'],
            "referedby": request.form['referedby'],
            "phonenumber": request.form['phonenumber'],
            "patient_id": request.form['patient_id'],
            "report_id": request.form['report_id'],
            "collection_date": request.form['collection_date'],
            "report_date": datetime.now().strftime('%d/%m/%Y %I:%M %p'),
            "reg_no": request.form['reg_no'],
            "hiv1": request.form['hiv1'],
            "hiv2": request.form['hiv2'],
            "vdrl": request.form['vdrl'],
            "hcv": request.form['hcv'],
            "hbsag": request.form['hbsag']
        }


        report_id  = len(viral_marker_reports) + 1
        viral_marker_reports[report_id] = report_data
        print("viral_marker_reports Results:", viral_marker_reports)

        return redirect(url_for('show_viral_marker_report', report_id=report_id))

@app.route('/generate_blood_sugar_report', methods=['POST'])
def generate_blood_sugar_report():
    if 'username' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        # Extract patient information
        report_data = {
            "patient_name": request.form['patient_name'],
            "patient_id": request.form['patient_id'],
            "Age": request.form['age'],
            "Gender": request.form['gender'],
            "referedby": request.form['referedby'],
            "phonenumber": request.form['phonenumber'],
            "collection_date": request.form.get('collection_date'),
            "report_date": datetime.now().strftime('%d/%m/%Y %I:%M %p'),
            "report_id": request.form['report_id'] # Added report_id from form
        }
        selected_blood_sugar_test = request.form['selected_blood_sugar_test']
        report_data['selected_blood_sugar_test'] = selected_blood_sugar_test

        if report_data['selected_blood_sugar_test'] == 'Blood Sugar (FP & PP)':
            selected_parameters = request.form.getlist('selected_blood_sugar_parameters')
            blood_sugar_results = {}
            for param in selected_parameters:
                value = request.form.get(param)
                normal_range_value = request.form.get(param + '_normal_range')

                if value is not None:
                    try:
                        blood_sugar_results[param] = float(value)
                    except ValueError:
                        blood_sugar_results[param] = value  # Store as string if conversion fails

                    # Store the user-provided normal range, if provided and not empty
                    if normal_range_value:
                        report_data[param + '_normal_range'] = normal_range_value

            report_data['blood_sugar_results'] = blood_sugar_results

            # Generate unique report ID for Blood Sugar
            # Using report_id from form, or generate if not provided
            report_id = len(blood_sugar_reports) + 1
            blood_sugar_reports[report_id] = report_data
            print("Blood Sugar Results:", blood_sugar_reports)

            # Redirect to Blood Sugar report page with the new ID
            return redirect(url_for('show_blood_sugar_report', report_id=report_id))
    return redirect(url_for('blood_sugar_form')) # Redirect back if not POST

@app.route('/generate_bt_ct_report', methods=['POST'])
def generate_bt_ct_report():
    if 'username' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        report_data = {
            "patient_name": request.form['patient_name'],
            "age": request.form['age'],
            "gender": request.form['gender'],
            "referred_by": request.form['referred_by'],
            "reg_no": request.form['reg_no'],
            "collection_date": request.form.get('collection_date', DATES['collected']),
            "received_date": request.form.get('received_date', DATES['received']),
            "reported_date": DATES['reported'],
            "bleeding_time": request.form['bleeding_time'],
            "clotting_time": request.form['clotting_time']
        }

        report_id = len(bt_ct_reports) + 1
        report_data['report_id'] = report_id
        bt_ct_reports[report_id] = report_data

        return redirect(url_for('show_bt_ct_report', report_id=report_id))

@app.route('/generate_bilirubin_report', methods=['POST'])
def generate_bilirubin_report():
    if 'username' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        report_data = {
            "patient_name": request.form['patient_name'],
            "age": request.form['age'],
            "gender": request.form['gender'],
            "referedby": request.form['referedby'],
            "phonenumber": request.form['phonenumber'],
            # "reg_no": request.form['reg_no'],
            "collection_date": request.form.get('collection_date', DATES['collected']),
            "received_date": datetime.now().strftime('%d/%m/%Y %I:%M %p'),
            # "bilirubin_results": {
            #     "SERUM BILIRUBIN (TOTAL)": float(request.form['SERUM BILIRUBIN (TOTAL)']),
            #     "SERUM BILIRUBIN (DIRECT)": float(request.form['SERUM BILIRUBIN (DIRECT)']),
            #     "SERUM BILIRUBIN (INDIRECT)": float(request.form['SERUM BILIRUBIN (INDIRECT)'])
            # }
        }
        selected_bilirubin_test = request.form['selected_bilirubin_test']
        report_data['selected_bilirubin_test'] = selected_bilirubin_test

        if report_data['selected_bilirubin_test'] == 'Bilirubin':
            selected_bilirubin_test = request.form.getlist('selected_bilirubin_parameters')

            bilirubin_results = {}
            for param in selected_bilirubin_test:
                value = request.form.get(param)
                normal_range_value = request.form.get(param + '_normal_range')
                if value:
                    try:
                        bilirubin_results[param] = float(value)
                    except ValueError:
                        bilirubin_results[param] = value

                    # Store the user-provided normal range, if provided and not empty
                    if normal_range_value:  # Ensure it's not an empty string
                        report_data[param + '_normal_range'] = normal_range_value

            report_data['bilirubin_results'] = bilirubin_results

        report_id = len(bilirubin_reports) + 1
        bilirubin_reports[report_id] = report_data
        print("Bilirubin Results:", bilirubin_reports)

        return redirect(url_for('show_bilirubin_report', report_id=report_id))
    return "Error: Invalid request"

@app.route('/generate_mp_card_report', methods=['POST'])
def generate_mp_card_report():
    if 'username' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        report_data = {
            "patient_name": request.form['patient_name'],
            "age": request.form['age'],
            "gender": request.form['gender'],
            "referedby": request.form['referred_by'],
            "reg_no": request.form['reg_no'],
            "collection_date": request.form.get('collection_date', DATES['collected']),
            "received_date": datetime.now().strftime('%d/%m/%Y %I:%M %p'),  # You might want a separate field for this

            "mp_card_results": {
                "MALARIA PARASITE (CARD TEST)": request.form['MALARIA PARASITE (CARD TEST)'],
                "PLASMODIUM FALCIPARUM 'Pf'": request.form["PLASMODIUM FALCIPARUM 'Pf'"],
                "PLASMODIUM VIVAX 'Pv'": request.form["PLASMODIUM VIVAX 'Pv'"]
            }
        }

        report_id = len(mp_card_reports) + 1
        mp_card_reports[report_id] = report_data
        print("MP Card Test Results:", mp_card_reports)

        return redirect(url_for('show_mp_card_report', report_id=report_id))
    return "Error: Invalid request"

@app.route('/generate_dengue_report', methods=['POST'])
def generate_dengue_report():
    if 'username' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        # Extract patient information
        report_data = {
            "patient_name": request.form['patient_name'],
            "patient_id": request.form['patient_id'],
            "Age": request.form['age'],
            "Gender": request.form['gender'],
            "referedby": request.form['referedby'],
            "phonenumber": request.form['phonenumber'],
            "collection_date": request.form.get('collection_date'),
            "report_date": datetime.now().strftime('%d/%m/%Y %I:%M %p'),
            "report_id": request.form['report_id'],
            "sample_collected_at": request.form.get('sample_collected_at'),
            "sample_collected_by": request.form.get('sample_collected_by'),
            "referred_by_dr": request.form.get('referred_by_dr')
        }
        selected_dengue_test = request.form['selected_dengue_test']
        report_data['selected_dengue_test'] = selected_dengue_test

        if report_data['selected_dengue_test'] == 'Dengue Fever Antigen, NS1':
            dengue_results = {
                "DENGUE FEVER ANTIGEN, NS1": {
                    "value": request.form.get("DENGUE FEVER ANTIGEN, NS1"),
                    "interpretation": request.form.get("DENGUE FEVER ANTIGEN, NS1_interpretation")
                }
            }
            report_data['dengue_results'] = dengue_results

            report_data['note'] = request.form.get('note_section')
            report_data['comments'] = request.form.get('comments_section')


            # Generate unique report ID for Dengue

            report_id = len(dengue_reports) + 1
            dengue_reports[report_id] = report_data
            print("Dengue Results:", dengue_reports)

            # Redirect to Dengue report page with the new ID
            return redirect(url_for('show_dengue_report', report_id=report_id))
    return redirect(url_for('dengue_form'))

@app.route('/generate_urine_report', methods=['POST'])
def generate_urine_report():
    if 'username' not in session:
        return redirect(url_for('login'))

    # Extract all form data for urine report
    report_data = {
        'patientName': request.form.get('patientName', 'N/A'),
        'ageSex': request.form.get('ageSex', 'N/A'),
        'referredBy': request.form.get('referredBy', 'N/A'),
        'regNo': request.form.get('regNo', 'N/A'),
        'registeredOnDate': request.form.get('registeredOnDate', 'N/A'),
        'registeredOnTime': request.form.get('registeredOnTime', 'N/A'),
        'collectedOn': request.form.get('collectedOn', 'N/A'),
        'reportedOn': request.form.get('reportedOn', 'N/A'),
        'receivedOnDate': request.form.get('receivedOnDate', 'N/A'),
        'receivedOnTime': request.form.get('receivedOnTime', 'N/A'),

        # Physical Examination
        'quantity': request.form.get('quantity', 'N/A'),
        'quantityUnit': request.form.get('quantityUnit', ''),
        'colour': request.form.get('colour', 'N/A'),
        'transparency': request.form.get('transparency', 'N/A'),
        'specificGravity': request.form.get('specificGravity', 'N/A'),
        'specificGravityRef': request.form.get('specificGravityRef', 'N/A'),
        'ph': request.form.get('ph', 'N/A'),
        'phRef': request.form.get('phRef', 'N/A'),
        'leukocytes': request.form.get('leukocytes', 'N/A'),
        'blood': request.form.get('blood', 'N/A'),

        # Chemical Examination
        'proteinAlbumin': request.form.get('proteinAlbumin', 'N/A'),
        'sugarGlucose': request.form.get('sugarGlucose', 'N/A'),
        'ketoneBodies': request.form.get('ketoneBodies', 'N/A'),
        'bilirubin': request.form.get('bilirubin', 'N/A'),
        'nitrite': request.form.get('nitrite', 'N/A'),

        # Microscopic Examination
        'rbc': request.form.get('rbc', 'N/A'),
        'rbcUnit': request.form.get('rbcUnit', ''),
        'pusCells': request.form.get('pusCells', 'N/A'),
        'pusCellsUnit': request.form.get('pusCellsUnit', ''),
        'epithelialCells': request.form.get('epithelialCells', 'N/A'),
        'epithelialCellsUnit': request.form.get('epithelialCellsUnit', ''),
        'casts': request.form.get('casts', 'N/A'),
        'crystals': request.form.get('crystals', 'N/A'),
        'bacteria': request.form.get('bacteria', 'N/A'),
        'others': request.form.get('others', 'N/A'),
    }

    # Generate unique report ID
    report_id = len(urine_reports) + 1
    urine_reports[report_id] = report_data
    print("Urine Report Data Stored:", urine_reports) # Debugging print

    # Redirect to the urine report display route
    return redirect(url_for('show_urine_report', report_id=report_id))



@app.route('/report/<int:report_id>')
def show_report(report_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    report = cbc_reports.get(report_id)
    print(report)

    if not report:
        return "Report not found!", 404

    # Pass both report data and report_id to the template
    return render_template('report.html', report=report, report_id=report_id, normal_ranges=NORMAL_RANGES)

@app.route('/lft_report/<int:report_id>')
def show_lft_report(report_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    report = lft_reports.get(report_id)
    if not report:
        return "LFT Report not found!", 404
    return render_template('lft.html', report=report, report_id=report_id, normal_ranges=NORMAL_RANGES_LFT)

@app.route('/kft_report/<int:report_id>')
def show_kft_report(report_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    report = kft_reports.get(report_id)
    if report:
        return render_template('kftreport.html', report=report,report_id=report_id, normal_ranges=NORMAL_RANGES_KFT)
    else:
        return "Report not found"

@app.route('/lipid_report/<int:report_id>')
def show_lipid_report(report_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    report = lipid_reports.get(report_id)
    if report:
        return render_template('lipidprofilereport.html', report=report,report_id=report_id, normal_ranges=NORMAL_RANGES_LIPID)
    else:
        return "Report not found"

@app.route('/viral_marker_report/<report_id>')
def show_viral_marker_report(report_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    viral_report_data = viral_marker_reports.get(int(report_id))
    if viral_report_data :
        return render_template('viralmarkerreport.html', report=viral_report_data , report_id=int(report_id), normal_ranges=viral_marker_normal_ranges)
    else:
        return "Report not found"

@app.route('/blood_sugar_report/<report_id>')
def show_blood_sugar_report(report_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    blood_sugar_report = blood_sugar_reports.get(int(report_id))
    print(blood_sugar_report)
    if blood_sugar_report:
        return render_template('blood_sugar_report.html', report=blood_sugar_report,report_id=int(report_id), normal_ranges=BLOOD_SUGAR_NORMAL_RANGES)
    else:
        return "Report Is not available"

@app.route('/bt_ct_report/<report_id>')
def show_bt_ct_report(report_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    btctreport = bt_ct_reports.get(int(report_id))
    if btctreport:
        return render_template('bt_ct_report.html', report=btctreport,report_id=int(report_id), normal_ranges=BT_CT_NORMAL_RANGES)
    else:
        return "Report not found"

@app.route('/bilirubin_report/<int:report_id>')
def show_bilirubin_report(report_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    blirubinreport = bilirubin_reports.get(int(report_id))
    if blirubinreport:
        return render_template('bilirubin_report.html', report=blirubinreport, report_id=int(report_id), normal_ranges=NORMAL_RANGES_BILIRUBIN, lab_info=LAB_INFO, dates=DATES)
    else:
        return "Bilirubin Report not found"

@app.route('/mp_card_report/<int:report_id>')
def show_mp_card_report(report_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    mpreport = mp_card_reports.get(int(report_id))
    if mpreport:
        return render_template('mp_card_report.html', report=mpreport, report_id=int(report_id), normal_ranges=NORMAL_RANGES_MP_CARD, lab_info=LAB_INFO, dates=DATES)
    else:
        return "MP Card Test Report not found"

@app.route('/dengue_report/<int:report_id>')
def show_dengue_report(report_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    dengureport = dengue_reports.get(int(report_id))
    print(dengureport)
    if dengureport:
        return render_template('dengu_report.html', report=dengureport, report_id=int(report_id), normal_ranges=dengue_normal_ranges)

    return "Dengue Report not found", 404

@app.route('/show_urine_report/<int:report_id>')
def show_urine_report(report_id):
    if 'username' not in session:
        return redirect(url_for('login'))

    urine_report_data = urine_reports.get(int(report_id))
    if not urine_report_data:
        return "Report not found!", 404

    return render_template('urinereport.html', report=urine_report_data,report_id=int(report_id))


@app.route('/download_pdf/<report_type>/<int:report_id>')
def download_pdf(report_type,report_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    # Get configuration for the report type
    config = REPORT_CONFIG.get(report_type.lower())
    if not config:
        return "Invalid report type!", 404

    # Get the report from appropriate storage
    report = config['storage'].get(report_id)
    if not report:
        return f"{report_type.upper()} Report not found!", 404

    # Render the appropriate template
    html = render_template(
        config['template'],
        report=report,
        report_id=report_id,
        normal_ranges=config['normal_ranges'],
        lab_info=LAB_INFO,
        dates=DATES
    )


    # Generate PDF
    pdf =HTML(string=html).write_pdf(
    stylesheets=[CSS(string='@page { size: A4; margin: 0; }')],
    presentational_hints=True
    )

    # Create response with PDF
    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=report_{report_id}.pdf'
    return response

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)