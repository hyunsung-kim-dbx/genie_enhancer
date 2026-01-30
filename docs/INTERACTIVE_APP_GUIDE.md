# Genie Space 대화형 개선 도구 (Interactive Enhancement Tool)

## 🎯 개요

기존 자동화된 for-loop 방식에서 **사람의 승인이 필요한 대화형 방식**으로 전환했습니다.

### 기존 방식 (Automated)
```
run_enhancement.py 실행 → 자동으로 10번 반복 → 모든 변경사항 자동 적용 → 완료
```

### 새로운 방식 (Interactive with Human-in-the-Loop)
```
Streamlit 앱 실행
 ↓
벤치마크 업로드 + Genie Space 설정
 ↓
반복 1 실행 → 결과 표시 (한글) → 사용자 승인/거부
 ↓
승인하면 적용 → 반복 2 실행 → 결과 표시 → 승인/거부
 ↓
...
 ↓
목표 달성 or 중단 → 완료
```

---

## 🚀 Databricks Apps에 배포하기

### 1단계: 코드 업로드

Databricks 워크스페이스에 프로젝트 전체를 업로드:

```bash
# Databricks CLI 사용
databricks workspace import-dir \
  /Users/hyunsung.kim/genie_enhancer \
  /Workspace/Users/your.email@company.com/genie_enhancer \
  --overwrite
```

또는 Databricks UI에서:
1. Workspace → Users → [Your User]
2. 우클릭 → Import → 폴더 선택 → 업로드

### 2단계: Databricks App 생성

1. Databricks 워크스페이스에서 **Apps** 클릭
2. **Create App** 버튼 클릭
3. 다음 설정 입력:
   - **Name:** Genie Space 개선 도구
   - **Source:** `databricks_apps/interactive_enhancement_app.py`
   - **Compute:** 기존 클러스터 선택 (또는 Serverless)
   - **Permissions:** 필요한 사용자에게 권한 부여

4. **Create** 클릭

### 3단계: 앱 실행

1. Apps 목록에서 방금 만든 앱 클릭
2. **Start** 버튼 클릭
3. 몇 초 후 Streamlit UI가 로드됩니다

---

## 📱 사용 방법

### 단계 1: 벤치마크 업로드

<img src="docs/images/step1_upload.png" width="600">

1. 벤치마크 JSON 파일 준비:
```json
[
  {
    "id": "1",
    "question": "Discord에서 가장 많은 반응을 받은 메시지는?",
    "expected_sql": "SELECT * FROM message ORDER BY reaction_count DESC LIMIT 10"
  },
  {
    "id": "2",
    "question": "Steam에서 가장 높은 평점을 받은 리뷰는?",
    "expected_sql": "SELECT * FROM review ORDER BY score DESC LIMIT 10"
  }
]
```

2. **파일 업로드** 버튼 클릭
3. JSON 파일 선택
4. 미리보기에서 내용 확인
5. **다음 단계로** 버튼 클릭

### 단계 2: Genie Space 설정

<img src="docs/images/step2_configure.png" width="600">

**Databricks 연결:**
- Databricks 호스트: `your-workspace.cloud.databricks.com`
- Personal Access Token: 설정 → 사용자 설정 → Access Tokens에서 생성
- Genie Space ID: 개선할 Space의 ID (Space URL에서 확인)

**개선 설정:**
- 목표 점수: 90% (기본값)
- 최대 반복 횟수: 10회
- LLM 엔드포인트: `databricks-meta-llama-3-1-70b-instruct`

**개선 시작** 버튼 클릭

### 단계 3: 반복 실행 및 검토

<img src="docs/images/step3_review.png" width="600">

각 반복마다:

1. **자동 실행:**
   - 벤치마크 평가
   - 실패 분석
   - 개선안 생성

2. **결과 표시 (한글):**
   - 현재 점수
   - 제안된 변경사항 (동의어, 조인, 설명 등)
   - 실패한 벤치마크 상세 정보

