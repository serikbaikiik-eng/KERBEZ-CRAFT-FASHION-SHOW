import csv, io, os, re, sqlite3
from datetime import datetime
from functools import wraps
from urllib.parse import quote
from flask import Flask, Response, redirect, render_template, request, url_for

app = Flask(__name__)

DB_PATH = os.environ.get("DB_PATH", os.path.join(os.path.dirname(__file__), "applications.db"))
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "")
FORM_URL = os.environ.get("FORM_URL", "https://docs.google.com/forms/d/e/1FAIpQLSeyfrwj2OZJPI-Ab31WmgB0vnpLHEoVW07fYXKAXLofgGlbJw/viewform")  # Google Form сілтемесі (болса, өтінім батырмалары соған апарады)


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

PHONE_RAW = "77029033490"
PHONE_VIEW = "+7 702 903 34 90"
SITE = {
    "name": "KERBEZ CRAFT",
    "title": "KERBEZ CRAFT FASHION SHOW",
    "tagline": "Өткеннен нәр алған рух. Болашаққа бағытталған сән.",
    "about": [
        "KERBEZ CRAFT FASHION SHOW – бұл жай ғана сән көрсетілімі емес. Бұл – қазақ халқының бай тарихи мұрасын, ұлттық болмысын және қазақ қыздарының қайсар рухын заманауи сән өнері арқылы танытатын шығармашылық фестиваль.",
        "Жобаның басты идеясы – тарих пен заманауи сәнді үйлестіре отырып, ұлттық құндылықтарды жаңа қырынан көрсету. Фестиваль студенттердің шығармашылық әлеуетін ашуға, жеке қабілеттерін дамытуға және өз идеяларын нақты сәндік бұйымдар арқылы жүзеге асыруға мүмкіндік береді.",
    ],
    "theme_title": "Биылғы тақырып – «Тұмар рухы»",
    "theme": [
        "«Тұмар рухы» – ежелгі сақ дәуірінен, Томирис патшайымның қайсар мінезі мен өр рухынан шабыт алған тақырып.",
        "Бұл тақырып арқылы қазақ әйелінің ішкі күшін, батылдығын, еркіндігін және сұлулығын бейнелеу көзделеді. Қатысушыларға сақ мәдениетінің ою-өрнектері, тарихи әшекейлері, киім үлгілері мен ұлттық символикасын заманауи этностильмен үйлестіріп, өзіндік дизайнерлік көзқарасын ұсыну ұсынылады.",
    ],
    "idea": "Тұмар – қорғаныш пен киелі символ ғана емес, ұлттық рухтың, әйел болмысы мен ішкі күштің бейнесі.",
    "goals": [
        "Қазақ халқының тарихи және мәдени мұрасын сән өнері арқылы дәріптеу.",
        "Қазақ әйелінің рухын, қайсарлығы мен ерекше болмысын көрсету.",
        "Ұлттық нақыш пен заманауи сән бағыттарын үйлестіру.",
        "Студенттердің шығармашылық ойлауын және дизайнерлік қабілеттерін дамыту.",
        "Жас дизайнерлерге өз туындыларын таныстыруға мүмкіндік беру.",
    ],
    "perks": [
        ("Дайын портфолио", "Өз жұмыстарыңызды болашақ оқу, тәжірибе және кәсіби мансап үшін портфолиоға енгізу мүмкіндігі."),
        ("Кәсіби тәжірибе", "Киім коллекциясын әзірлеу, модель жасау және дайын бұйымды өндіру үдерісінен тәжірибе жинақтау."),
        ("Шығармашылық орта", "Жаңа таныстықтар орнату, өзге дизайнерлермен тәжірибе алмасу және шығармашылық байланыс қалыптастыру."),
        ("Мастер-кластар", "Тәжірибелі мамандардан білім алып, сән индустриясының қыр-сырын меңгеру."),
        ("Сертификат және марапат", "Фестивальге қатысқаны үшін мадақтама және болашақ кәсіби қызметте қолдануға болатын жетістікті растайтын құжаттар алу."),
    ],
    "conditions": [
        "Фестивальге университеттің барлық курс студенттері қатыса алады.",
        "Жеке және топтық жұмыс форматына рұқсат етіледі.",
        "Бір топтағы қатысушылар саны 3 адамнан аспауы тиіс.",
        "Ұсынылатын жұмыстар фестивальдің «Тұмар рухы» тақырыбына және этностиль бағытына сәйкес болуы қажет.",
    ],
    "stages": [
        {
            "tag": "I кезең",
            "name": "Авторлық эскиздер топтамасын әзірлеу",
            "text": "Қатысушы «Тұмар рухы» тақырыбына сәйкес кемінде 5–7 киім эскизін ұсынуы қажет.",
            "list_title": "Эскизге қойылатын талаптар",
            "list": [
                "Формат: А4 немесе А3.",
                "Бейнелеу материалдары: еркін таңдалады. Гуашь, акварель, қарындаш, фломастер, коллаж және аппликация материалдарын қолдануға болады.",
                "Тақырыптық сәйкестік: сақ дәуірінің эстетикасы мен этностиль элементтері көрініс табуы тиіс.",
                "Жұмыс авторлық және шығармашылық идеяға негізделуі қажет.",
            ],
        },
        {
            "tag": "II кезең",
            "name": "Эскиз негізінде дайын киім үлгісін жасау",
            "text": "Бірінші кезеңнен өткен қатысушылар өздері ұсынған эскиздердің ішінен киім үлгісін таңдап, оны толыққанды дайын бұйым ретінде тігуі қажет.",
            "list_title": "Негізгі шарттар",
            "list": [
                "Киім үлгісі бірінші кезеңде ұсынылған авторлық эскизге сәйкес болуы керек.",
                "Материалдар мен тігінге қажетті шығындарды қатысушы өз қаражаты есебінен қамтамасыз етеді.",
                "Дайын бұйым фестивальдің қорытынды сән көрсетілімінде ұсынылады.",
                "Дайын өнім қатысушының жеке меншігінде қалады. Университет дайын бұйымға меншік құқығын талап етпейді.",
            ],
        },
    ],
    "deadline_label": "II кезеңнің соңғы мерзімі",
    "deadline": "22.02.2027",
    "deadline_iso": "2027-02-22",
    "deadline_words": "2027 жылғы 22 ақпан",
    "who": ["Университеттің барлық курс студенттері", "Жеке қатысушылар", "3 адамға дейінгі шығармашылық топтар"],
    "criteria": ["Тақырыпқа сәйкестік", "Идеяның ерекшелігі", "Шығармашылық шешім", "Орындалу сапасы"],
    "cta_title": "Бізбен бірге жаңа тарих жаса!",
    "cta_text": "Сенің идеяң – болашақ коллекцияның бастауы. Өз қиялыңды шектеме, ұлттық мұрадан шабыт ал және өзіңнің дизайнерлік көзқарасыңды әлемге таныт!",
    "cta_final": "Өз рухыңды көрсет. Өз қолтаңбаңды қалдыр!",
    "footer": "KERBEZ CRAFT FASHION SHOW – Тұмар рухын сән арқылы жаңғыртатын шығармашылық алаң.",
}


