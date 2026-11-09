
import os, sqlite3, json, random, secrets, string
from functools import wraps
from flask import Flask, request, redirect, url_for, session, flash, render_template, abort
from werkzeug.security import generate_password_hash, check_password_hash

APP_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.environ.get("DATABASE_PATH", os.path.join(APP_DIR, "matematika.db"))
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-secret-before-deploying")

def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with db() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS users(
          id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL,
          full_name TEXT NOT NULL, password_hash TEXT NOT NULL,
          role TEXT NOT NULL CHECK(role IN ('teacher','student')),
          active INTEGER NOT NULL DEFAULT 1, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS tests(
          id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL,
          kind TEXT NOT NULL, month INTEGER NOT NULL DEFAULT 1,
          homework_no INTEGER, questions TEXT NOT NULL, active INTEGER NOT NULL DEFAULT 1,
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS attempts(
          id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL,
          test_id INTEGER NOT NULL, score INTEGER NOT NULL, total INTEGER NOT NULL,
          answers TEXT NOT NULL, completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          FOREIGN KEY(user_id) REFERENCES users(id), FOREIGN KEY(test_id) REFERENCES tests(id)
        );
        """)
        teacher_name = os.environ.get("TEACHER_USERNAME", "Gulmira To‘raqulova")
        teacher_pass = os.environ.get("TEACHER_PASSWORD")
        if teacher_pass:
            existing = c.execute("SELECT id FROM users WHERE role='teacher' LIMIT 1").fetchone()
            if not existing:
                c.execute("INSERT INTO users(username,full_name,password_hash,role) VALUES(?,?,?,'teacher')",
                          (teacher_name, teacher_name, generate_password_hash(teacher_pass)))

def login_required(role=None):
    def deco(fn):
        @wraps(fn)
        def wrapped(*args, **kwargs):
            if not session.get("user_id"):
                return redirect(url_for("login"))
            if role and session.get("role") != role:
                abort(403)
            return fn(*args, **kwargs)
        return wrapped
    return deco

def make_questions(count=50):
    rng = random.Random()
    questions = []
    for i in range(count):
        typ = i % 10
        if typ == 0:
            a,b=rng.randint(125,8999),rng.randint(101,999)
            q,ans=f"{a} + {b} = ?",a+b
        elif typ == 1:
            a=rng.randint(500,9999); b=rng.randint(100,a)
            q,ans=f"{a} − {b} = ?",a-b
        elif typ == 2:
            a,b=rng.randint(2,12),rng.randint(2,12)
            q,ans=f"{a} × {b} = ?",a*b
        elif typ == 3:
            b=rng.randint(2,12); ans=rng.randint(2,12); a=b*ans
            q,ans=f"{a} ÷ {b} = ?",ans
        elif typ == 4:
            a,b=rng.randint(10,99),rng.randint(10,99)
            q,ans=f"{a} × {b} = ?",a*b
        elif typ == 5:
            a,b=rng.randint(100,900),rng.randint(10,99)
            q,ans=f"{a} + {b} − 25 = ?",a+b-25
        elif typ == 6:
            a=rng.randint(2,20); b=rng.randint(2,20)
            q,ans=f"{a} × 5 + {b} = ?",a*5+b
        elif typ == 7:
            a,b=rng.randint(2,10),rng.randint(2,10)
            q,ans=f"({a} + {b}) × 3 = ?",(a+b)*3
        elif typ == 8:
            a,b=rng.randint(2,20),rng.randint(2,20)
            q,ans=f"{a}² + {b} = ?",a*a+b
        else:
            a,b=rng.randint(2,15),rng.randint(2,15)
            q,ans=f"Perimetri {a} sm va {b} sm bo‘lgan to‘g‘ri to‘rtburchak: 2 × ({a} + {b}) = ?",2*(a+b)
        wrong=set()
        while len(wrong)<3:
            v=ans+rng.choice([-20,-10,-5,-3,-2,-1,1,2,3,5,10,20])
            if v>=0 and v!=ans: wrong.add(v)
        opts=list(wrong)+[ans]; rng.shuffle(opts)
        questions.append({"q":q,"options":[str(x) for x in opts],"answer":str(ans)})
    return questions

BASE = """
<!doctype html><html lang="uz"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Matematika olami</title><link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}"></head>
<body><header><a class="brand" href="{{ url_for('home') }}">✦ Matematika olami</a>
{% if session.get('user_id') %}<span>{{ session.get('full_name') }}</span><a href="{{ url_for('logout') }}">Chiqish</a>{% endif %}</header>
<main>{% with messages=get_flashed_messages() %}{% if messages %}<div class="notice">{% for m in messages %}{{m}}{% endfor %}</div>{% endif %}{% endwith %}
{{ body|safe }}</main><footer>4-sinf matematika to‘garagi · Har bir qadam — yutuq!</footer></body></html>
"""

def page(body, **ctx):
    return render_template_string(BASE, body=render_template_string(body, **ctx))

@app.route("/")
def home():
    if not session.get("user_id"): return redirect(url_for("login"))
    return redirect(url_for("teacher" if session["role"]=="teacher" else "student"))

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method=="POST":
        username=request.form.get("username","").strip()
        password=request.form.get("password","")
        with db() as c:
            u=c.execute("SELECT * FROM users WHERE username=? AND active=1",(username,)).fetchone()
        if u and check_password_hash(u["password_hash"],password):
            session.clear(); session.update(user_id=u["id"],role=u["role"],full_name=u["full_name"])
            return redirect(url_for("teacher" if u["role"]=="teacher" else "student"))
        flash("Login yoki parol noto‘g‘ri, yoki hisob faol emas.")
    return page("""<section class="login card"><h1>Xush kelibsiz!</h1><p>Matematika olamiga kirish uchun login va parolingizni yozing.</p>
    <form method="post"><label>Login</label><input name="username" required autocomplete="username">
    <label>Parol</label><input type="password" name="password" required autocomplete="current-password">
    <button>Kirish</button></form></section>""")

@app.route("/logout")
def logout():
    session.clear(); return redirect(url_for("login"))

@app.route("/teacher")
@login_required("teacher")
def teacher():
    with db() as c:
        students=c.execute("SELECT * FROM users WHERE role='student' ORDER BY full_name").fetchall()
        tests=c.execute("SELECT * FROM tests ORDER BY month, homework_no, id DESC").fetchall()
        attempts=c.execute("""SELECT a.*,u.full_name,t.title FROM attempts a JOIN users u ON u.id=a.user_id
                           JOIN tests t ON t.id=a.test_id ORDER BY a.completed_at DESC LIMIT 100""").fetchall()
        stats=c.execute("SELECT COUNT(*) n FROM users WHERE role='student' AND active=1").fetchone()["n"]
    return page("""<h1>O‘qituvchi kabineti</h1><div class="stats"><div class="card"><b>{{stats}}</b><small>Faol o‘quvchi</small></div>
    <div class="card"><b>{{tests|length}}</b><small>Testlar</small></div></div>
    <div class="card"><h2>Yangi o‘quvchi qo‘shish</h2><form method="post" action="{{url_for('add_student')}}" class="grid">
    <input name="full_name" placeholder="O‘quvchining ism-familiyasi" required><input name="username" placeholder="Yangi login" required>
    <input name="password" placeholder="Vaqtinchalik parol" required minlength="6"><button>O‘quvchini yaratish</button></form></div>
    <div class="card"><h2>Test yaratish</h2><form method="post" action="{{url_for('create_test')}}" class="grid">
    <input name="title" placeholder="Masalan: 1-oy, 1-uy ishi" required>
    <select name="kind"><option value="homework">Uy ishi (50 ta savol)</option><option value="lesson">Dars testi (20 ta savol)</option></select>
    <select name="month">{% for n in range(1,5) %}<option value="{{n}}">{{n}}-oy</option>{% endfor %}</select>
    <select name="homework_no">{% for n in range(1,9) %}<option value="{{n}}">{{n}}-uy ishi</option>{% endfor %}</select>
    <button>Test yaratish</button></form><p class="muted">Uy ishi avtomatik 50 ta, dars testi 20 ta matematik savoldan tuziladi.</p></div>
    <div class="card"><h2>O‘quvchilar</h2><div class="tablewrap"><table><tr><th>Ism</th><th>Login</th><th>Holat</th><th>Amal</th></tr>
    {% for s in students %}<tr><td>{{s.full_name}}</td><td>{{s.username}}</td><td>{{'Faol' if s.active else 'Bloklangan'}}</td><td>
    <form method="post" action="{{url_for('toggle_student',uid=s.id)}}"><button class="secondary">{{'Bloklash' if s.active else 'Faollashtirish'}}</button></form></td></tr>{% else %}<tr><td colspan="4">Hozircha o‘quvchi yo‘q.</td></tr>{% endfor %}</table></div></div>
    <div class="card"><h2>Testlar</h2><ul>{% for t in tests %}<li>{{t.title}} · {{'Uy ishi' if t.kind=='homework' else 'Dars testi'}} · {{t.month}}-oy · {{json.loads(t.questions)|length}} savol</li>{% else %}<li>Testlar hali yaratilmagan.</li>{% endfor %}</ul></div>
    <div class="card"><h2>So‘nggi natijalar</h2><div class="tablewrap"><table><tr><th>O‘quvchi</th><th>Test</th><th>Natija</th><th>Sana</th></tr>
    {% for a in attempts %}<tr><td>{{a.full_name}}</td><td>{{a.title}}</td><td>{{a.score}} / {{a.total}}</td><td>{{a.completed_at}}</td></tr>{% else %}<tr><td colspan="4">Hali topshirilgan test yo‘q.</td></tr>{% endfor %}</table></div></div>""",
    students=students,tests=tests,attempts=attempts,stats=stats,json=json)

@app.route("/teacher/student/add",methods=["POST"])
@login_required("teacher")
def add_student():
    name=request.form.get("full_name","").strip(); username=request.form.get("username","").strip()
    password=request.form.get("password","")
    if not name or not username or len(password)<6: flash("Barcha maydonlarni to‘ldiring. Parol kamida 6 belgidan iborat bo‘lsin.")
    else:
        try:
            with db() as c: c.execute("INSERT INTO users(username,full_name,password_hash,role) VALUES(?,?,?,'student')",
                                      (username,name,generate_password_hash(password)))
            flash(f"{name} uchun hisob yaratildi. Login va parolni o‘quvchiga xavfsiz yetkazing.")
        except sqlite3.IntegrityError: flash("Bu login band. Boshqa login tanlang.")
    return redirect(url_for("teacher"))

@app.route("/teacher/student/<int:uid>/toggle",methods=["POST"])
@login_required("teacher")
def toggle_student(uid):
    with db() as c:
        c.execute("UPDATE users SET active=CASE active WHEN 1 THEN 0 ELSE 1 END WHERE id=? AND role='student'",(uid,))
    flash("O‘quvchi hisobi holati yangilandi.")
    return redirect(url_for("teacher"))

@app.route("/teacher/test/create",methods=["POST"])
@login_required("teacher")
def create_test():
    title=request.form.get("title","").strip()
    kind=request.form.get("kind","homework")
    month=max(1,min(4,int(request.form.get("month",1))))
    no=max(1,min(8,int(request.form.get("homework_no",1))))
    if not title: flash("Test nomini kiriting.")
    else:
        qs=make_questions(50 if kind=="homework" else 20)
        with db() as c:
            c.execute("INSERT INTO tests(title,kind,month,homework_no,questions) VALUES(?,?,?,?,?)",
                      (title,kind,month,no,json.dumps(qs,ensure_ascii=False)))
        flash(f"{title} yaratildi: {len(qs)} ta savol.")
    return redirect(url_for("teacher"))

@app.route("/student")
@login_required("student")
def student():
    with db() as c:
        tests=c.execute("SELECT * FROM tests WHERE active=1 ORDER BY month,kind,homework_no").fetchall()
        attempts=c.execute("SELECT test_id,score,total,completed_at FROM attempts WHERE user_id=? ORDER BY completed_at DESC",(session["user_id"],)).fetchall()
        latest={a["test_id"]:a for a in attempts}
        all_attempts=c.execute("SELECT SUM(score) s,SUM(total) t,COUNT(*) n FROM attempts WHERE user_id=?",(session["user_id"],)).fetchone()
    return page("""<h1>Salom, {{session_name}}!</h1><p class="muted">Darslaringiz va uy vazifalaringiz shu yerda.</p>
    <div class="stats"><div class="card"><b>{{all_attempts.n or 0}}</b><small>Topshirilgan test</small></div><div class="card"><b>{{(100*all_attempts.s/all_attempts.t)|round|int if all_attempts.t else 0}}%</b><small>Umumiy natija</small></div></div>
    {% for m in range(1,5) %}<h2>{{m}}-oy</h2><div class="cards">{% for t in tests if t.month==m %}
    <div class="card"><small>{{'UY ISHI' if t.kind=='homework' else 'DARSLIK TESTI'}}</small><h3>{{t.title}}</h3><p>{{json.loads(t.questions)|length}} ta savol</p>
    {% if t.id in latest %}<p class="result">Oxirgi natija: {{latest[t.id].score}} / {{latest[t.id].total}}</p>{% endif %}
    <a class="button" href="{{url_for('take_test',tid=t.id)}}">Testni boshlash</a></div>{% else %}<div class="card muted">Bu oy uchun test hali ochilmagan.</div>{% endfor %}</div>{% endfor %}""",
    tests=tests,latest=latest,all_attempts=all_attempts,session_name=session["full_name"],json=json)

@app.route("/test/<int:tid>",methods=["GET","POST"])
@login_required("student")
def take_test(tid):
    with db() as c: t=c.execute("SELECT * FROM tests WHERE id=? AND active=1",(tid,)).fetchone()
    if not t: abort(404)
    qs=json.loads(t["questions"])
    if request.method=="POST":
        answers=[]; score=0
        for i,q in enumerate(qs):
            ans=request.form.get(f"q{i}","")
            answers.append(ans)
            if ans==q["answer"]: score+=1
        with db() as c:
            c.execute("INSERT INTO attempts(user_id,test_id,score,total,answers) VALUES(?,?,?,?,?)",
                      (session["user_id"],tid,score,len(qs),json.dumps(answers)))
        pct=round(score*100/len(qs))
        return page("""<section class="card center"><h1>Test yakunlandi!</h1><div class="big">{{score}} / {{total}}</div><h2>{{pct}}%</h2>
        <p>{{'Ajoyib natija! Barakalla!' if pct>=90 else 'Yaxshi harakat! Xatolarni ko‘rib, yana mashq qiling.'}}</p><a class="button" href="{{url_for('student')}}">Kabinetga qaytish</a></section>""",
        score=score,total=len(qs),pct=pct)
    return page("""<h1>{{t.title}}</h1><p class="muted">{{qs|length}} ta savol. Har bir savolga bitta javob belgilang.</p>
    <form method="post">{% for q in qs %}{% set qindex = loop.index0 %}<section class="card question"><h3>{{loop.index}}. {{q.q}}</h3>
    {% for op in q.options %}<label class="option"><input type="radio" name="q{{qindex}}" value="{{op}}" required> {{op}}</label>{% endfor %}</section>{% endfor %}
    <button class="submit">Javoblarni yuborish</button></form>""",t=t,qs=qs)

@app.errorhandler(403)
def forbidden(e): return "Bu sahifaga kirish huquqingiz yo‘q.",403
@app.errorhandler(404)
def missing(e): return "Sahifa topilmadi.",404

init_db()
if __name__=="__main__":
    app.run(host="0.0.0.0",port=int(os.environ.get("PORT",5000)),debug=False)
