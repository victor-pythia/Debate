from flask import *
from db.initial import *
from Models.Topic import *
from Models.Claim import *
from Models.User import *
from db.connectionHelper import execute
from db.initial import initial
import hashlib
import json

initial()

app = Flask(__name__)
app.secret_key = b'dasdashdkhasldkasdasdasdkas;dk;as'

@app.before_request
def setup():
    session.permanent = True

@app.route('/')
def index():
    topics = execute("select distinct t.id, t.text, u.username from user_topics ut, topics t, users u where ut.topic_id = t.id and ut.user_id = u.id", (), "many")
    if 'user' in session:
        return render_template('index.html', user=session['user'], topics=topics)
    else:
        return render_template('index.html', topics=topics)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form["username"]
        exists = execute("select * from users where username = %s", (username,), "one")
        if exists:
            return({"msg": "Username is taken"})

        password = request.form["password"]
        password = hashlib.sha256(password.encode("utf-8")).hexdigest()
        execute("insert into users (username, password) values (%s, %s)", (username, password))
        usr = execute("select * from users where username = %s and password = %s", (username, password), "one")
        session['user'] = usr
        return jsonify({"user": usr})


@app.route('/login', methods=['POST'])
def login():    
    username = request.form["username"]
    password = request.form["password"]

    password = hashlib.sha256(password.encode("utf-8")).hexdigest()

    res = execute(
        "SELECT * FROM users WHERE username = %s and password = %s",
        (username, password), "one"
    )
    if not res:
        print("User not found")
        return jsonify({"message": "Username or password are wrong!"})
    else:
        print("User logged in")
        session['user'] = res
        return jsonify({"message": "ok"})


@app.route('/topic', methods=['GET', 'POST'])
def topic():
    if request.method == 'POST':
        if 'user' in session:
            text = request.form["text"]
            _, sqlid = execute("insert into topics (text) values (%s)", (text, ), lastId=True)
            execute("insert into user_topics (user_id, topic_id) values (%s, %s)", (session['user']['id'], sqlid))
            user = execute("select * from users where id = %s", (session["user"]["id"],), "one")
            return jsonify({"text": text, "sqlid": sqlid, "user": user["username"], "message": "ok"})
        else:
            return jsonify({"message": "err"})

@app.route('/claim', methods=['GET', 'POST'])
def post():
    if request.method == 'POST':
        if 'user' in session:
            req_json = request.get_json()
            text = req_json["form"][0]["value"]
            topicId = req_json["topicId"]
            print(req_json["relationList"])
            relation_list = list(map(lambda x: int(x) if x.isdigit() else x, req_json["relationList"]))
            res, lastId = execute("insert into claims (text) values (%s)", (text, ), None, True)
            execute("insert into topic_claims (topic_id, claim_id) values (%s, %s)", (topicId, lastId), None)
            execute("insert into user_claims (user_id, claim_id) values (%s, %s)", (session['user']['id'], lastId), None)

            for i in range(0, len(relation_list)-1, 2):
                execute("insert into claim_relation (parent_id, linked_to, type) values (%s, %s, %s)", (lastId, relation_list[i], relation_list[i+1]), None)
                execute("insert into claim_relation (parent_id, linked_to, type) values (%s, %s, %s)", (relation_list[i], lastId, relation_list[i+1]), None)

            claim = execute("select distinct c.id, c.text,  u.username from claims c join topic_claims tc on tc.topic_id = %s "
                           "join user_claims uc on uc.user_id = %s join users u on uc.user_id=u.id where c.id = %s",
                           (topicId, session['user']['id'], lastId), "one")
            return jsonify(claim)
        else:
            return jsonify({"message": "err"})
    if request.method == "GET":
        claims = execute("select distinct * from claims order by post_date", (), "many")
        print(claims)
        return jsonify(claims)

@app.route('/claim/<cid>', methods=['GET'])
def claim(cid):
    if request.method == 'GET':
        claim = execute(
            "select distinct c.id, c.text, u.username, tc.topic_id, c.post_date from claims c join topic_claims tc on tc.claim_id = c.id "
            "join user_claims uc on c.id = uc.claim_id join users u on u.id = uc.user_id "
            "where c.id = %s"
            , (cid,), "one"
        )
        if 'user' in session:
            return render_template('claim.html', user=session['user'], claim=claim)
        else:
            return render_template('claim.html', claim=claim)

