from mysql.connector import connect

def execute(query, args, hm=None, lastId=False):
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
    if not lastId:
        return res
    else:
        return res, cursor.lastrowid