3. **3가지 선택:**
   - ✅ **승인 및 적용**: 변경사항을 Genie Space에 적용하고 다음 반복으로
   - ❌ **거부 및 건너뛰기**: 이번 변경사항은 건너뛰고 다음 반복으로
   - ⏸️ **개선 중단**: 지금까지 적용한 변경사항만 유지하고 종료

### 단계 4: 완료

<img src="docs/images/step4_complete.png" width="600">

- 점수 추이 그래프
- 적용된 변경사항 요약
- 새로운 개선 시작 버튼

---

## 🎨 UI 특징

### 1. 한글 인터페이스
모든 UI 텍스트가 한글로 표시됩니다:
- 단계 설명
- 변경사항 설명
- 에러 메시지
- 버튼 레이블

### 2. 직관적인 변경사항 표시

**변경 유형별 한글 표시:**
- `add_synonym` → "동의어 추가: `테이블`.`컬럼` → '동의어'"
- `add_join` → "조인 추가: `테이블1` ↔ `테이블2`"
- `add_column_description` → "컬럼 설명 추가: ..."
- `create_metric_view` → "메트릭 뷰 생성: ..."

### 3. 실패 분석 상세 정보

실패한 벤치마크마다:
- 질문 내용
- 예상 SQL vs Genie 생성 SQL (병렬 표시)
- 실패 카테고리 (한글)
- 실패 이유

### 4. 진행 상태 사이드바

왼쪽 사이드바에 항상 표시:
- 현재 단계 (1️⃣ ~ ✅)
- 반복별 점수 추이
- 자동 새로고침 옵션

---

## 🔧 아키텍처 변경 사항

### 변경 전 (Automated)

```python
# run_enhancement.py
job = EnhancementJob(config)
result = job.run()  # 자동으로 모든 반복 실행
```

**문제점:**
- 사용자가 변경사항을 검토할 수 없음
- 잘못된 변경사항도 자동 적용
- 중간에 중단 불가능
- 영어 로그만 제공

### 변경 후 (Interactive)

```python
# databricks_apps/interactive_enhancement_app.py
# Streamlit 세션 상태로 단계별 진행
if st.session_state.step == 'review':
    # 변경사항 표시
    if st.button("승인 및 적용"):
        # 사용자가 승인한 경우에만 적용
        apply_changes()
```

**장점:**
- ✅ 각 변경사항을 검토하고 승인/거부 가능
- ✅ 예상치 못한 변경사항 차단
- ✅ 언제든 중단 가능
- ✅ 한글 UI로 비개발자도 사용 가능
- ✅ 실시간 피드백
- ✅ 안전성 향상

---

## 💾 데이터 저장

### For-loop 유지 (백엔드)

실제 반복 로직은 여전히 for-loop 방식을 사용하되, **각 반복 후 사용자 승인을 기다립니다**.

```python
# 내부적으로는 여전히 for-loop
for iteration in range(1, max_iterations + 1):
    # 1. 벤치마크 평가
    results = scorer.score(benchmarks)

    # 2. 변경사항 생성
    changes = enhancer.enhance(...)

    # 3. Streamlit에 표시하고 대기
    st.session_state.proposed_changes = changes
    st.session_state.step = 'review'

    # 사용자 승인 대기...
    # (Streamlit은 비동기이므로 세션 상태로 처리)

    # 4. 승인되면 적용
    if user_approved:
        space_updater.update_space(...)
```

### Delta Table 저장

모든 반복 결과는 여전히 Delta 테이블에 저장됩니다:

```python
# pipeline/delta_reporter.py 사용
reporter = DeltaReporter(catalog="genie_enhancement")

# 반복마다 기록
reporter.report_iteration(
    iteration_number=iteration,
    benchmark_results=results,
    changes_made=changes if approved else [],
    user_approved=approved
)
```

### Lessons Learned (Markdown)

