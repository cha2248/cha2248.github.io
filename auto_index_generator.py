#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
전남 소방서 도상훈련 자동 인덱스 생성기
폴더 구조를 자동으로 분석하여 HTML 인덱스 파일을 생성합니다.
"""

import os
import re
import json
from pathlib import Path

def extract_region_from_folder(folder_name):
    """폴더명에서 지역명 추출"""
    # ★1(목포), ★8(해남) 등의 패턴에서 지역명 추출
    match = re.search(r'[★]?\d*\(?([가-힣]+)\)?', folder_name)
    if match:
        return match.group(1)
    return None

def extract_facility_name(folder_name):
    """폴더명에서 시설명 추출"""
    # ★(목포)푸른마을 노인전문요양원 -> 푸른마을 노인전문요양원
    # (목포)성모노인요양원 -> 성모노인요양원
    patterns = [
        r'[★]?\([가-힣]+\)(.+)',  # ★(지역)시설명 또는 (지역)시설명
        r'[★]?(.+)',  # 나머지
    ]
    
    for pattern in patterns:
        match = re.search(pattern, folder_name)
        if match:
            facility_name = match.group(1).strip()
            # 불필요한 문자 제거
            facility_name = facility_name.replace('★', '').strip()
            return facility_name
    
    return folder_name

def find_html_files(base_path):
    """지정된 경로에서 HTML 파일들을 찾아 지역별로 분류"""
    regions_data = {}
    
    # 360도 모바일 변환 폴더 찾기
    mobile_path = Path(base_path) / "360도 모바일 변환"
    
    if not mobile_path.exists():
        print(f"❌ 경로를 찾을 수 없습니다: {mobile_path}")
        return regions_data
    
    print(f"🔍 분석 중: {mobile_path}")
    
    # 각 지역 폴더 탐색
    for region_folder in mobile_path.iterdir():
        if not region_folder.is_dir():
            continue
            
        region_name = extract_region_from_folder(region_folder.name)
        if not region_name:
            continue
            
        print(f"\n📍 지역 발견: {region_name} (폴더: {region_folder.name})")
        
        if region_name not in regions_data:
            regions_data[region_name] = []
            
        # 시설 폴더들 탐색
        for facility_folder in region_folder.rglob("*"):
            if not facility_folder.is_dir():
                continue
                
            # HTML 파일이 있는 시설 폴더 찾기
            html_files = list(facility_folder.glob("*.html"))
            if not html_files:
                continue
                
            # .bak 파일 제외하고 메인 HTML 파일 선택
            main_html = None
            for html_file in html_files:
                if not html_file.name.endswith('.bak'):
                    main_html = html_file
                    break
                    
            if not main_html:
                continue
                
            # 시설명 추출
            facility_name = extract_facility_name(facility_folder.name)
            
            # 상대 경로 생성
            relative_path = main_html.relative_to(Path(base_path))
            
            facility_info = {
                'name': facility_name,
                'path': str(relative_path).replace('\\', '/')
            }
            
            regions_data[region_name].append(facility_info)
            print(f"  ✅ {facility_name} -> {relative_path}")
    
    return regions_data

def generate_html_content(regions_data):
    """지역 데이터를 기반으로 HTML 콘텐츠 생성"""
    
    # 전남 22개 시군 리스트 (순서대로)
    jeonnam_regions = [
        '목포', '여수', '순천', '나주', '광양', '담양', '곡성', '구례',
        '고흥', '보성', '화순', '장흥', '강진', '해남', '영암', '무안',
        '함평', '영광', '장성', '완도', '진도', '신안'
    ]
    
    # JavaScript 데이터 객체 생성
    js_regions_data = "        const regionsData = {\n"
    
    for region in jeonnam_regions:
        facilities = regions_data.get(region, [])
        js_regions_data += f"          '{region}': [\n"
        
        for facility in facilities:
            name = facility['name']
            path = facility['path']
            js_regions_data += f"            {{ name: '{name}', path: '{path}' }},\n"
            
        js_regions_data += f"          ],\n"
    
    js_regions_data += "        };"
    
    html_content = f'''<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>전남소방본부 피난약자시설 도상훈련</title>
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <div class="container">
        <header class="header">
            <div class="logo-section">
                <img src="logo.png" alt="전남소방본부 로고" class="logo">
                <h1>전남소방본부 피난약자시설 도상훈련</h1>
            </div>
        </header>

        <main class="main-content">
            <div class="region-grid" id="regionGrid">
                <!-- 지역 버튼들이 JavaScript로 동적 생성됩니다 -->
            </div>

            <div class="facility-section" id="facilitySection" style="display: none;">
                <h2 id="selectedRegion">선택된 지역</h2>
                <div class="facility-grid" id="facilityGrid">
                    <!-- 시설 버튼들이 JavaScript로 동적 생성됩니다 -->
                </div>
                <button class="back-button" onclick="showRegions()">← 지역 선택으로 돌아가기</button>
            </div>
        </main>

        <footer class="footer">
            <p>© 2024 전남소방본부. 모든 권리 보유.</p>
        </footer>
    </div>

    <script>
{js_regions_data}

        // 전남 22개 시군 순서
        const regionOrder = ['목포', '여수', '순천', '나주', '광양', '담양', '곡성', '구례', '고흥', '보성', '화순', '장흥', '강진', '해남', '영암', '무안', '함평', '영광', '장성', '완도', '진도', '신안'];

        function showRegions() {{
            document.getElementById('regionGrid').style.display = 'grid';
            document.getElementById('facilitySection').style.display = 'none';
            renderRegions();
        }}

        function showFacilities(regionName) {{
            document.getElementById('regionGrid').style.display = 'none';
            document.getElementById('facilitySection').style.display = 'block';
            document.getElementById('selectedRegion').textContent = regionName + ' 지역 시설';
            renderFacilities(regionName);
        }}

        function renderRegions() {{
            const regionGrid = document.getElementById('regionGrid');
            regionGrid.innerHTML = '';
            
            regionOrder.forEach(region => {{
                const facilityCount = regionsData[region].length;
                const button = document.createElement('button');
                button.className = `region-button ${{facilityCount === 0 ? 'no-facilities' : ''}}`;
                button.innerHTML = `
                    <span class="region-name">${{region}}</span>
                    <span class="facility-count">${{facilityCount}}개 시설</span>
                `;
                
                if (facilityCount > 0) {{
                    button.onclick = () => showFacilities(region);
                }} else {{
                    button.disabled = true;
                    button.title = '등록된 시설이 없습니다';
                }}
                
                regionGrid.appendChild(button);
            }});
        }}

        function renderFacilities(regionName) {{
            const facilityGrid = document.getElementById('facilityGrid');
            facilityGrid.innerHTML = '';
            
            const facilities = regionsData[regionName];
            facilities.forEach(facility => {{
                const button = document.createElement('button');
                button.className = 'facility-button';
                button.textContent = facility.name;
                button.onclick = () => {{
                    window.open(facility.path, '_blank');
                }};
                facilityGrid.appendChild(button);
            }});
        }}

        // 페이지 로드 시 지역 표시
        document.addEventListener('DOMContentLoaded', showRegions);
    </script>
</body>
</html>'''
    
    return html_content

def generate_summary_report(regions_data):
    """분석 결과 요약 리포트 생성"""
    total_facilities = sum(len(facilities) for facilities in regions_data.values())
    
    print("\n" + "="*50)
    print("📊 전남 피난약자시설 도상훈련 분석 결과")
    print("="*50)
    
    # 전남 22개 시군 순서대로 정렬
    jeonnam_regions = [
        '목포', '여수', '순천', '나주', '광양', '담양', '곡성', '구례',
        '고흥', '보성', '화순', '장흥', '강진', '해남', '영암', '무안',
        '함평', '영광', '장성', '완도', '진도', '신안'
    ]
    
    regions_by_count = {}
    for region in jeonnam_regions:
        count = len(regions_data.get(region, []))
        if count not in regions_by_count:
            regions_by_count[count] = []
        regions_by_count[count].append(region)
    
    print(f"총 시설 수: {total_facilities}개")
    print(f"등록된 지역 수: {len([r for r in jeonnam_regions if len(regions_data.get(r, [])) > 0])}개 / 22개")
    print()
    
    for count in sorted(regions_by_count.keys(), reverse=True):
        regions = regions_by_count[count]
        if count == 0:
            print(f"🔴 {count}개 시설: {', '.join(regions)} ({len(regions)}개 지역)")
        elif count < 5:
            print(f"🟡 {count}개 시설: {', '.join(regions)} ({len(regions)}개 지역)")
        else:
            print(f"🟢 {count}개 시설: {', '.join(regions)} ({len(regions)}개 지역)")
    
    print("\n" + "="*50)
    print("📋 지역별 상세 현황")
    print("="*50)
    
    for region in jeonnam_regions:
        facilities = regions_data.get(region, [])
        count = len(facilities)
        status = "🔴" if count == 0 else "🟡" if count < 5 else "🟢"
        print(f"{status} {region}: {count}개")
        
        for facility in facilities:
            print(f"    - {facility['name']}")
        
        if count == 0:
            print(f"    (시설 없음)")
        print()

def main():
    """메인 실행 함수"""
    print("🚀 전남소방본부 피난약자시설 도상훈련 자동 인덱스 생성기")
    print("="*60)
    
    # 현재 디렉토리를 기본 경로로 설정
    base_path = "."
    
    # 사용자에게 경로 확인
    current_path = os.path.abspath(base_path)
    print(f"현재 작업 디렉토리: {current_path}")
    
    user_input = input("다른 경로를 사용하시겠습니까? (y/N): ").strip().lower()
    if user_input == 'y':
        base_path = input("기본 경로를 입력하세요: ").strip()
        if not os.path.exists(base_path):
            print(f"❌ 경로가 존재하지 않습니다: {base_path}")
            return
    
    print(f"\n🔍 폴더 구조 분석 시작...")
    
    # 폴더 구조 분석
    regions_data = find_html_files(base_path)
    
    if not regions_data:
        print("❌ 분석할 데이터가 없습니다.")
        return
    
    # 요약 리포트 생성
    generate_summary_report(regions_data)
    
    # HTML 파일 생성
    html_content = generate_html_content(regions_data)
    
    output_file = "auto_generated_index.html"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"\n✅ HTML 파일이 생성되었습니다: {output_file}")
    
    # JSON 데이터도 저장 (디버깅용)
    json_file = "regions_data.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(regions_data, f, ensure_ascii=False, indent=2)
    
    print(f"📄 JSON 데이터 파일: {json_file}")
    print("\n🎉 완료!")

if __name__ == "__main__":
    main()
