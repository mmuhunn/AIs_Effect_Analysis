# AI 관심도의 구조적 이동 분석 대시보드

Wikipedia Pageviews 데이터를 기반으로, ChatGPT 등장 초기(2023)와 정착기(2025)의 사회적 관심사가 어떻게 **기술(Tech)**에서 **사회적 영향(Social Impact)**으로 이동했는지 분석하는 인터랙티브 웹 대시보드입니다.

## 📊 주요 기능

- **Trend Overview**: 연도별 Top 키워드 비교 및 급상승/급하락 키워드 분석
- **Category Shift**: 카테고리별 조회수 총량 및 점유율 변화 분석
- **Deep Insights**: 변화 패턴 산점도, 카테고리별 평균 변화율, 신규/사라진 키워드 추적
- **Keyword Search**: 특정 키워드 검색 및 조회수 변화 분석
- **Raw Data**: 원본 데이터 탐색 및 필터링

## 🛠️ 기술 스택

- **Streamlit**: 웹 대시보드 프레임워크
- **Pandas**: 데이터 처리 및 분석
- **Plotly**: 인터랙티브 시각화
- **Python 3.x**

## 📁 프로젝트 구조

```
BigData_project/
├── data/
│   ├── monthly_views_202302.csv  # 2023년 2월 데이터
│   ├── monthly_views_202509.csv  # 2025년 9월 데이터
│   └── nodes.csv                 # 노드 데이터
├── app.py                        # Streamlit 메인 애플리케이션
├── requirements.txt              # 필요한 패키지 목록
└── README.md                     # 프로젝트 설명서
```

## 🚀 실행 방법

### 1. 저장소 클론

```bash
git clone https://github.com/mmuhunn/AIs_Effect_Analysis.git
cd AIs_Effect_Analysis
```

### 2. 가상환경 생성 (선택사항)

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Mac/Linux
source venv/bin/activate
```

### 3. 패키지 설치

```bash
pip install -r requirements.txt
```

### 4. 애플리케이션 실행

```bash
streamlit run app.py
```

브라우저가 자동으로 열리며 대시보드가 표시됩니다. (기본 주소: http://localhost:8501)

## 📈 사용 방법

### 필터 옵션

- **ChatGPT 제외**: 사이드바에서 ChatGPT 관련 키워드를 분석에서 제외할 수 있습니다.
- **카테고리 필터**: Trend Overview 탭에서 특정 카테고리만 선택하여 분석할 수 있습니다.

### 주요 분석 기능

1. **Trend Overview**: 카테고리별 체크박스를 통해 원하는 카테고리만 필터링하여 Top 키워드 순위를 확인할 수 있습니다.
2. **Category Shift**: Technology, Application, Social_Impact 카테고리별 점유율 변화를 시각적으로 확인할 수 있습니다.
3. **Keyword Search**: 키워드를 검색하여 해당 키워드의 2023년과 2025년 조회수 변화를 분석할 수 있습니다.

## 📊 데이터 카테고리

- **Technology**: AI 기술 관련 키워드 (ChatGPT, OpenAI, Machine Learning 등)
- **Application**: AI 응용 사례 (Automation, AI_art, Chatbot 등)
- **Social_Impact**: AI의 사회적 영향 (Job_loss, Layoff, AI_ethics 등)

## 🔍 노이즈 필터링

다음 키워드들은 자동으로 필터링됩니다:
- 스포츠 관련: NFL, Playoff, Championship, Football, Basketball 등
- Wikipedia 내부 페이지: File:, Wikipedia:, User:, Talk: 등
- 기타 노이즈: DiBiase, Tobias, Len_Bias 등

## 📝 라이선스

이 프로젝트는 교육 및 연구 목적으로 제작되었습니다.

## 👤 작성자

mmuhunn

## 🔗 관련 링크

- [GitHub 저장소](https://github.com/mmuhunn/AIs_Effect_Analysis)