승인된 변경사항만 lessons learned에 기록:

```python
# pipeline/lessons_learned_enhanced.py
lessons = EnhancedLessonsLearned()

if user_approved:
    lessons.record_iteration(
        run_id=run_id,
        iteration=iteration,
        changes_applied=changes,
        ...
    )
    # lessons/lessons_learned.md에 자동 업데이트
```

---

## 🔄 기존 자동화 스크립트와 병행

기존 `run_enhancement.py`도 유지됩니다!

### 사용 시나리오

**대화형 앱 (Interactive App):**
- ✅ 프로덕션 Genie Space 변경
- ✅ 중요한 Space 개선
- ✅ 비개발자가 사용
- ✅ 변경사항을 신중하게 검토

**자동화 스크립트 (Automated):**
- ✅ 개발/테스트 환경
- ✅ 야간 배치 작업
- ✅ CI/CD 파이프라인
- ✅ 많은 Space를 일괄 개선

```bash
# 자동화 (여전히 사용 가능)
python3 run_enhancement.py

# 대화형 (새로운 방식)
# Databricks Apps에서 실행
```

---

## 📊 Delta Table 스키마 (변경 없음)

Delta 테이블 구조는 동일하게 유지:
- `enhancement_runs`: 전체 실행 기록
- `enhancement_iterations`: 반복별 상세 기록
- `enhancement_changes`: 개별 변경사항
- `enhancement_benchmarks`: 벤치마크 결과
- `enhancement_lessons_learned`: 학습 내용

새로 추가된 필드:
- `user_approved`: Boolean (사용자가 승인했는지)
- `approval_timestamp`: Timestamp (승인 시간)

---

## 🎯 다음 단계

### 즉시 가능:

1. ✅ Databricks Apps에 배포
2. ✅ 벤치마크 JSON 준비
3. ✅ 테스트 Space에서 시도

### 추가 개선 (선택):

1. **이메일 알림:**
   - 각 반복 완료 시 이메일 발송
   - 사용자가 링크를 클릭해서 검토

2. **Slack 통합:**
   - Slack에서 직접 승인/거부

3. **변경사항 diff 보기:**
   - 설정 변경 전/후 비교

4. **롤백 기능:**
   - 이전 반복으로 되돌리기 버튼

5. **다중 사용자 승인:**
   - 팀장 승인 필요 등

---

## 🐛 트러블슈팅

### 앱이 시작되지 않음

**증상:** "App failed to start" 에러

**해결:**
1. 클러스터가 실행 중인지 확인
2. 필요한 라이브러리 설치 확인:
```bash
pip install streamlit plotly pandas
```
3. 파일 경로가 올바른지 확인

### 벤치마크 파일 업로드 실패

**증상:** "Invalid JSON" 에러

**해결:**
1. JSON 형식 검증: https://jsonlint.com
2. 인코딩이 UTF-8인지 확인
3. 파일 크기가 10MB 이하인지 확인

### Genie API 연결 실패

**증상:** "Failed to initialize clients" 에러

**해결:**
1. Databricks 호스트 형식 확인 (https:// 제외)
2. Personal Access Token이 유효한지 확인
3. Space ID가 정확한지 확인
4. 토큰에 Genie Space 권한이 있는지 확인

### 변경사항 적용 후 에러

**증상:** "Failed to apply changes" 에러

**해결:**
1. Space updater 권한 확인
2. 변경사항이 유효한지 검증 탭에서 확인
3. Genie Space가 다른 곳에서 수정 중이 아닌지 확인

---

## 📞 지원

문제가 발생하면:
1. 앱 로그 확인 (Databricks Apps → Logs 탭)
2. `IMPLEMENTATION_STATUS.md`에서 알려진 이슈 확인
3. 이슈 트래커에 보고

---

**이제 안전하고 투명한 방식으로 Genie Space를 개선할 수 있습니다!** 🎉
