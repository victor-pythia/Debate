from mysql.connector import connect

def execute(query, args, hm="one"):
    db = connect(user='kazi', password='Kazimir_pass123',
                              host='localhost',
                              database='dragos')
    cursor = db.cursor(buffered=True, dictionary=True)
    cursor.execute(query, args)
    try:
        db.commit()
    except:
        print("------------------------------")
    res = None
    if hm:
        if hm == "one":
            res = cursor.fetchone()
        elif hm == "many":
            res = cursor.fetchall()
    cursor.close()
    db.close()
    return res

database = dict()

# database['drop'] = """
# drop database dragos;
# """

database['users'] = """
create table if not exists users (
    id INT(6) UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(25) NOT NULL,
    password VARCHAR(256) NOT NULL
)
"""

database['reply_type'] = """
create table if not exists reply_type (
    id int(6) unsigned auto_increment primary key,
    type varchar(20) not null unique default "test"
)
"""

database['topics'] = """
create table if not exists topics(
    id INT(6) UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    post_date timestamp not null default current_timestamp,
    text VARCHAR(1000) NOT NULL
)
"""

database['claims'] = """
create table if not exists claims (
    id INT(6) UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    text VARCHAR(1000) NOT NULL,
    post_date timestamp not null default current_timestamp
)
"""

database['user_claims'] = """
create table if not exists user_claims (
    user_id int(6) UNSIGNED not null,
    claim_id int(6) UNSIGNED not null,
    primary key (claim_id, user_id),
    foreign key (claim_id) references claims(id) on delete cascade,
    foreign key (user_id) references users(id) on delete cascade
)
"""

database['user_topics'] = """
create table if not exists user_topics (
    user_id int(6) UNSIGNED not null,
    topic_id int(6) UNSIGNED not null,
    primary key (topic_id, user_id),
    foreign key (topic_id) references topics(id) on delete cascade,
    foreign key (user_id) references users(id) on delete cascade
)
"""

database['topic_claims'] = """
create table if not exists topic_claims (
    topic_id int(6) UNSIGNED not null,
    claim_id int(6) UNSIGNED not null,
    primary key (topic_id, claim_id),
    foreign key (topic_id) references topics(id) on delete cascade,
    foreign key (claim_id) references claims(id) on delete cascade
)
"""

database['replies'] = """
create table if not exists replies (
    id int(6) UNSIGNED AUTO_INCREMENT not null primary key,
    text varchar(1000) not null,
    parent_id int(6) UNSIGNED not null,
    post_date timestamp not null default current_timestamp,
    type INT(6) unsigned NOT NULL,
    foreign key (type) references reply_type (id) on delete cascade
)
"""

database['user_replies'] = """
create table if not exists user_replies(
    reply_id int(6) UNSIGNED not null,
    user_id int(6) UNSIGNED not null,
    primary key (user_id, reply_id),
    foreign key (user_id) references users(id) on delete cascade,
    foreign key (reply_id) references replies(id) on delete cascade
)
"""

database['claim_replies'] = """
create table if not exists claim_replies (
    reply_id int(6) UNSIGNED not null,
    claim_id int(6) unsigned not null,
    primary key (reply_id, claim_id),
    foreign key (reply_id) references replies(id) on delete cascade,
    foreign key (claim_id) references claims(id) on delete cascade
)
"""

database['claim_relation'] = """
create table if not exists claim_relation (
    parent_id int(6) UNSIGNED not null,
    linked_to int(6) unsigned not null,
    type varchar(15) not null,
    primary key (parent_id, linked_to)
)
"""

def initial():
    for table, query in database.items():
        execute(query, (), None)
        print(f"Created table {table}")

    res = execute("select * from reply_type", (), "many")
    if len(res) != 6:
        execute("insert into reply_type (type) values (%s)", ("clarification",), None)
        execute("insert into reply_type (type) values (%s)", ("counterargument",), None)
        execute("insert into reply_type (type) values (%s)", ("supporting argument",), None)
        execute("insert into reply_type (type) values (%s)", ("evidence",), None)
        execute("insert into reply_type (type) values (%s)", ("support",), None)
        execute("insert into reply_type (type) values (%s)", ("rebuttal",), None)
        
        print("Generated claim types")
    print("DONE")