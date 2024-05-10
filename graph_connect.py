import sqlite3
import graphviz

# db 연결
conn = sqlite3.connect("DB.db")
cur = conn.cursor()

# url = start_url 인 것들만 일단 뽑기
# 얘네 하나하나를 중심으로 연결도를 만듭니다
# 애초에 크롤링을 그런 방식으로 진행했으니까요
cur.execute("select start_url from table1 where prev_url = '';")
start_list = cur.fetchall()

# 각각의 start_url 마다 for문 수행
for s_url in start_list:
    start_url = s_url[0]

    # start_url에서 파생된 것들 select
    cur.execute("select prev_url, url, title, html_check from table1 where start_url = '{}'".format(start_url))

    tmp = cur.fetchall()

    # start_url 중 크롤링 실패한 것들 제외
    if tmp[0][3] == 0:
        continue

    # start_url 에서 링크가 없었던 것들도 제외
    if len(tmp) == 1 :
        continue

    # start_url 에서 앞의 'http://' 없애주기
    start_url = start_url[7:]

    #관계도 만들기
    dot = graphviz.Digraph(comment="{} site_connect".format(start_url))
    d_list = []

    # 카운터
    # 노드 99개만 하게. 연결관계가 1500개 짜리인 start_url이 있는데, 연결도 만들다 에러남
    cnt_1 = 0

    # 노드 만들기 : title 이 표시되게 설정해주기
    for i in tmp:

        #카운터 처리
        cnt_1 += 1
        if cnt_1 == 100:
            break

        # title이 없는건 스킵
        if i[2] == None:
            continue
        
        # 앞에 'http~' 부분 없애주기
        if i[1].startswith('http://'):
            tmp_1 = i[1][7:]
        if i[1].startswith('https://'):
            tmp_1 = i[1][8:]

        dot.node(tmp_1, i[2])
        d_list.append(tmp_1)

    # 카운터 초기화
    cnt_1 = 0

    # 엣지 만들기
    for i in tmp:

        # 카운터 처리
        cnt_1 += 1
        if cnt_1 == 100:
            break

        # title 이 없는건 스킵
        if i[2] == None:
            continue

        # start_url 도 스킵
        if i[0] == "":
            continue

        if i[1].startswith('http://'):
            tmp_1 = i[1][7:]
        if i[1].startswith('https://'):
            tmp_1 = i[1][8:]

        if i[0].startswith('http://'):
            tmp_0 = i[0][7:]
        if i[0].startswith('https://'):
            tmp_0 = i[0][8:]

        # prev_url 의 title 이 없는 경우, 앞에서 스킵되었어서 제대로 연결도가 안 만들어짐
        # 그 경우, prev_url 을 start_url 과 연결하는 엣지 만들어주는 코드.
        # '최대 깊이 = 3' 일 때만 이 코드를 사용 가능
        # '최대 깊이 > 3' 일 땐 코드 다시 짜야함
        if tmp_0 not in d_list:
            dot.edge(start_url, tmp_0)

        #엣지 생성
        dot.edge(tmp_0, tmp_1)


    print(dot.source)

    # './doctest_ouput' 폴더에 'url.gv.pdf' 파일 생성
    dot.render('doctest-output/{}.gv'.format(start_url), view=False)  # doctest: +SKIP
    'doctest-output/{}.gv.pdf'.format(start_url)




