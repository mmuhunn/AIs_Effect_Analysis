# -*- coding: utf-8 -*-
"""
Wikipedia 트렌드 분석 - Spark 버전
2023년과 2025년 데이터를 비교하여 AI 관련 키워드의 변화 추적
"""

import sys
from pyspark import SparkContext, SparkConf
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, when, sum as spark_sum, round as spark_round
import re


def is_clean(title):
    """
    노이즈 필터링 함수
    스포츠, Wikipedia 내부 페이지 등을 제거
    """
    if not title:
        return False
    
    title_str = str(title).lower()
    
    # "playoff" 체크 (단, "layoff"는 제외 - Social_Impact 카테고리)
    if 'playoff' in title_str and 'layoff' not in title_str:
        return False
    
    # 스포츠 관련 키워드
    sports_keywords = [
        'nfl', 'nba', 'nhl', 'mlb', 'mls',
        'championship', 'cup', 'tournament', 'super bowl', 'world cup',
        'college football', 'college basketball', 'college baseball',
        'football', 'basketball', 'baseball', 'soccer', 'hockey',
        'olympics', 'olympic', 'fifa', 'uefa',
        'playoff', 'playoffs', 'semifinal', 'final', 'quarterfinal',
        'season', 'game', 'match', 'league', 'team', 'player', 'coach',
        'stadium', 'arena', 'field', 'court', 'pitch'
    ]
    
    for sport in sports_keywords:
        if sport in title_str:
            # 예외: "layoff"는 Social_Impact 카테고리이므로 제외
            if sport == 'playoff' and 'layoff' in title_str:
                continue
            return False
    
    # 기타 노이즈 키워드
    noise_keywords = [
        'file:', 'wikipedia:', 'user:', 'talk:', 'template:',
        'category:', 'help:', 'portal:', 'special:', 
        'dibiase', 'tobias', 'len_bias'
    ]
    
    for noise in noise_keywords:
        if noise in title_str:
            return False
    
    return True


def assign_category(title):
    """
    키워드를 카테고리에 매핑
    """
    if not title:
        return "Other"
    
    title_lower = str(title).lower()
    
    # 카테고리 정의
    categories = {
        "Technology": [
            "artificial_intelligence", "machine_learning", "deep_learning", 
            "generative_ai", "chatgpt", "openai", "gpt-4", "gpt_4",
            "large_language_model", "neural_network", 
            "transformer_(machine_learning_model)", "gemini_(chatbot)", 
            "grok_(chatbot)"
        ],
        "Application": [
            "automation", "prompt_engineering", "chatbot", "ai_art",
            "github_copilot", "midjourney", "stable_diffusion", 
            "robotics", "virtual_assistant"
        ],
        "Social_Impact": [
            "job_loss", "technological_unemployment", "labor_market", 
            "layoff", "universal_basic_income", "ai_ethics", "copyright",
            "deepfake", "hallucination", "bias"
        ]
    }
    
    for cat, keywords in categories.items():
        for k in keywords:
            if k in title_lower:
                return cat
    
    return "Other"


def process_line(line):
    """
    Wikipedia 데이터 라인 파싱
    포맷: domain title views size
    """
    try:
        parts = line.split(" ")
        if len(parts) < 3:
            return None
        
        domain = parts[0]
        title = " ".join(parts[1:-2])  # 제목이 공백 포함할 수 있음
        views = int(parts[-2])  # 마지막에서 두 번째가 views
        
        # 영어 위키만 처리
        if domain in ["en", "en.m"]:
            # 노이즈 필터링
            if is_clean(title):
                category = assign_category(title)
                # Other 카테고리는 제외
                if category != "Other":
                    return (title, views, category)
        
        return None
    except:
        return None


def run_analysis(sc, year, hdfs_path):
    """
    특정 연도의 데이터 분석
    """
    print("\n" + "=" * 60)
    print(">>> Processing Year: " + year + " from " + hdfs_path)
    print("=" * 60)
    
    # 데이터 로드 및 처리
    raw_rdd = sc.textFile(hdfs_path)
    
    # 파싱 및 필터링
    processed_rdd = raw_rdd.map(process_line) \
                            .filter(lambda x: x is not None)
    
    # 같은 제목끼리 조회수 합산 (카테고리도 함께 유지)
    # (title, views, category) -> (title, total_views, category)
    result_rdd = processed_rdd.map(lambda x: (x[0], (x[1], x[2]))) \
                              .reduceByKey(lambda a, b: (a[0] + b[0], a[1])) \
                              .map(lambda x: (x[0], x[1][0], x[1][1])) \
                              .sortBy(lambda x: x[1], ascending=False)
    
    # 결과를 딕셔너리로 변환 (병합을 위해)
    results = result_rdd.collect()
    result_dict = {}
    
    for title, views, category in results:
        result_dict[title] = {
            'views': views,
            'category': category
        }
    
    print("\n>>> Top 20 Keywords for " + year)
    print("-" * 60)
    for i, (title, views, category) in enumerate(results[:20], 1):
        print("%2d. %-50s : %10d (%s)" % (i, title[:50], views, category))
    print("-" * 60)
    
    return result_dict


