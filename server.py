# 같은 디렉토리에 html 폴더 만들어야 html 저장할 때 에러 안 뜸

from flask import Flask, request, g
from datetime import datetime
import sqlite3, hashlib, tldextract
from bs4 import BeautifulSoup
import re

# DB 밑작업 : DB.db가 없으면 만들고, table1이 없으면 만듬.
conn = sqlite3.connect("DB.db")
cu = conn.cursor()
cu.execute('''create table if not exists table1 (
            id integer primary key autoincrement,
            start_url text,
            prev_url text,
            url text,
            html_check integer,
            time text,
            title text,
            key_words text,
            bits text,
            emails text
            );''')
conn.commit()
cu.close()
conn.close()

# 시간 관련 밑작업
time_form = "%Y-%m-%d %H:%M:%S"

def check_time_difference(datetime1, datetime2):
    # 시간 차이 절댓값
    time_diff = abs(datetime2 - datetime1)
    
    # 1시간 이상 차이나는지 체크 (3600초)
    if time_diff.total_seconds() > 3600:
        return True # 1시간 이상 차이 나면 True 반환
    else:
        return False

# Flask 시작
app = Flask(__name__)

#전역변수로 db 객체 생성. 앞으로 db 쓸 때 이거 끌어쓸거임.
#sqlite 인스턴스를 하나만 사용하면 db lock 에러로 인한 비정상 종료가 없다는 것 같음(검색해서 찾은 정보인데 완전 정확한지는 모름)
def get_db():
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = sqlite3.connect('DB.db')
    return g.sqlite_db

#페이지별 동작할거
@app.route("/")
def hello():
    return "hello"

# 이 url로 크롤링 해도 되는가 check 하는 페이지
# 크롤러는 post의 data 로 {'url' : ~} 을 보내면 됨
@app.route("/check", methods=['POST'])
def q():
    start_url = request.form['start_url']
    prev_url = request.form['prev_url']
    url = request.form['url']

    #db에서 검사 
    conn = get_db()
    cur = conn.cursor()
    cur.execute("select * from table1 where start_url = '{}' and prev_url = '{}' and url = '{}';".format(start_url, prev_url, url))
    tmp = cur.fetchall()

    #case 1. 주소 없는 경우
    now_time = datetime.now()
    if len(tmp) == 0:
        cur.execute("insert into table1 (start_url, prev_url, url, html_check, time) values ('{}', '{}', '{}', 0, '{}');".format(start_url, prev_url, url, now_time.strftime(time_form)))
        conn.commit()
        cur.close()

        return "No"

    # case 2. 주소는 있지만, html은 없고, 다른 사람이 요청한지 시간 1시간 이상 지나면 가능.
    #         1시간 차이 안난다 = 아직 다른 사람이 수행 중일 수 있다고 생각
    tmp2 = tmp[0]
    tmp_time = datetime.strptime(tmp2[5], time_form)

    if (tmp2[4] == 0 and check_time_difference(tmp_time, now_time)):
        # 내가 수행하는 중에 또 다른 사람이 하면 안되니까 time 재설정해주기
        cur.execute("update table1 set time = '{}' where id = {};".format(now_time.strftime(time_form), tmp2[0]))
        conn.commit()
        print("[/check] case 2")
        cur.close()
        return "No"
    
    # case 3. 그 외
    cur.close()
    return "Yes"

@app.route("/done", methods=['POST'])
def d():
    #data 받기
    start_url = request.form['start_url']
    prev_url = request.form['prev_url']
    url = request.form['url']
    html = request.form['html']
    title = request.form['title']
    key_words = request.form['key_words']
    bits = request.form['bits']
    emails = request.form['emails']

    # db에서 select
    conn = get_db()
    cur = conn.cursor()
    cur.execute("select * from table1 where start_url = '{}' and prev_url = '{}' and url = '{}';".format(start_url, prev_url, url))
    tmp = cur.fetchall()
    
    tmp2 = tmp[0]

    # 수정해주기
    cur.execute("update table1 set html_check = {}, title = ''' {} ''', key_words = \"{}\", bits = '{}', emails = '{}' where id = {};".format(1, title, key_words, bits, emails, tmp2[0]))
    conn.commit()
    cur.close()

    # html 파일 저장
    # 같은 디렉토리 속 html 폴더에 저장합니다
    hash_text = hashlib.sha256(url.encode()).hexdigest()
    try:
        fd = open('./html/{}.html'.format(hash_text), "wb")
        fd.write(html.encode("utf-8"))
        fd.close()
        print("[html file saved] '{}' as '{}.html'".format(url, hash_text)) # 로그용
    except:
        print("[Error : during save] maybe because of name?]")
    

    return "<h1>done page. html is saved on './html' as sha256 value.</h1>"



#ip, 포트 설정?
host_addr = "0.0.0.0"
port_num = "8080"

#실행
if __name__ == "__main__":              
    app.run(host=host_addr, port=port_num)

