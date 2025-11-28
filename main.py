from flask import Flask, render_template, request, redirect, url_for, session
from instagrapi import Client
import threading
import time
import random
import uuid
import json

app = Flask(__name__)
app.secret_key = "sujal_hawk_king_007_2025_render"
MASTER_PASSWORD = "sujal@007"        # ← change kar lena

users_data = {}

FAKE_DEVICES = [
    {"app_version": "263.0.0.23.118", "android_version": 13, "manufacturer": "Google", "model": "Pixel 7"},
    {"app_version": "263.0.0.23.118", "android_version": 13, "manufacturer": "Samsung", "model": "SM-G998B"},
    {"app_version": "263.0.0.23.118", "android_version": 14, "manufacturer": "Xiaomi", "model": "2210132G"},
]

def add_log(user_id, msg, color="white"):
    if user_id not in users_data: users_data[user_id] = {"logs": []}
    timestamp = time.strftime('%H:%M:%S')
    users_data[user_id]["logs"].append({"time": timestamp, "msg": msg, "color": color})
    if len(users_data[user_id]["logs"]) > 500:
        users_data[user_id]["logs"] = users_data[user_id]["logs"][-500:]

def spam_worker(user_id, client, thread_id, messages, delay, cycle_count, cycle_break):
    sent = 0
    while users_data[user_id].get("running", False):
        try:
            msg = random.choice(messages)
            client.direct_send(msg, thread_ids=[thread_id])
            sent += 1
            users_data[user_id]["total_sent"] = users_data[user_id].get("total_sent", 0) + 1
            add_log(user_id, f"Sent #{users_data[user_id]['total_sent']} → {msg[:60]}", "lime")
            if sent % cycle_count == 0:
                add_log(user_id, f"Break {cycle_break}s after {cycle_count} msgs", "yellow")
                time.sleep(cycle_break)
            time.sleep(delay * random.uniform(1.3, 2.2))
        except Exception as e:
            add_log(user_id, f"Error: {str(e)[:100]}", "red")
            time.sleep(30)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['password'] == MASTER_PASSWORD:
            session['auth'] = True
            return redirect('/')
        else:
            return "<h1>Galat Password</h1>", 403
    return '''<center style="margin-top:20%;background:#000;color:#0f0;height:100vh;font-family:Arial">
    <h1>HAWK SUJAL SPAMMER v9</h1>
    <form method=post><input type=password name=password placeholder="Master Password" required style="padding:15px;width:300px;border-radius:10px">
    <br><br><button type=submit style="padding:15px 40px;background:#ff006e;color:white;border:none;border-radius:10px">ENTER</button></form></center>'''

@app.route('/', methods=['GET', 'POST'])
def index():
    if not session.get('auth'): return redirect('/login')

    user_id = session.get('user_id')
    if not user_id or user_id not in users_data:
        user_id = str(uuid.uuid4())
        session['user_id'] = user_id
        users_data[user_id] = {
            "running": False, "total_sent": 0, "status": "Ready", "threads": 0, "logs": [], "clients": [], "worker_threads": [],
            "input_mode": "username", "username": "", "password": "", "session_json": "", "thread_id": "", "messages": "",
            "delay": 10, "cycle_count": 40, "cycle_break": 30, "threads_num": 3
        }
    data = users_data[user_id]

    if request.method == 'POST':
        data["input_mode"] = request.form.get('input_mode', 'username')
        data["username"] = request.form.get('username', '')
        data["password"] = request.form.get('password', '')
        data["session_json"] = request.form.get('session_json', '').strip()
        data["thread_id"] = request.form['thread_id']
        data["messages"] = request.form['messages']
        data["delay"] = float(request.form.get('delay', 10))
        data["cycle_count"] = int(request.form.get('cycle_count', 40))
        data["cycle_break"] = int(request.form.get('cycle_break', 30))
        data["threads_num"] = int(request.form['threads'])

        data["running"] = False
        time.sleep(2)
        data["logs"] = []
        add_log(user_id, "New bombing session started...", "cyan")

        data["running"] = True
        data["total_sent"] = 0
        data["status"] = "BOMBING ACTIVE"
        data["clients"] = []
        data["worker_threads"] = []

        for i in range(data["threads_num"]):
            cl = Client()
            cl.delay_range = [8, 22]
            cl.set_device(random.choice(FAKE_DEVICES))

            try:
                if data["input_mode"] == "session" and data["session_json"]:
                    settings = json.loads(data["session_json"])
                    cl.login_by_sessionid(settings["authorization_data"]["sessionid"])
                    add_log(user_id, f"Thread {i+1} → Session ID Login OK", "lime")
                else:
                    cl.login(data["username"], data["password"])
                    add_log(user_id, f"Thread {i+1} → Username Login OK", "lime")

                data["clients"].append(cl)
                t = threading.Thread(target=spam_worker, args=(user_id, cl,
                    int(data["thread_id"]), [m.strip() for m in data["messages"].split('\n') if m.strip()],
                    data["delay"], data["cycle_count"], data["cycle_break"]), daemon=True)
                t.start()
                data["worker_threads"].append(t)

            except Exception as e:
                add_log(user_id, f"Thread {i+1} → Failed: {str(e)[:100]}", "red")

        data["threads"] = len(data["clients"])
        if data["clients"]:
            add_log(user_id, "BOMBING STARTED!", "lime")
        else:
            data["running"] = False
            data["status"] = "Login Failed"

    return render_template('index.html',
        status=data.get("status","Ready"), total_sent=data.get("total_sent",0),
        threads=data.get("threads",0), logs=data.get("logs",[]),
        input_mode=data.get("input_mode","username"),
        username=data.get("username",""), session_json=data.get("session_json",""),
        thread_id=data.get("thread_id",""), messages=data.get("messages",""),
        delay=data.get("delay",10), cycle_count=data.get("cycle_count",40),
        cycle_break=data.get("cycle_break",30), threads_num=data.get("threads_num",3)
    )

@app.route('/stop') 
def stop(): 
    if session.get('auth') and session.get('user_id') in users_data:
        users_data[session['user_id']]["running"] = False
        add_log(session['user_id'], "STOPPED!", "red")
        users_data[session['user_id']]["status"] = "STOPPED"
    return redirect('/')

@app.route('/clear') 
def clear(): 
    if session.get('auth') and session.get('user_id') in users_data:
        users_data[session.get('user_id')]["logs"] = []
    return redirect('/')

@app.route('/logout') 
def logout(): 
    session.clear()
    return redirect('/login')

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)
