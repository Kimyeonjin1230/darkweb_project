import sqlite3,seaborn
import matplotlib.pyplot as plt
from collections import Counter

# 데이터베이스 연결 및 데이터 가져오기
with sqlite3.connect("DB.db") as conn:
    cu = conn.cursor()
    cu.execute("SELECT key_words FROM table1")
    words_list = [tup[0].strip() for tup in cu.fetchall() if tup[0] is not None and tup[0].strip() != '']

# 단어 빈도수 계산
word_counts = Counter()
for entry in words_list:
    word_freq_pairs = entry.split()
    for i in range(0, len(word_freq_pairs), 2):
        word = word_freq_pairs[i]
        frequency = int(word_freq_pairs[i+1])
        word_counts[word] += frequency

# 가장 많이 등장한 단어 순으로 정렬 (빈도수가 높은 순)
sorted_word_counts = word_counts.most_common(20) # 최대 x 축 자료 개수

# 그래프 데이터 분리
x_data, y_data = zip(*sorted_word_counts)

# 막대 그래프 그리기
plt.bar(x_data, y_data, color=seaborn.color_palette('cool', len(x_data))[::-1])
[plt.text(i, value+1000, str(value), ha='center') for i, value in enumerate(y_data)]
plt.xlabel('word')
plt.ylabel('frequency')
plt.title('word frequency graph')
plt.xticks(rotation=45)  # x 축 레이블 회전
plt.savefig('word_frequency_graph.png', dpi=200)
plt.show()