@app.route("/")
def index():
    apply_url = FORM_URL or url_for("apply")
    return render_template("index.html", s=SITE, phone=PHONE_VIEW, apply_url=apply_url, external=bool(FORM_URL))


@app.route("/apply", methods=["GET", "POST"])
def apply():
    if FORM_URL:  # Google Form-ға тікелей жібереміз
        return redirect(FORM_URL)
    form, errors = {}, {}
    if request.method == "POST":
        form = {k: request.form.get(k, "").strip() for k in
                ("full_name", "faculty", "course", "phone", "kind", "team", "idea", "drive_link")}
        if request.form.get("website"):  # honeypot
            return redirect(url_for("thanks"))
        if len(form["full_name"].split()) < 2:
            errors["full_name"] = "Аты-жөніңізді толық жазыңыз (тегі мен аты)."
        if len(form["faculty"]) < 2:
            errors["faculty"] = "Факультетті жазыңыз."
        if form["course"] not in {"1", "2", "3", "4", "5", "6"}:
            errors["course"] = "Курсты таңдаңыз."
        if len(re.sub(r"\D", "", form["phone"])) < 10:
            errors["phone"] = "Телефон нөмірін дұрыс жазыңыз, мысалы +7 700 000 00 00."
        if form["kind"] not in {"Жеке", "Топтық"}:
            errors["kind"] = "Қатысу түрін таңдаңыз."
        if form["kind"] == "Топтық" and not form["team"]:
            errors["team"] = "Топ мүшелерінің аты-жөнін жазыңыз (өзіңізді қоспағанда 2 адамға дейін)."
        if not re.match(r"^https?://(drive|docs)\.google\.com/", form["drive_link"]):
            errors["drive_link"] = "Google Drive сілтемесін жазыңыз (drive.google.com/... деп басталуы керек)."
        if not request.form.get("agree"):
            errors["agree"] = "Ережелермен келісетініңізді белгілеңіз."
        if not errors:
            con = db()
            con.execute("INSERT INTO applications(created,full_name,faculty,course,phone,kind,team,idea,drive_link) VALUES(?,?,?,?,?,?,?,?,?)",
                        (datetime.now().strftime("%Y-%m-%d %H:%M"), form["full_name"], form["faculty"], form["course"],
                         form["phone"], form["kind"], form["team"] if form["kind"] == "Топтық" else "", form["idea"], form["drive_link"]))
            con.commit()
            con.close()
            return redirect(url_for("thanks"))
    return render_template("apply.html", s=SITE, form=form, errors=errors, phone=PHONE_VIEW)


@app.route("/thanks")
def thanks():
    return render_template("thanks.html", s=SITE, phone=PHONE_VIEW)


@app.route("/admin")
@admin_only
def admin():
    rows = db().execute("SELECT * FROM applications ORDER BY id DESC").fetchall()
    return render_template("admin.html", s=SITE, rows=rows)


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