def compare_years(data_2023, data_2025):
    """
    두 연도 데이터를 비교하여 변화율 계산
    """
    print("\n" + "=" * 60)
    print(">>> Year-over-Year Comparison (2023 → 2025)")
    print("=" * 60)
    
    # 모든 키워드 수집
    all_titles = set(data_2023.keys()) | set(data_2025.keys())
    
    comparison_results = []
    
    for title in all_titles:
        views_2023 = data_2023.get(title, {}).get('views', 0)
        views_2025 = data_2025.get(title, {}).get('views', 0)
        category = data_2025.get(title, {}).get('category') or \
                   data_2023.get(title, {}).get('category', 'Other')
        
        if category == 'Other':
            continue
        
        change = views_2025 - views_2023
        
        # 변화율 계산 (0으로 나누기 방지)
        if views_2023 > 0:
            change_pct = ((views_2025 - views_2023) / views_2023) * 100
        elif views_2025 > 0:
            change_pct = float('inf')  # 무한대 (새로 등장)
        else:
            change_pct = 0
        
        # 무한대 처리
        if change_pct == float('inf'):
            change_pct = 999999  # 매우 큰 값으로 표시
        
        comparison_results.append({
            'title': title,
            'category': category,
            'views_2023': views_2023,
            'views_2025': views_2025,
            'change': change,
            'change_pct': change_pct
        })
    
    return comparison_results


def print_top_keywords_by_category(comparison_results, year, top_n=15):
    """
    카테고리별 Top 키워드 출력
    """
    categories = ["Technology", "Application", "Social_Impact"]
    
    for category in categories:
        cat_data = [x for x in comparison_results if x['category'] == category]
        
        if year == "2023":
            cat_data.sort(key=lambda x: x['views_2023'], reverse=True)
            print("\n>>> Top %d Keywords in %s (%s) - 2023" % (top_n, category, len(cat_data)))
        else:
            cat_data.sort(key=lambda x: x['views_2025'], reverse=True)
            print("\n>>> Top %d Keywords in %s (%s) - 2025" % (top_n, category, len(cat_data)))
        
        print("-" * 60)
        for i, item in enumerate(cat_data[:top_n], 1):
            if year == "2023":
                print("%2d. %-50s : %10d" % (i, item['title'][:50], item['views_2023']))
            else:
                print("%2d. %-50s : %10d" % (i, item['title'][:50], item['views_2025']))
        print("-" * 60)


def print_rapid_changes(comparison_results, rising=True, top_n=10):
    """
    급상승/급하락 키워드 출력
    """
    if rising:
        # 급상승: 변화율이 큰 순서
        filtered = [x for x in comparison_results 
                   if x['views_2023'] > 0 and x['change_pct'] > 0]
        filtered.sort(key=lambda x: x['change_pct'], reverse=True)
        title_text = "급상승 키워드 (2023 → 2025)"
    else:
        # 급하락: 변화율이 작은 순서 (음수 또는 0으로 감소)
        filtered = [x for x in comparison_results 
                   if x['views_2023'] > 0 and (x['change_pct'] < 0 or x['views_2025'] == 0)]
        filtered.sort(key=lambda x: x['change_pct'])
        title_text = "급하락 키워드 (2023 → 2025)"
    
    print("\n>>> " + title_text)
    print("-" * 80)
    print("%-50s | %-15s | %10s | %10s | %12s" % 
          ("키워드", "카테고리", "2023 조회수", "2025 조회수", "변화율(%)"))
    print("-" * 80)
    
    for item in filtered[:top_n]:
        change_pct_str = "%.1f" % item['change_pct'] if item['change_pct'] < 999999 else "NEW"
        print("%-50s | %-15s | %10d | %10d | %12s" % 
              (item['title'][:50], item['category'], 
               item['views_2023'], item['views_2025'], change_pct_str))
    print("-" * 80)


def print_insights(comparison_results):
    """
    핵심 인사이트 요약 출력
    """
    print("\n" + "=" * 60)
    print(">>> 핵심 인사이트 요약")
    print("=" * 60)
    
    # 카테고리별 통계
    categories = ["Technology", "Application", "Social_Impact"]
    
    for category in categories:
        cat_data = [x for x in comparison_results if x['category'] == category]
        total_2023 = sum(x['views_2023'] for x in cat_data)
        total_2025 = sum(x['views_2025'] for x in cat_data)
        change_pct = ((total_2025 - total_2023) / total_2023 * 100) if total_2023 > 0 else 0
        
        print("\n[%s]" % category)
        print("  2023년 총 조회수: %d" % total_2023)
        print("  2025년 총 조회수: %d" % total_2025)
        print("  변화율: %.1f%%" % change_pct)
    
    # 급상승 키워드 Top 3
    rising = [x for x in comparison_results 
              if x['views_2023'] > 0 and x['change_pct'] > 100]
    rising.sort(key=lambda x: x['change_pct'], reverse=True)
    
    print("\n>>> 가장 급상승한 키워드 Top 3")
    for i, item in enumerate(rising[:3], 1):
        print("  %d. %s: %.1f%% 증가 (%d → %d)" % 
              (i, item['title'], item['change_pct'], 
               item['views_2023'], item['views_2025']))


if __name__ == "__main__":
    # Spark 설정
    conf = SparkConf().setAppName("WikiTrendAnalysis") \
                     .set("spark.sql.adaptive.enabled", "true") \
                     .set("spark.sql.adaptive.coalescePartitions.enabled", "true")
    
    sc = SparkContext(conf=conf)
    
    try:
        # 2023년 분석
        data_2023 = run_analysis(sc, "2023", "/user/spark/raw_data/2023/*.gz")
        
        # 2025년 분석
        data_2025 = run_analysis(sc, "2025", "/user/spark/raw_data/2025/*.gz")
        
        # 연도별 비교 분석
        comparison_results = compare_years(data_2023, data_2025)
        
        # 카테고리별 Top 키워드 출력
        print_top_keywords_by_category(comparison_results, "2023", top_n=15)
        print_top_keywords_by_category(comparison_results, "2025", top_n=15)
        
        # 급상승/급하락 키워드
        print_rapid_changes(comparison_results, rising=True, top_n=10)
        print_rapid_changes(comparison_results, rising=False, top_n=10)
        
        # 핵심 인사이트 요약
        print_insights(comparison_results)
        
    finally:
        sc.stop()


