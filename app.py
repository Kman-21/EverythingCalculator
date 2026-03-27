from flask import Flask, request, render_template_string, redirect, session
import sqlite3
import sympy as sp

app = Flask(__name__)
app.secret_key = "supersecretkey"

# =========================
# DATABASE
# =========================
def init_db():
    conn = sqlite3.connect("db.db")
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS users (username TEXT, password TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS history (username TEXT, query TEXT, result TEXT)")
    conn.commit()
    conn.close()

init_db()

# =========================
# ENGINE
# =========================
def compute(query):
    try:
        query = query.lower()

        if "=" in query:
            x = sp.symbols('x')
            left, right = query.split("=")
            return str(sp.solve(sp.sympify(left) - sp.sympify(right), x))

        if "derivative" in query:
            expr = query.replace("derivative of", "")
            return str(sp.diff(sp.sympify(expr), sp.symbols('x')))

        if "integral" in query:
            expr = query.replace("integral of", "")
            return str(sp.integrate(sp.sympify(expr), sp.symbols('x')))

        return str(eval(query))

    except:
        return "Error"

# =========================
# UI
# =========================

landing = """
<style>
body {
    margin:0;
    font-family:Segoe UI;
    background: radial-gradient(circle,#0f172a,#020617);
    color:white;
    text-align:center;
    padding:60px;
}
h1 {
    font-size:clamp(40px,8vw,70px);
    background:linear-gradient(to right,#38bdf8,#22c55e);
    -webkit-background-clip:text;
    -webkit-text-fill-color:transparent;
}
a {
    display:inline-block;
    margin:15px;
    padding:12px 20px;
    border-radius:10px;
    background:#1e293b;
    color:white;
    text-decoration:none;
    transition:0.3s;
}
a:hover {transform:translateY(-3px);background:#334155;}
</style>

<h1>NovaCalc AI</h1>
<p>The next-gen intelligent calculator</p>

<a href="/login">Login</a>
<a href="/signup">Sign Up</a>
"""

auth = """
<style>
body {
    background:#020617;
    color:white;
    text-align:center;
    padding:50px;
    font-family:Segoe UI;
}
input {
    padding:15px;
    margin:10px;
    width:90%;
    max-width:300px;
    border-radius:8px;
    border:none;
}
button {
    padding:15px 25px;
    background:linear-gradient(135deg,#22c55e,#38bdf8);
    border:none;
    color:white;
    border-radius:8px;
    cursor:pointer;
}
button:hover {opacity:0.9;}
</style>

<h1>{{title}}</h1>

<form method="POST">
<input name="username" placeholder="Username"><br>
<input name="password" type="password" placeholder="Password"><br>
<button>{{title}}</button>
</form>

<p>{{msg}}</p>
<a href="/">Back</a>
"""

dashboard = """
<style>
body {
    margin:0;
    display:flex;
    font-family:Segoe UI;
    background:#020617;
    color:white;
}

/* SIDEBAR */
.sidebar {
    width:220px;
    background:#0f172a;
    padding:20px;
}
.sidebar a {
    display:block;
    margin-top:15px;
    color:#38bdf8;
}

/* MAIN */
.main {
    flex:1;
    padding:20px;
}

input {
    padding:15px;
    width:100%;
    max-width:500px;
    border-radius:8px;
    border:none;
}

button {
    padding:15px;
    margin-top:10px;
    background:linear-gradient(135deg,#22c55e,#38bdf8);
    border:none;
    color:white;
    border-radius:8px;
}

/* CARD */
.card {
    background:#1e293b;
    padding:15px;
    margin-top:15px;
    border-radius:10px;
    transition:0.3s;
}
.card:hover {transform:translateY(-3px);}

/* MOBILE */
@media(max-width:700px){
    body {flex-direction:column;}
    .sidebar {width:100%;display:flex;justify-content:space-around;}
}
</style>

<div class="sidebar">
<h2>NovaCalc</h2>
<a href="/dashboard">Dashboard</a>
<a href="/logout">Logout</a>
</div>

<div class="main">
<h1>Dashboard</h1>

<form method="POST">
<input name="query" placeholder="Try: derivative of x^2">
<button>Run</button>
</form>

{% if result %}
<div class="card"><b>Result:</b> {{result}}</div>
{% endif %}

<h2>History</h2>
{% for q,r in history %}
<div class="card">{{q}} → {{r}}</div>
{% endfor %}

<h2>Usage</h2>
<canvas id="chart"></canvas>
</div>

<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script>
new Chart(document.getElementById('chart'), {
type:'bar',
data:{
labels: {{labels}},
datasets:[{data: {{values}}}]
}
});
</script>
"""

# =========================
# ROUTES
# =========================
@app.route("/")
def home():
    return landing

@app.route("/signup", methods=["GET","POST"])
def signup():
    msg=""
    if request.method=="POST":
        u=request.form["username"]
        p=request.form["password"]

        conn=sqlite3.connect("db.db")
        c=conn.cursor()
        c.execute("INSERT INTO users VALUES (?,?)",(u,p))
        conn.commit()
        conn.close()
        return redirect("/login")

    return render_template_string(auth,title="Sign Up",msg=msg)

@app.route("/login", methods=["GET","POST"])
def login():
    msg=""
    if request.method=="POST":
        u=request.form["username"]
        p=request.form["password"]

        conn=sqlite3.connect("db.db")
        c=conn.cursor()
        c.execute("SELECT * FROM users WHERE username=? AND password=?",(u,p))
        user=c.fetchone()
        conn.close()

        if user:
            session["user"]=u
            return redirect("/dashboard")
        else:
            msg="Invalid login"

    return render_template_string(auth,title="Login",msg=msg)

@app.route("/dashboard", methods=["GET","POST"])
def dash():
    if "user" not in session:
        return redirect("/login")

    result=None

    if request.method=="POST":
        query=request.form["query"]
        result=compute(query)

        conn=sqlite3.connect("db.db")
        c=conn.cursor()
        c.execute("INSERT INTO history VALUES (?,?,?)",(session["user"],query,result))
        conn.commit()
        conn.close()

    conn=sqlite3.connect("db.db")
    c=conn.cursor()
    c.execute("SELECT query,result FROM history WHERE username=?",(session["user"],))
    data=c.fetchall()
    conn.close()

    labels=[i[0] for i in data]
    values=list(range(1,len(data)+1))

    return render_template_string(dashboard,result=result,history=data,labels=labels,values=values)

@app.route("/logout")
def logout():
    session.pop("user",None)
    return redirect("/")

if __name__=="__main__":
    app.run(debug=True)
