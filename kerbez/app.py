import csv, io, os, re, sqlite3
from datetime import datetime
from functools import wraps
from urllib.parse import urlparse
from flask import Flask, Response, g, redirect, render_template, request, url_for

from i18n import DEFAULT_LANG, HTML_LANG, LANGS, get_content

app = Flask(__name__)

DB_PATH = os.environ.get("DB_PATH", os.path.join(os.path.dirname(__file__), "applications.db"))
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "")
FORM_URL = os.environ.get("FORM_URL", "https://docs.google.com/forms/d/e/1FAIpQLSeyfrwj2OZJPI-Ab31WmgB0vnpLHEoVW07fYXKAXLofgGlbJw/viewform")  # Google Form сілтемесі (болса, өтінім батырмалары соған апарады)

PHONE_RAW = "77029033490"
PHONE_VIEW = "+7 702 903 34 90"


# ------------------------------------------------------------ тіл таңдау
LANG_COOKIE = "kc_lang"  # ескі "lang" cookie-ді елемейміз (ол бір жылға сақталып қалған болуы мүмкін)


def from_own_site():
    """Келуші сайттың өз ішінде жүр ме (бір беттен екінші бетке)? Сырттан/тікелей кірсе — жоқ."""
    ref = request.referrer
    return bool(ref) and urlparse(ref).netloc == request.host


@app.before_request
def pick_language():
    if request.path.startswith("/admin"):  # админ беті әрқашан қазақша
        g.lang = DEFAULT_LANG
        return
    q = request.args.get("lang")
    c = request.cookies.get(LANG_COOKIE)
    if q in LANGS:
        g.lang = q
    elif c in LANGS and from_own_site():  # тек сайт ішінде жүргенде таңдалған тілді сақтаймыз
        g.lang = c
    else:  # сайтқа жаңа кірсе — әрқашан қазақша
        g.lang = DEFAULT_LANG


@app.after_request
def remember_language(resp):
    if request.path.startswith("/static"):
        return resp
    q = request.args.get("lang")
    if q in LANGS and not request.path.startswith("/admin"):
        resp.set_cookie(LANG_COOKIE, q, samesite="Lax")
    if request.cookies.get("lang"):  # ескі cookie-ді өшіреміз
        resp.delete_cookie("lang")
    if resp.mimetype == "text/html":
        resp.headers["Cache-Control"] = "private, no-cache"  # тіл келушіге байланысты, кэшке түспесін
    return resp


@app.context_processor
def inject_i18n():
    lang = g.get("lang", DEFAULT_LANG)
    c = get_content(lang)
    return dict(s=c["site"], t=c["ui"], lang=lang, langs=LANGS, html_lang=HTML_LANG[lang], phone=PHONE_VIEW)


# ------------------------------------------------------------ дерекқор
def db():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    con.execute("""CREATE TABLE IF NOT EXISTS applications(
        id INTEGER PRIMARY KEY AUTOINCREMENT, created TEXT, full_name TEXT, faculty TEXT,
        course TEXT, phone TEXT, kind TEXT, team TEXT, idea TEXT)""")
    cols = [r[1] for r in con.execute("PRAGMA table_info(applications)")]
    if "drive_link" not in cols:
        con.execute("ALTER TABLE applications ADD COLUMN drive_link TEXT")
    return con


def admin_only(f):
    @wraps(f)
    def wrap(*args, **kw):
        auth = request.authorization
        if not ADMIN_PASSWORD or not auth or auth.password != ADMIN_PASSWORD:
            return Response("Кіру үшін құпия сөз қажет", 401, {"WWW-Authenticate": 'Basic realm="Admin"'})
        return f(*args, **kw)
    return wrap


def form_link():
    """Google Form-ға тілді (интерфейс) көрсететін hl параметрін қосамыз."""
    if not FORM_URL:
        return ""
    sep = "&" if "?" in FORM_URL else "?"
    return f"{FORM_URL}{sep}hl={g.lang}"


# ------------------------------------------------------------ беттер
@app.route("/")
def index():
    apply_url = form_link() or url_for("apply")
    video = os.path.exists(os.path.join(app.static_folder, "video", "podium.mp4"))  # static/video/podium.mp4 болса, фонға қосылады
    return render_template("index.html", apply_url=apply_url, external=bool(FORM_URL), has_video=video)


@app.route("/apply", methods=["GET", "POST"])
def apply():
    if FORM_URL:  # Google Form-ға тікелей жібереміз
        return redirect(form_link())
    t = get_content(g.lang)["ui"]
    form, errors = {}, {}
    if request.method == "POST":
        form = {k: request.form.get(k, "").strip() for k in
                ("full_name", "faculty", "course", "phone", "kind", "team", "idea", "drive_link")}
        if request.form.get("website"):  # honeypot
            return redirect(url_for("thanks"))
        if len(form["full_name"].split()) < 2:
            errors["full_name"] = t["e_name"]
        if len(form["faculty"]) < 2:
            errors["faculty"] = t["e_faculty"]
        if form["course"] not in {"1", "2", "3", "4", "5", "6"}:
            errors["course"] = t["e_course"]
        if len(re.sub(r"\D", "", form["phone"])) < 10:
            errors["phone"] = t["e_phone"]
        if form["kind"] not in {"Жеке", "Топтық"}:  # дерекқорда әрқашан қазақша мән сақталады
            errors["kind"] = t["e_kind"]
        if form["kind"] == "Топтық" and not form["team"]:
            errors["team"] = t["e_team"]
        if not re.match(r"^https?://(drive|docs)\.google\.com/", form["drive_link"]):
            errors["drive_link"] = t["e_drive"]
        if not request.form.get("agree"):
            errors["agree"] = t["e_agree"]
        if not errors:
            con = db()
            con.execute("INSERT INTO applications(created,full_name,faculty,course,phone,kind,team,idea,drive_link) VALUES(?,?,?,?,?,?,?,?,?)",
                        (datetime.now().strftime("%Y-%m-%d %H:%M"), form["full_name"], form["faculty"], form["course"],
                         form["phone"], form["kind"], form["team"] if form["kind"] == "Топтық" else "", form["idea"], form["drive_link"]))
            con.commit()
            con.close()
            return redirect(url_for("thanks"))
    return render_template("apply.html", form=form, errors=errors)


@app.route("/thanks")
def thanks():
    return render_template("thanks.html")


@app.route("/admin")
@admin_only
def admin():
    rows = db().execute("SELECT * FROM applications ORDER BY id DESC").fetchall()
    return render_template("admin.html", rows=rows)


@app.route("/admin/export.csv")
@admin_only
def export():
    rows = db().execute("SELECT * FROM applications ORDER BY id").fetchall()
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["№", "Күні", "Аты-жөні", "Факультет", "Курс", "Телефон", "Түрі", "Топ мүшелері", "Идея", "Drive сілтемесі"])
    w.writerows([list(r) for r in rows])
    return Response("\ufeff" + buf.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition": "attachment; filename=applications.csv"})


if __name__ == "__main__":
    app.run(debug=True)
