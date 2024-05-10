import os, random, requests, psutil, subprocess, time, tldextract, re, nltk, operator
from urllib.parse import urljoin
from bs4 import BeautifulSoup

# 서버 ip port
server_addr = "127.0.0.1:8080"

#빈도수 계산하는 함수. n=한 단어
# ex)hello world -> {"hello":1, "world":1} 딕셔너리로 반환
def ngrams(input_, n):
    output = {}
    for i in range(len(input_) - n + 1):
        ngramTemp = " ".join(input_[i:i+n])
        if ngramTemp not in output:
            output[ngramTemp] = 0
        output[ngramTemp] += 1
    return output

# tor 프로세스 다시 시작
# =>실행중인 모든 프로세스 반복 => "tor.exe" 프로세스 종료
# => tor실행파일을 실행해서 tor 다시 시작
# => tor를 다시 시작한 후 10초 동안 기다린다. 
def restart_tor():
    try:
        for process in psutil.process_iter():
            if process.name().lower() == "tor.exe":
                process.kill()
                print("Tor process killed.")
                time.sleep(5)

        print("Restarting Tor...")
        #로컬환경에서 tor.exe가 있는 파일경로 
        tor_path = "C:\\Users\\kyj97\\OneDrive\\바탕 화면\\Tor Browser\\Browser\\TorBrowser\\Tor\\tor.exe"
        subprocess.Popen([tor_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        print("Tor process restarted.")
        time.sleep(10)

    except Exception as e:
        print(f"Error restarting Tor: {e}")



# .onion URL을 방문하여 해당 콘텐츠를 스크랩하고 파일에 저장
def visit_onion(start_url, prev_url, onion_url, depth=1, max_depth=2):
    try:
        ttmp_data = {
            "start_url" : start_url,
            "prev_url" : prev_url,
            "url" : onion_url
        }
        ttmp_res = requests.post("http://" + server_addr + "/check", data=ttmp_data)
        if ttmp_res.text == 'No':
            if onion_url.startswith('http://') or onion_url.startswith('https://'):
                session = requests.session()
                session.proxies = {
                    'http': 'socks5h://localhost:9050',
                    'https': 'socks5h://localhost:9050'
                }
                response = session.get(onion_url)
                if response.status_code == 200: 
                    #파싱 : html의 제목 추출
                    soup = BeautifulSoup(response.content, 'html.parser') 
                    title = soup.title.text if soup.title else ""
                    tmp_tap = '    ' * (depth-1)
                    print(tmp_tap, "Title:", title)

                    body = soup.find('body').text if soup.find('body') else ""
                    words = body.split()

                    #비트코인 주소들 찾기
                    bit_pattern = re.compile('[13][a-km-zA-HJ-NP-Z0-9]{26,33}')
                    bits = []
                    for word in words:  
                        if len(word) >26 and len(word) < 35:
                            bits += bit_pattern.findall(word)
                    print(bits)
                    tmp_bits = ''
                    for i in bits:
                        tmp_bits += i + ' '
                    bits = tmp_bits

                    #이메일. pdf 121 페이지에 다른 것들도 있음
                    email_pattern = re.compile('^[a-zA-Z0-9+-\_.]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')
                    emails = []
                    for word in words:  
                        emails += email_pattern.findall(word)
                    print(emails)
                    tmp_emails = ''
                    for i in emails:
                        tmp_emails += i + ' '
                    emails = tmp_emails

                    #key_words 파싱
                    tmp = body.lower()
                    tmp_pattern = re.compile("[a-z0-9']*")
                    tmps = tmp_pattern.findall(tmp)
                    tmp_list = []
                    for elm in tmps:
                        if elm != '':
                            tmp_list.append(elm)
                    ttmp = nltk.pos_tag(tmp_list)
                    ttmp_list = []
                    for i in ttmp:
                        if i[1][0] == 'N':
                            ttmp_list += [i[0]]
                    ttmp_dic = ngrams(ttmp_list,1)
                    sorted_ttmp = sorted(ttmp_dic.items(), key = operator.itemgetter(1), reverse = True)
                    key_words = ''
                    for i in sorted_ttmp[:20]:
                        key_words += i[0] + ' ' + str(i[1]) + ' '
                    print(key_words)

                    #서버한테 보내기
                    ttmp_html = response.content
                    ttmp_data = {
                        "start_url" : start_url,
                        "prev_url" : prev_url,
                        "url": onion_url,
                        'html' : ttmp_html,
                        'title' : title,
                        'key_words' : key_words,
                        'bits' : bits,
                        'emails' : emails
                    }
                    ttmp_res = requests.post("http://" + server_addr + "/done", data = ttmp_data)

                    # 혹시나 db lock 방지용
                    time.sleep(1)
                    
                    #재귀 깊이<최대깊이 : 링크추출 - >재귀방문
                    if depth < max_depth:
                        links = soup.find_all('a', href=lambda href: href and '.onion' in href)
                        for link in links:
                            absolute_link = urljoin(onion_url, link['href']) #상대주소로 변환
                            visit_onion(start_url, onion_url, absolute_link, depth=depth+1, max_depth=max_depth)
                else:
                    print(f"Failed to download: {onion_url}, status code: {response.status_code}")
            else:
                print(f"Invalid URL: {onion_url}")

    except requests.exceptions.RequestException as e:
        print(f"Error visiting {onion_url}: {e}")
        return

#onion url목록방문
def visit_random_onion_urls(onion_urls):
    random.shuffle(onion_urls)  #url목록을 무작위로 섞고 반복
    for onion_url in onion_urls: 
        full_url = f"http://{onion_url}" 
        visit_onion(full_url, "", full_url) #각 url에 대한 함수 호출

#onion url 목록 읽기
def read_onion_urls(filename):
    with open(filename, "r") as file:
        onion_urls = [line.strip() for line in file.readlines() if line.strip()]
    return onion_urls


#시작        
if __name__ == "__main__":
    onion_list_file = "onions.txt"
    onion_urls = read_onion_urls(onion_list_file) #onion_list_file에서 onion url목록을 읽어옴

    restart_tor()
    visit_random_onion_urls(onion_urls) 
 # onion URL 목록에서 URL을 임의로 선택하고, 각 URL에 대해 visit_onion() 함수를 호출하여
 # 해당 .onion 웹사이트를 방문하고 스크랩