@app.route('/relationship/<cid>', methods=['GET'])
def rel(cid):
    if request.method == 'GET':
        related_claims = execute(
            "select cr.linked_to, cr.type from claim_relation cr join claims c on c.id = cr.parent_id where cr.parent_id=%s",
            (cid, ), "many"
        )
        for rel in related_claims:
            rel["url"] = url_for('claim', cid=rel["linked_to"])
        print(related_claims)
        return jsonify(related_claims)

@app.route('/claim/topicId/<tId>', methods=['GET'])
def claim_by_topic_id(tId):
    claims = execute(
        "select distinct c.id, c.text, u.username, c.post_date from claims c join topic_claims tc on tc.claim_id = c.id "
        "join user_claims uc on c.id = uc.claim_id join users u on u.id = uc.user_id"
        " where tc.topic_id = %s order by c.post_date desc",
        (tId,), "many"
    )
    return jsonify(claims)

@app.route('/topic/<tId>', methods=['GET', 'POST', "DELETE"])
def topic_id(tId):
    if request.method == 'GET':
        fetched = execute(
            "SELECT * FROM topics WHERE id = %s order by post_date desc",
            (tId,), "one"
        )
        if fetched:
            topic = fetched
        else:
            topic = None

        claims = execute(
            "select distinct c.id, c.text, u.username, c.post_date from claims c join topic_claims tc on tc.claim_id = c.id "
            "join user_claims uc on c.id = uc.claim_id join users u on u.id = uc.user_id "
            " where tc.topic_id = %s order by c.post_date desc",
            (topic["id"],), "many"
        )
        if 'user' in session:
            return render_template('topic.html', topic=topic, user=session['user'], claims=claims)
        else:
            return render_template('topic.html', topic=topic, claims=claims)
    elif request.method == 'DELETE':
        execute("delete from user_topics where topic_id=%s", (tId,))
        execute("delete from topics where id=%s", (tId, ))
        return jsonify({"message": "ok"})
    else:
        return "ERROR"

@app.route('/reply', methods=['GET', 'POST'])
def reply():
    if request.method == 'POST':
        text = request.form["text"]
        claim_id = request.form["claimId"]
        parent_id = request.form["parentId"]
        _type = request.form["type"]
        _, reply_id = execute("insert into replies (text, parent_id, type) values (%s, %s, %s)", (text, parent_id, _type), lastId=True)
        execute("insert into claim_replies (claim_id, reply_id) values (%s, %s)", (claim_id, reply_id))
        execute("insert into user_replies (user_id, reply_id) values (%s, %s)", (session['user']['id'], reply_id))
        reply = execute(
            "Select r.id, r.parent_id, r.text, u.username, cr.claim_id, r.post_date, rt.type from replies r join claim_replies cr on r.id = cr.reply_id "
            "join user_replies ur on ur.reply_id = r.id join users u on ur.user_id = u.id join reply_type rt on rt.id = r.type where r.id=%s",
             (reply_id,), "one")
        return jsonify(reply)

@app.route('/replies', methods=['GET'])
def replies():
    topicId = request.args.get('topicId')
    claimId = request.args.get('claimId')
    if claimId:
        replies = execute("Select r.id, r.parent_id, r.text, u.username, cr.claim_id, r.post_date, rt.type from replies r join claim_replies cr on r.id = cr.reply_id "
                   "join user_replies ur on ur.reply_id = r.id join users u on ur.user_id = u.id join reply_type rt on rt.id = r.type "
                   " join topic_claims tc on tc.claim_id = cr.claim_id where tc.topic_id = %s and tc.claim_id = %s order by r.post_date desc",
                   (topicId, claimId), "many")
    else:
        replies = execute("Select r.id, r.parent_id, r.text, u.username, cr.claim_id, r.post_date, rt.type from replies r join claim_replies cr on r.id = cr.reply_id "
                    "join user_replies ur on ur.reply_id = r.id join users u on ur.user_id = u.id join reply_type rt on rt.id = r.type "
                    " join topic_claims tc on tc.claim_id = cr.claim_id where tc.topic_id = %s order by r.post_date desc",
                    (topicId,), "many")
    return jsonify(replies)

@app.route('/logout')
def logout():
    try:
        session.pop("user")
    except KeyError:
        pass
    return jsonify({"message": "ok"})

if __name__=='__main__':
    app.run('localhost', 3001, debug=True)

.0