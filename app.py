"""
CreditX Backend — Flask API
Run: python3 app.py  →  http://localhost:8080
"""
from flask import Flask, request, jsonify, send_from_directory, session
import sqlite3, random, os, datetime, json, re
from werkzeug.utils import secure_filename

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, 'uploads')
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'jpeg', 'png'}

def get_env(name, default=''):
    value = os.environ.get(name, default)
    return value.strip() if isinstance(value, str) else value

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

app = Flask(__name__, static_folder=os.path.join(BASE_DIR, 'static'))
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max upload
app.secret_key = get_env('FLASK_SECRET_KEY', 'creditx-local-dev-secret')

@app.after_request
def add_cors(response):
    response.headers['Access-Control-Allow-Origin']  = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization'
    response.headers['Access-Control-Allow-Methods'] = 'GET,POST,PUT,DELETE,OPTIONS'
    return response

@app.route('/', defaults={'path': ''}, methods=['OPTIONS'])
@app.route('/<path:path>', methods=['OPTIONS'])
def handle_options(path): return '', 204

DB = os.path.join(BASE_DIR, 'creditx.db')

def init_db():
    conn = sqlite3.connect(DB); c = conn.cursor()
    # ── Core tables ──
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        uid TEXT UNIQUE, email TEXT, display_name TEXT,
        photo_url TEXT, auth_provider TEXT DEFAULT 'google',
        phone TEXT, verified INTEGER DEFAULT 0,
        profile_complete INTEGER DEFAULT 0,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS company_profiles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_uid TEXT UNIQUE,
        company_name TEXT, gstin TEXT, sector TEXT,
        address TEXT, owner_name TEXT, mobile TEXT,
        bee_cert TEXT, energy_manager TEXT,
        gst_doc TEXT, pan_doc TEXT, reg_doc TEXT,
        digilocker_verified INTEGER DEFAULT 0,
        profile_status TEXT DEFAULT 'pending',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS companies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT, gstin TEXT, sector TEXT, address TEXT,
        energy_manager TEXT, bee_cert TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS emissions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company_id INTEGER, period TEXT,
        electricity REAL, fuel REAL, transport REAL, production REAL,
        co2_electricity REAL, co2_fuel REAL, co2_transport REAL,
        co2_total REAL, credits REAL, credit_value REAL, green_score REAL,
        ef_electricity REAL DEFAULT 0.82, ef_fuel REAL DEFAULT 2.31,
        ef_transport REAL DEFAULT 0.12,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS credits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        token_id TEXT UNIQUE, company_id INTEGER, company_name TEXT,
        sector TEXT, amount REAL, price_per_credit REAL DEFAULT 800,
        status TEXT DEFAULT 'active', tx_hash TEXT, block_number INTEGER,
        verified INTEGER DEFAULT 1, emission_id INTEGER,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS trades (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        token_id TEXT, from_company TEXT, to_company TEXT,
        amount REAL, price_per_credit REAL, total_value REAL,
        platform_fee REAL, tx_hash TEXT,
        trade_type TEXT DEFAULT 'BUY', status TEXT DEFAULT 'confirmed',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS portfolio (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company_id INTEGER, token_id TEXT, source TEXT,
        amount REAL, buy_price REAL, current_price REAL DEFAULT 800,
        acquired_at TEXT DEFAULT CURRENT_TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company_id INTEGER, report_ref TEXT UNIQUE, period TEXT,
        co2_total REAL, credits REAL, sec_value REAL, status TEXT DEFAULT 'draft',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS otp_store (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        phone TEXT, otp TEXT, expires_at TEXT,
        used INTEGER DEFAULT 0,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP)''')

    c.execute("SELECT COUNT(*) FROM companies"); 
    if c.fetchone()[0] == 0:
        companies = [
            ('Rajan Industries Pvt. Ltd.','29AABCR1234P1ZX','Small Scale Industry','Plot 47, MIDC, Pune','Rajesh Kumar Sharma','BEE-EM-2019-08847'),
            ('GreenSteel Ltd.','27AABCG5678Q1ZY','Iron & Steel','Sector 12, GIDC, Surat','Anita Mehta','BEE-EM-2020-04321'),
            ('TerraFabrics','24AABCT9012R1ZZ','Textile','Ludhiana Industrial Area','Suresh Patel','BEE-EM-2018-07654'),
            ('EcoPharma','07AABCE3456S1ZW','Pharmaceutical','Baddi, Himachal Pradesh','Dr. Priya Sharma','BEE-EM-2021-09876'),
            ('SunAgro Farms','29AABCS7890T1ZV','Agriculture','Nashik, Maharashtra','Ramesh Yadav','BEE-EM-2019-03210'),
            ('CoolChain Ltd.','06AABCC2345U1ZU','Cold Storage','Kundli, Haryana','Vikram Singh','BEE-EM-2022-06543'),
            ('NovoCement','08AABCN6789V1ZT','Cement','Gulbarga, Karnataka','Mohan Das','BEE-EM-2017-01987'),
        ]
        c.executemany("INSERT INTO companies (name,gstin,sector,address,energy_manager,bee_cert) VALUES (?,?,?,?,?,?)", companies)
        creds = [
            ('CX-2025-00198',1,'Rajan Industries Pvt. Ltd.','Small Scale Industry',1.248,800,'active','0x4a3b2c1d...f12c',4891204),
            ('CX-2025-00245',1,'Rajan Industries Pvt. Ltd.','Small Scale Industry',0.980,800,'active','0x5b4c3d2e...g23d',4891210),
            ('CX-2025-00134',2,'GreenSteel Ltd.','Iron & Steel',5.200,820,'active','0x7d8e9f0a...a091',4891100),
            ('CX-2025-00156',3,'TerraFabrics','Textile',2.100,760,'active','0x1f2a3b4c...c445',4891150),
            ('CX-2025-00178',4,'EcoPharma','Pharmaceutical',0.800,890,'active','0x9c4d5e6f...b223',4891200),
            ('CX-2025-00201',5,'SunAgro Farms','Agriculture',3.400,700,'active','0xab1cd2ef...d334',4891201),
            ('CX-2025-00223',6,'CoolChain Ltd.','Cold Storage',1.600,810,'active','0xa1b2c3d4...d445',4891220),
        ]
        c.executemany("INSERT INTO credits (token_id,company_id,company_name,sector,amount,price_per_credit,status,tx_hash,block_number) VALUES (?,?,?,?,?,?,?,?,?)", creds)
        c.executemany("INSERT INTO trades (token_id,from_company,to_company,amount,price_per_credit,total_value,platform_fee,tx_hash,trade_type,status) VALUES (?,?,?,?,?,?,?,?,?,?)", [
            ('CX-2025-00134','GreenSteel Ltd.','Rajan Industries',2.0,780,1560,15.6,'0x1f2a3b4c...c445','BUY','confirmed'),
            ('CX-2025-00156','TerraFabrics','EcoPharma',0.5,820,410,4.1,'0x7d8e9f0a...a091','SELL','confirmed'),
            ('CX-2025-00178','EcoPharma','Rajan Industries',1.0,760,760,7.6,'0x3e5f6a7b...d778','BUY','confirmed'),
        ])
        c.executemany("INSERT INTO portfolio (company_id,token_id,source,amount,buy_price,current_price) VALUES (?,?,?,?,?,?)", [
            (1,'CX-2025-00245','Electricity Reduction',1.248,800,800),
            (1,'CX-2025-00198','Fuel Optimisation',0.980,780,800),
            (1,'CX-2025-00134','Purchased (GreenSteel)',2.000,780,800),
        ])
    conn.commit(); conn.close()

def get_db():
    conn = sqlite3.connect(DB); conn.row_factory = sqlite3.Row; return conn

def gen_hash(): return '0x'+''.join(random.choices('0123456789abcdef',k=8))+'...'+''.join(random.choices('0123456789abcdef',k=4))
def gen_token(): return 'CX-2025-'+str(random.randint(10000,99999))

# ── SERVE FRONTEND ──
@app.route('/')
def index(): return send_from_directory(os.path.join(BASE_DIR,'static'),'index.html')


@app.route('/favicon.ico')
def favicon():
    return '', 204


@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'success': True, 'status': 'ok', 'service': 'creditx-backend'})


@app.route('/api/config', methods=['GET'])
def config():
    firebase_config = {
        'apiKey': get_env('FIREBASE_API_KEY'),
        'authDomain': get_env('FIREBASE_AUTH_DOMAIN'),
        'projectId': get_env('FIREBASE_PROJECT_ID'),
        'storageBucket': get_env('FIREBASE_STORAGE_BUCKET'),
        'messagingSenderId': get_env('FIREBASE_MESSAGING_SENDER_ID'),
        'appId': get_env('FIREBASE_APP_ID')
    }
    firebase_enabled = all(firebase_config.values())
    return jsonify({
        'success': True,
        'firebaseEnabled': firebase_enabled,
        'firebaseConfig': firebase_config,
        'appName': 'CreditX',
        'authModes': ['google', 'otp']
    })


@app.route('/api/auth/session', methods=['GET'])
def auth_session():
    uid = session.get('uid')
    if not uid:
        return jsonify({'success': True, 'authenticated': False})
    conn = get_db(); c = conn.cursor()
    c.execute("SELECT * FROM users WHERE uid=?", (uid,))
    user_row = c.fetchone()
    c.execute("SELECT * FROM company_profiles WHERE user_uid=?", (uid,))
    profile_row = c.fetchone()
    conn.close()
    if not user_row:
        session.clear()
        return jsonify({'success': True, 'authenticated': False})
    return jsonify({
        'success': True,
        'authenticated': True,
        'user': dict(user_row),
        'has_profile': profile_row is not None,
        'profile': dict(profile_row) if profile_row else None
    })

# ══════════════════════════════════
# AUTH & USER PROFILE ENDPOINTS
# ══════════════════════════════════

@app.route('/api/auth/google', methods=['POST'])
def auth_google():
    """Called after Firebase Google sign-in — saves/updates user in local DB"""
    d = request.get_json(force=True)
    uid = d.get('uid',''); email = d.get('email','')
    name = d.get('displayName',''); photo = d.get('photoURL','')
    if not uid: return jsonify({'success':False,'error':'uid required'}), 400
    conn = get_db(); c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (uid,email,display_name,photo_url,auth_provider) VALUES (?,?,?,?,'google')",(uid,email,name,photo))
    c.execute("UPDATE users SET email=?,display_name=?,photo_url=? WHERE uid=?",(email,name,photo,uid))
    c.execute("SELECT * FROM users WHERE uid=?", (uid,))
    user = dict(c.fetchone()); conn.commit(); conn.close()
    session['uid'] = uid
    conn2 = get_db(); c2 = conn2.cursor()
    c2.execute("SELECT * FROM company_profiles WHERE user_uid=?",(uid,))
    prof = c2.fetchone()
    conn2.close()
    return jsonify({'success':True,'user':user,'has_profile': prof is not None,'profile':dict(prof) if prof else None})

@app.route('/api/auth/send-otp', methods=['POST'])
def send_otp():
    """Generate OTP for phone login (simulated — in prod use SMS gateway)"""
    d = request.get_json(force=True); phone = d.get('phone','').strip()
    normalized_phone = phone.replace(' ', '').replace('-', '')
    if normalized_phone.startswith('+91'):
        candidate = normalized_phone[3:]
    elif normalized_phone.startswith('91') and len(normalized_phone) == 12:
        candidate = normalized_phone[2:]
    else:
        candidate = normalized_phone
    if not re.match(r'^[6-9]\d{9}$', candidate):
        return jsonify({'success':False,'error':'Invalid Indian mobile number'}), 400
    otp = str(random.randint(100000,999999))
    expires = (datetime.datetime.now() + datetime.timedelta(minutes=10)).isoformat()
    conn = get_db(); c = conn.cursor()
    c.execute("INSERT INTO otp_store (phone,otp,expires_at) VALUES (?,?,?)",(phone,otp,expires))
    conn.commit(); conn.close()
    # In production: send via SMS (Twilio / MSG91). For demo we return it.
    print(f"[OTP] Phone: {phone}  OTP: {otp}  (demo — not sent via SMS)")
    return jsonify({'success':True,'message':f'OTP sent to {phone}','demo_otp':otp})

@app.route('/api/auth/verify-otp', methods=['POST'])
def verify_otp():
    d = request.get_json(force=True)
    phone = d.get('phone','').strip(); otp = d.get('otp','').strip()
    conn = get_db(); c = conn.cursor()
    c.execute("SELECT * FROM otp_store WHERE phone=? AND otp=? AND used=0 ORDER BY created_at DESC LIMIT 1",(phone,otp))
    row = c.fetchone()
    if not row: conn.close(); return jsonify({'success':False,'error':'Invalid or expired OTP'}), 400
    if datetime.datetime.fromisoformat(row['expires_at']) < datetime.datetime.now():
        conn.close(); return jsonify({'success':False,'error':'OTP expired'}), 400
    c.execute("UPDATE otp_store SET used=1 WHERE id=?",(row['id'],))
    uid = 'phone_'+phone.replace('+','').replace(' ','')
    c.execute("INSERT OR IGNORE INTO users (uid,phone,auth_provider) VALUES (?,?,'otp')",(uid,phone))
    c.execute("SELECT * FROM users WHERE uid=?",(uid,)); user = dict(c.fetchone())
    session['uid'] = uid
    conn.commit(); conn.close()
    return jsonify({'success':True,'user':user})

@app.route('/api/profile/save', methods=['POST'])
def save_profile():
    # Support JSON, multipart/form-data, and regular form posts
    if request.content_type and ('multipart/form-data' in request.content_type or 'application/x-www-form-urlencoded' in request.content_type):
        d = request.form.to_dict()
    else:
        d = request.get_json(force=True) or {}
    uid = d.get('user_uid','')
    if not uid: return jsonify({'success':False,'error':'user_uid required'}), 400

    # Save uploaded documents
    saved_files = {}
    for field in ['gst_doc', 'pan_doc', 'reg_doc']:
        f = request.files.get(field)
        if f and allowed_file(f.filename):
            filename = secure_filename(f"{uid}_{field}_{f.filename}")
            f.save(os.path.join(UPLOAD_DIR, filename))
            saved_files[field] = filename

    digilocker_verified = 1 if str(d.get('digilocker_verified', '')).lower() in ['1', 'true', 'yes'] else 0
    conn = get_db(); c = conn.cursor()
    c.execute("SELECT gst_doc, pan_doc, reg_doc, digilocker_verified FROM company_profiles WHERE user_uid=?", (uid,))
    existing = c.fetchone()
    gst_doc = saved_files.get('gst_doc') or (existing['gst_doc'] if existing else '')
    pan_doc = saved_files.get('pan_doc') or (existing['pan_doc'] if existing else '')
    reg_doc = saved_files.get('reg_doc') or (existing['reg_doc'] if existing else '')
    if existing and existing['digilocker_verified']:
        digilocker_verified = 1

    profile_status = 'verified' if digilocker_verified else 'pending'
    c.execute('''INSERT INTO company_profiles
        (user_uid,company_name,gstin,sector,address,owner_name,mobile,bee_cert,energy_manager,
         gst_doc,pan_doc,reg_doc,digilocker_verified,profile_status)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        ON CONFLICT(user_uid) DO UPDATE SET
            company_name=excluded.company_name,
            gstin=excluded.gstin,
            sector=excluded.sector,
            address=excluded.address,
            owner_name=excluded.owner_name,
            mobile=excluded.mobile,
            bee_cert=excluded.bee_cert,
            energy_manager=excluded.energy_manager,
            gst_doc=excluded.gst_doc,
            pan_doc=excluded.pan_doc,
            reg_doc=excluded.reg_doc,
            digilocker_verified=excluded.digilocker_verified,
            profile_status=CASE
                WHEN excluded.digilocker_verified=1 THEN 'verified'
                ELSE company_profiles.profile_status
            END''',
        (uid, d.get('company_name',''), d.get('gstin',''), d.get('sector',''),
         d.get('address',''), d.get('owner_name',''), d.get('mobile',''),
         d.get('bee_cert',''), d.get('energy_manager',''),
         gst_doc, pan_doc, reg_doc, digilocker_verified, profile_status))
    c.execute("UPDATE users SET profile_complete=1 WHERE uid=?",(uid,))
    conn.commit(); conn.close()
    docs_saved = [k for k in saved_files]
    return jsonify({
        'success': True,
        'status': profile_status,
        'message': 'Profile saved successfully.',
        'docs_saved': docs_saved
    })

@app.route('/api/profile/upload-doc', methods=['POST'])
def upload_doc():
    """Dedicated endpoint for uploading individual verification documents"""
    uid = request.form.get('user_uid','')
    doc_type = request.form.get('doc_type','')  # gst_doc | pan_doc | reg_doc
    if not uid or doc_type not in ['gst_doc','pan_doc','reg_doc']:
        return jsonify({'success':False,'error':'user_uid and valid doc_type required'}), 400
    f = request.files.get('file')
    if not f or not allowed_file(f.filename):
        return jsonify({'success':False,'error':'No valid file provided (pdf/jpg/png only)'}), 400
    filename = secure_filename(f"{uid}_{doc_type}_{f.filename}")
    f.save(os.path.join(UPLOAD_DIR, filename))
    conn = get_db(); c = conn.cursor()
    c.execute(f"UPDATE company_profiles SET {doc_type}=? WHERE user_uid=?", (filename, uid))
    if c.rowcount == 0:
        c.execute(f"INSERT OR IGNORE INTO company_profiles (user_uid,{doc_type}) VALUES (?,?)", (uid, filename))
    conn.commit(); conn.close()
    return jsonify({'success':True,'filename':filename,'doc_type':doc_type})

@app.route('/api/profile/get/<uid>', methods=['GET'])
def get_profile(uid):
    conn = get_db(); c = conn.cursor()
    c.execute("SELECT * FROM company_profiles WHERE user_uid=?",(uid,))
    row = c.fetchone(); conn.close()
    if row: return jsonify({'found':True,'profile':dict(row)})
    return jsonify({'found':False})

@app.route('/api/profile/digilocker-verify', methods=['POST'])
def digilocker_verify():
    """Simulates DigiLocker GSTIN + PAN verification"""
    d = request.get_json(force=True); uid = d.get('user_uid','')
    gstin = d.get('gstin','')
    # Simulate: accept any 15-char GSTIN
    if len(gstin) != 15:
        return jsonify({'success':False,'error':'Invalid GSTIN format (must be 15 characters)'})
    conn = get_db(); c = conn.cursor()
    c.execute("UPDATE company_profiles SET digilocker_verified=1, profile_status='verified' WHERE user_uid=?",(uid,))
    if c.rowcount == 0:
        c.execute("INSERT INTO company_profiles (user_uid, gstin, digilocker_verified, profile_status) VALUES (?, ?, 1, 'verified')", (uid, gstin))
    conn.commit(); conn.close()
    return jsonify({'success':True,'message':'DigiLocker verification successful','status':'verified'})

# ══════════════════════════════════
# CORE PLATFORM ENDPOINTS (unchanged)
# ══════════════════════════════════

@app.route('/api/calculate', methods=['POST'])
def calculate():
    d=request.get_json(force=True)
    e=float(d.get('electricity',0)); f=float(d.get('fuel',0)); t=float(d.get('transport',0))
    p=float(d.get('production',1)) or 1
    fe=float(d.get('ef_electricity',0.82)); ff=float(d.get('ef_fuel',2.31)); ft=float(d.get('ef_transport',0.12))
    co2_e=e*fe; co2_f=f*ff; co2_t=t*ft; total=co2_e+co2_f+co2_t
    credits=total/1000; value=credits*800; score=max(0,min(100,round(100-total/500,1))); mx=max(total,1)
    tips={'fuel':{'icon':'⛽','title':'Reduce Fuel Consumption','text':f'Fuel is your highest emission source. CNG conversion earns ~{round(co2_f*0.15/1000,3)} extra credits/month.'},
          'elec':{'icon':'⚡','title':'Optimise Electricity Use','text':'Install LED lighting and rooftop solar. Eligible for MNRE subsidy under PM-KUSUM scheme.'},
          'trans':{'icon':'🚛','title':'Greener Logistics','text':'Consolidate shipments and explore EVs. FAME II offers subsidies for commercial EVs.'},
          'good':{'icon':'🌿','title':'Excellent Performance!','text':'Emissions well-managed. Explore voluntary carbon trading via Verra VCS or Gold Standard.'}}
    src='fuel' if(co2_f>co2_e and co2_f>co2_t) else 'elec' if co2_e>co2_t else 'good' if total<500 else 'trans'
    return jsonify({'co2_electricity':round(co2_e,2),'co2_fuel':round(co2_f,2),'co2_transport':round(co2_t,2),
        'co2_total':round(total,2),'credits':round(credits,3),'credit_value':round(value,2),
        'green_score':score,'sec':round(total/p,2),'pct_elec':round(co2_e/mx*100,1),
        'pct_fuel':round(co2_f/mx*100,1),'pct_trans':round(co2_t/mx*100,1),'tip':tips[src],
        'bee_status':'⚠️ Above recommended threshold. SEC target may be at risk.' if total>5000 else '✅ Within BEE target range. ESCert generation supported.',
        'annual':{'co2':round(total*12/1000,2),'credits':round(credits*12,3),'value':round(value*12,2)}})

@app.route('/api/save-emission', methods=['POST'])
def save_emission():
    d=request.get_json(force=True); res=d.get('result',{})
    conn=get_db(); c=conn.cursor()
    c.execute('''INSERT INTO emissions (company_id,period,electricity,fuel,transport,production,
        co2_electricity,co2_fuel,co2_transport,co2_total,credits,credit_value,green_score,ef_electricity,ef_fuel,ef_transport)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
        (1,d.get('period','FY 2024-25'),d.get('electricity',0),d.get('fuel',0),d.get('transport',0),d.get('production',1),
         res.get('co2_electricity',0),res.get('co2_fuel',0),res.get('co2_transport',0),res.get('co2_total',0),
         res.get('credits',0),res.get('credit_value',0),res.get('green_score',0),0.82,2.31,0.12))
    em_id=c.lastrowid; tid=gen_token(); tx=gen_hash(); blk=random.randint(4891204,4999999)
    c.execute("INSERT INTO credits (token_id,company_id,company_name,sector,amount,price_per_credit,status,tx_hash,block_number,emission_id) VALUES (?,1,'Rajan Industries Pvt. Ltd.','Small Scale Industry',?,800,'active',?,?)",
        (tid,res.get('credits',0),tx,blk,em_id))
    c.execute("INSERT INTO portfolio (company_id,token_id,source,amount,buy_price,current_price) VALUES (1,?,'Emission Reduction',?,800,800)",
        (tid,res.get('credits',0)))
    conn.commit(); conn.close()
    return jsonify({'success':True,'token_id':tid,'tx_hash':tx,'block':blk})

@app.route('/api/marketplace', methods=['GET'])
def marketplace():
    conn=get_db(); c=conn.cursor()
    c.execute("SELECT token_id,company_name,sector,amount,price_per_credit,verified FROM credits WHERE status='active' ORDER BY created_at DESC")
    rows=c.fetchall(); conn.close()
    icons={'Iron & Steel':'⚙️','Textile':'🧵','Pharmaceutical':'💊','Agriculture':'🌾','Cold Storage':'🧊','Cement':'🪨','Small Scale Industry':'🏭'}
    colors={'Iron & Steel':'#eef3ea','Textile':'#eaf0f5','Pharmaceutical':'#faf5ea','Agriculture':'#eef3ea','Cold Storage':'#eaf0f5','Cement':'#f5f0ea','Small Scale Industry':'#f0f5ea'}
    seen=set(); result=[]
    for r in rows:
        if r['company_name'] in seen: continue
        seen.add(r['company_name'])
        result.append({'token_id':r['token_id'],'name':r['company_name'],'sector':r['sector'],'credits':r['amount'],
            'price':r['price_per_credit'],'verified':bool(r['verified']),'icon':icons.get(r['sector'],'🏭'),
            'color':colors.get(r['sector'],'#f0f5ea'),'score':random.randint(65,95)})
    return jsonify(result)

@app.route('/api/buy', methods=['POST'])
def buy_credit():
    d=request.get_json(force=True); token_id=d.get('token_id',''); qty=float(d.get('qty',1)); price=float(d.get('price',800))
    buyer=d.get('buyer','Rajan Industries Pvt. Ltd.')
    conn=get_db(); c=conn.cursor()
    c.execute("SELECT * FROM credits WHERE token_id=? AND status='active'",(token_id,)); credit=c.fetchone()
    if not credit: conn.close(); return jsonify({'success':False,'error':'Credit not found'}),404
    tx=gen_hash(); total_val=round(qty*price,2); fee=round(total_val*0.01,2)
    c.execute("INSERT INTO trades (token_id,from_company,to_company,amount,price_per_credit,total_value,platform_fee,tx_hash,trade_type,status) VALUES (?,?,?,?,?,?,?,?,'BUY','confirmed')",
        (token_id,credit['company_name'],buyer,qty,price,total_val,fee,tx))
    conn.commit(); conn.close()
    return jsonify({'success':True,'tx_hash':tx,'total':total_val,'fee':fee})

@app.route('/api/sell', methods=['POST'])
def sell_credit():
    d=request.get_json(force=True); qty=float(d.get('qty',1)); price=float(d.get('price',800))
    tid=gen_token(); tx=gen_hash(); blk=random.randint(4891204,4999999)
    conn=get_db(); c=conn.cursor()
    c.execute("INSERT INTO credits (token_id,company_id,company_name,sector,amount,price_per_credit,status,tx_hash,block_number) VALUES (?,1,'Rajan Industries Pvt. Ltd.','Small Scale Industry',?,?,'listed',?,?)",
        (tid,qty,price,tx,blk))
    conn.commit(); conn.close()
    return jsonify({'success':True,'token_id':tid,'tx_hash':tx,'listed_price':price})

@app.route('/api/blockchain/transactions', methods=['GET'])
def blockchain_txs():
    conn=get_db(); c=conn.cursor()
    c.execute("SELECT * FROM trades ORDER BY created_at DESC LIMIT 20"); trades=c.fetchall()
    c.execute("SELECT * FROM credits ORDER BY created_at DESC LIMIT 10"); mints=c.fetchall(); conn.close()
    txs=[]
    for t in trades: txs.append({'hash':t['tx_hash'] or gen_hash(),'type':t['trade_type'],'co':f"{t['from_company']} → {t['to_company']}",'amount':f"{t['amount']} credits",'time':t['created_at'][:16]})
    for m in mints[:5]: txs.append({'hash':m['tx_hash'] or gen_hash(),'type':'MINT','co':m['company_name'],'amount':f"+{m['amount']} credits",'time':m['created_at'][:16]})
    txs.sort(key=lambda x:x['time'],reverse=True)
    return jsonify(txs[:15])

@app.route('/api/blockchain/stats', methods=['GET'])
def blockchain_stats():
    conn=get_db(); c=conn.cursor()
    c.execute("SELECT SUM(amount) as total FROM credits"); r=c.fetchone(); conn.close()
    return jsonify({'latest_block':random.randint(4891204,4999999),'total_credits':round(r['total'] or 0,1),'verification_rate':100})

@app.route('/api/blockchain/verify', methods=['POST'])
def verify_credit():
    d=request.get_json(force=True); token=d.get('token','').strip()
    conn=get_db(); c=conn.cursor()
    c.execute("SELECT * FROM credits WHERE token_id=?",(token,)); row=c.fetchone()
    if not row and token.startswith('0x'):
        c.execute("SELECT * FROM credits WHERE tx_hash LIKE ?",(f'%{token[:8]}%',)); row=c.fetchone()
    conn.close()
    if row: return jsonify({'found':True,'token_id':row['token_id'],'status':'Valid','owner':row['company_name'],'amount':row['amount'],'issued_by':'BEE Verification Agency','tx_hash':row['tx_hash'],'block':row['block_number'],'created_at':row['created_at']})
    return jsonify({'found':False,'message':f'Token "{token}" not found on chain.'})

@app.route('/api/portfolio/<int:cid>', methods=['GET'])
def portfolio(cid):
    conn=get_db(); c=conn.cursor()
    c.execute("SELECT * FROM portfolio WHERE company_id=? ORDER BY acquired_at DESC",(cid,)); rows=c.fetchall()
    c.execute("SELECT SUM(amount) as total, SUM(amount*current_price) as value FROM portfolio WHERE company_id=?",(cid,)); s=c.fetchone(); conn.close()
    return jsonify({'holdings':[dict(r) for r in rows],'total_credits':round(s['total'] or 0,3),'total_value':round(s['value'] or 0,2)})

@app.route('/api/report/generate', methods=['POST'])
def generate_report():
    d=request.get_json(force=True)
    elec=float(d.get('electricity',0)); fuel=float(d.get('fuel',0)); trans=float(d.get('transport',0)); prod=float(d.get('production',1)) or 1
    co2_e=elec*0.82; co2_f=fuel*2.31; co2_t=trans*0.12; total=co2_e+co2_f+co2_t; credits=total/1000; sec_val=total/prod
    ref=f"CX-RPT-{random.randint(100000,999999)}"; today=datetime.date.today().strftime('%d %B %Y')
    conn=get_db(); c=conn.cursor()
    c.execute("INSERT INTO reports (company_id,report_ref,period,co2_total,credits,sec_value) VALUES (?,?,?,?,?,?)",
        (1,ref,d.get('period','FY 2024-25'),round(total,2),round(credits,3),round(sec_val,2)))
    conn.commit(); conn.close()
    return jsonify({'ref':ref,'today':today,'co2_e':round(co2_e,2),'co2_f':round(co2_f,2),'co2_t':round(co2_t,2),
        'co2_total':round(total,2),'co2_total_tonnes':round(total/1000,3),'baseline':round(total/1000*1.25,3),
        'reduction':round(total/1000*0.25,3),'credits':round(credits,3),'credit_value':round(credits*800,2),
        'sec':round(sec_val,2),'sec_target':round(sec_val*1.05,2)})

@app.route('/api/scope3/calculate', methods=['POST'])
def scope3():
    d=request.get_json(force=True)
    up=sum(float(d.get(k,0)) for k in ['purchased_goods','upstream_transport','capital_goods'])
    dn=sum(float(d.get(k,0)) for k in ['downstream_transport','end_of_life','customer_use','leased_assets'])
    tot=up+dn
    return jsonify({'upstream':round(up,2),'downstream':round(dn,2),'total':round(tot,2),'credits':round(tot/1000,3)})

@app.route('/api/dashboard/stats', methods=['GET'])
def dashboard_stats():
    conn=get_db(); c=conn.cursor()
    c.execute("SELECT co2_total,credits,credit_value,green_score FROM emissions WHERE company_id=1 ORDER BY created_at DESC LIMIT 6")
    rows=c.fetchall(); conn.close()
    if not rows: return jsonify({'co2':1248,'credits':1.248,'value':8736,'score':74,'change':-12})
    latest=rows[0]; prev=rows[1] if len(rows)>1 else latest
    chg=round((latest['co2_total']-prev['co2_total'])/max(prev['co2_total'],1)*100,1)
    return jsonify({'co2':round(latest['co2_total'],0),'credits':round(latest['credits'],3),'value':round(latest['credit_value'],0),'score':latest['green_score'],'change':chg})

if __name__ == '__main__':
    init_db()
    print("\n"+"="*52)
    print("  🌿 CreditX Backend is RUNNING!")
    print("  Open your browser at:")
    print("  --> http://localhost:8080 <--")
    print("="*52+"\n")
    app.run(debug=False, host='0.0.0.0', port=8080)
