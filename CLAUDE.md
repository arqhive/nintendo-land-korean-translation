# 닌텐도 랜드(Wii U) 한글화

## 현재 단계
- **한글 글꼴 확정(11/06 사용자): 티머니 둥근바람**(noonnu 458, PC 사용자 글꼴 폴더 설치본 → `tools/fonts/` 복사, git 제외·재배포 금지, 임베딩 허용)
  - `work/font_calib.json`: Msg 43/**Regular**(사용자 결정), M 50/ExtraBold, L 114/ExtraBold(M과 맞춤), Ruby 21/Regular. 이전 Noto 값은 `work/font_calib_noto.json`
  - `font_render.FONT_PATH` 가 {400: Regular, 800: ExtraBold} 사전이면 가까운 굵기 파일을 씀(nl_font 에서 설정)
  - 한글은 번역에 쓰인 870자 — 창을 못 찾은 줄(291)이 있어 빌드 때 네 폰트(Msg·M·L·Ruby)에 모두 넣는 게 안전
- **진짜 원인(11/06): 내 Yaz0 헤더 8~11바이트 정렬값을 0으로 씀** — 원본은 0x2000/0x100. KR5(크기 맞춤)·KR6(원본 내용 재압축)도 오류였던 이유. `yaz0_compress(..., align=)` 로 원본 값 복사하게 고침 → v0.3
  - **실기 KR7·KR8 모두 정상(11/06)** → 크기 제한 없음, 원인은 헤더 정렬값뿐. 로고 색 줄이기 끔(`POSTER_BITS = 8`, 투명 칸 색만 0)
  - **정식 빌드 v0.3 = KR8_v0.3_FullColor 와 4개 파일 MD5 같음**(`work/build/v0.3/`). **SD 정리(11/06): 게임 폴더엔 `NintendoLandKR`(v0.3) 하나만**, 시험 묶음 KR1~8·v0.1 은 `D:\wiiu\_sdcafiine_hold\0005000010101F00\`
  - 번역 검토 페이지 `python -I tools/review_page.py` → `work/review/번역본.html`(git 제외, 어트랙션별·검색·id 찾기)
  - **규칙: Yaz0 재압축은 원본 헤더 정렬값을 그대로(`align=yaz0_align(원본)`)**. 빌드 결과 헤더 8~15 바이트가 원본과 같은지 확인
- 원인 1차 판단: Static2.pack(로고 묶음) — KR1·KR2 정상, KR3(로고)만 부팅 오류(11/06 실기)
  - (헛짚음) v0.2: 크기 탓으로 보고 로고 색 5비트로 줄여 원본 크기에 맞춤 → KR5 오류, 원본 내용 재압축만 한 KR6 도 오류 → 크기가 아님
- v0.1 실기에서 「An error has occurred」(11/06)
  - 원본보다 커진 건 Static2.pack(+150KB, 로고 szs 재압축이 약해서)뿐 → 촘촘한 압축 `yaz0_compress_best`(지연 매칭·체인 256)로 v0.1b(+79KB)
  - 시험 묶음 4개를 SD `D:\wiiu\sdcafiine\0005000010101F00\` 에 넣음(실행 때 고르는 화면): KR1_TextOnly / KR2_Text_Ninja / KR3_Text_Logo / KR4_Full (`work/build/bisect/`). 에러 난 v0.1 은 `D:\wiiu\_sdcafiine_hold\0005000010101F00\NintendoLandKR_v0.1` 로 옮김
- 8단계 첫 전체 빌드 v0.1(11/06)
  - `python -I tools/build.py v0.1 [--sd D:]` → `work/build/v0.1/sdcafiine/0005000010101F00/NintendoLandKR/content/` 4개(AllMessage.szs·Font.szs 는 업데이트판 기준, Nzm_Cmn.pack 은 본편, Static2.pack 은 업데이트판), md5 `work/build/v0.1/md5.json`, 약 20초
  - 메시지 2,660줄 넣음(원문과 같은 233줄 빼고 2,427줄 실제 변경), 폰트: Msg 1,211자(시트 4→3)·M 1,143자(3→4)·Ruby 1,183자(1)·L 420자(6→7, L 창·창 못 찾은 줄 글자만)
  - 폰트 글자: 번역문 전체 글자 + 영숫자·가나(일본어 Mii 이름 대비)·아이콘 글자, 원본 글자 모양 어긋남 0. M 폰트엔 「·」가 없어 「・」 그림에 연결(ALIAS)
  - 그림: .arc 는 같은 길이로 제자리 덮어쓰기(sarc_patch_same_size, .arc 재배치는 원본과 달라짐), .szs 는 다시 압축, .pack 은 재배치(왕복 확인됨). 바꾼 szs 외엔 바이트 같음 확인
- **6단계 그림 변환 끝(11/06)**: `python -I tools/gfx_build.py` → `work/gfx_out/*.bflim` 11개 + `manifest.json`(넣을 묶음 경로), 비교 `graphics/비교/최종_원본_한글.png`
  - GPT 결과 5장(05 동물의 숲은 3차에서 확정, 1차는 로고가 90%로 줄어 재요청). 원본에서 역산한 규칙: 기술 띠 BC5 R=글자 속/0~20px 테두리, G=-9~-13px 페이드 / 작은 로고=큰 로고 0.3배(알파 곱 축소) / 그림자 BC4=작은 로고 알파 0.39배 BOX, (3,3)·(4,2), 블러 0.5(`work/shadow_fit.json`)
  - GPT 로고 안쪽 투명 구멍(04: 1047px, 05: 56px)은 흰 판 색으로 메움(+구멍 테두리 회색 선 제거)
  - 인코더 검증: 원본 왕복 RGBA8 바이트 동일, BC 평균 오차 0.07~0.18
- 6단계 그림: GPT 요청 꾸러미(11/06) → 사용자가 GPT에 요청, 결과는 각 폴더 `결과.png`**
  - `graphics/GPT_요청/요청문.md` + 폴더 01~05(원본·마스크·미리보기). GPT에 맡기는 것 5장: 기술 띠 3(흑백 글자 마스크로 받음), 큰 로고 2(투명 컬러)
  - Claude 몫: 기술 띠 BC5 R(글자 속/테두리)·G(바깥 테두리) 채널 생성, 작은 로고 2장 축소, 그림자 마스크 2장(BC4) 재생성
  - 그림 위치: Nzm_Cmn.pack → Nzm_Waza_00.szs → timg/Nh_NzmWaza_00~02^t.bflim(740×180 BC5), Static2.pack → AttractionLogo_00.szs(Te_AttractionLogoJP_09·05^l RGBA8 210×150·236×154, Nt_AttractionLogoShJP_09·05^s BC4) / AttractionLogo_01.szs(Te_AttractionLogoLJP_09·05^q BC3 700×500·788×512, 그림자 같음). 업데이트판 Static2.pack 도 같은 그림을 가짐
- 5단계: 1차 번역 끝(2026-11-06, 2,660줄 전부), 사용자 결정 반영
  - 번역 6묶음(에이전트 병렬): `translation/ko/{statue,ttl,common_msg,common_layout,pkm_mtr,attractions}.json` → `translation/messages.json` ko 칸에 합침
  - 작업 묶음 `tools/make_packets.py` → `work/tl/packet_*.json`, 검사 `python -I tools/check_ko.py <묶음>`(누락·태그·아이콘 글자·아이콘 뒤 조사·일본어·넘침·용어·금지 부호·줄 끝 부호 경고)
  - 번역 규칙 `docs/translation_rules.md`, 버튼 아이콘 표 `docs/icons.md`(폰트 그림으로 확인: =A … =GamePad), 결정 목록 `docs/translation_decisions.md`(note 97)
  - 창 연결 규칙 추가: 코스·미션·마스터 조건·옵션·아이템·스탬프·게임 모드 이름 → 각 표시 창(winmap RULES). 글 있는 줄 중 rel 399
  - 묶음끼리 통일: 全X=전 X, ほおばり=볼 가득
  - 사용자 결정(11/06 결정 목록 표 검토): あそびかた=**하는 법**(5줄), 3772 アナタの失敗=**당신의 실패**. 나머지 말장난 27줄·기타 항목은 지금 번역 그대로(고칠 번호만 지정받음)
  - ReplaceList.msbt(음성 읽기 목록)는 화면에 안 나와 원문 그대로
- 5단계 용어집·말투표 승인됨(2026-11-06)
  - 확정본: `translation/glossary.json`(591개) + `docs/glossary.md`, 말투 `docs/tone.md`
  - 사용자 결정: キャンディー=사탕, レディ=레이디(폴린은 이 게임 뒤 결정), マリオチェイスのスター=스타, デカブリン·ハヤブリン=음역, **닌자성 般若·焙烙玉·マキビシ=그냥 읽기**(한냐·호로쿠다마·마키비시), 기술 띠 鷹の目·三方手裏剣=뜻 살림(매의 눈·세 갈래 수리검), ジーマ=지머, 피크민 제안안, ゲッソー=징오징오
  - 말투: 모니타 하십시오체(가타카나 어미 흉내 안 냄), 공주 하오체(나·그대·○○ 공), 다크 모니타 해요체, 석상 명판 명사형, 시스템 「~하세요」·확인 「~하시겠습니까?」, 팁 「~해 보자」, アナタ는 문맥상 빼고 필요하면 「손님」, さん=「○○ 님」
  - 사용자 지시: **공식 발매된 적이 있는 이름은 충실히 따른다**(닌텐도 레퍼런스가 많음)
  - 공식 이름 조사: `work/glossary/research_{zelda,metroid,pikmin,others}.json` → 합본 `work/glossary/merged.json`(589개: 공식 88·제안 231·일반 270)
  - 화자표 `tools/assign_speakers.py` → messages.json speaker 칸(모니타 528, 공주 42, 수련 17, 다크 모니타 17, 가짜 공주 1, 석상 명판 130…)
  - 피크민 공식 근거: 한국닌텐도 피크민 도감 `nintendo.com/kr/character/pikmin/assets/data/book.json`(차피·풍선호롱 확인)
- 4단계 전수 추출 끝·조사 범위 확정(2026-11-06)
- **전자 설명서(manual.bfma)는 범위에서 뺌**(사용자 결정 11/06). 릴리즈 문서에 「설명서는 일본어 그대로」 적을 것
- 조사 범위 표 `work/survey/scope.md`(`tools/survey_all.py`·`survey_report.py`·`tex_survey.py`·`tex_sheets.py`)
  - 잎 파일 16,554개 4가지 인코딩 문자열 검사, 고유 그림 7,959장 디코드·눈 검토(검토 결과 `work/survey/tex/review_part0~3.json`)
  - 게임 안 일본어 그림 7장: Nzm_Waza_00 의 Nh_NzmWaza_00~02(기술 띠), AttractionLogo_00/01 의 Te_AttractionLogo(L)JP_09·05(+그림자 Nt_…ShJP 마스크)
  - 설명서(manual.bfma): 본문 조각 513(좌표 배치 형식)·일본어 그림 13·JPEG 54 → 범위 미정
  - 추정(실기 확인 필요): 레이아웃 기본 글은 안 보임, ffsd Mii 이름은 MiiName.msbt 로 덮음
- 번역용 JSON `translation/messages.json`(`tools/make_tl_json.py`, git 제외): ja·en(북미판)·voiced·box·max_w·max_lines
- 화자: MSBT ATR1 은 비어 있음 → 5단계에서 장면 읽어 화자표 작성(대부분 모니타, 닌자성에 わらわ 쓰는 공주 등)
- Yaz0 풀기 빠른 판(겹치지 않는 복사 한 번에) — 2.8GB 전체 펼치기 약 10분
- 3단계 창 측정 끝(2026-11-06)
- 2단계 출력 시험 실기 통과 (2026-11-06, Aroma SDCafiine)

## 창 측정 (3단계)
- 글 상자 906개(`work/survey/textboxes.json`, FLYT v2.2), 부품 참조 900개(`layout_parts.json`)
- 폭 계산 = Σ char_w × (fontSize.x / FINF.width) + 자간 — 레이아웃 기본 일본어 409개 중 393개 상자 안(넘는 16개는 자리 표시 글)으로 검증
- 메시지 → 창 연결 `tools/winmap.py` → `work/survey/winmap.json`
  - exact(라벨=텍스트 ID) 229 / stem(이름 줄기) 432 / part(부품 이름) 74 / rule(장면·공통 메시지 종류 규칙) 1,289 / 못 찾음(rel) 636 (글 있는 2,660줄 기준)
  - 연결한 창에 원문이 넘치는 줄 26개뿐 → 그런 줄은 원문 크기를 한도로 씀
  - 일본어 실행은 `_JpJa` 상자를 씀(언어별 상자가 따로 있음, `_EuXx`·`_UsXx` 제외)
  - 장면 라벨: `_W` 큰 글씨(L), `_S`/MsgS 보조 줄(M), `_D`·`_T` 게임패드·TV
- 창 크기 표 `work/survey/window_table.md`(`tools/window_table.py`), 주요 창
  - 모니타 등 대사창 GameWindow_00 _JpJa: Msg 34.4, 폭 950 = 한글 28자 × 2줄 (578줄)
  - 석상 설명 Cmg_ScrollWindow_00 T_Text_00: 흐르는 띠, 폭 제한 없음 / 석상 이름 T_Prize_00 810 = 22자
  - 공통 창 Cmn_MsgWindow_00 800 = 21자 × 5줄, AdviceWindow 770 = 22자 × 4줄, NoticeWindow 800 = 21자 × 4줄
  - 시작 알림 StartCall_00 L 77.3, 1000 = 13자 / 성공 Success_00 L 107.1, 900 = 9자
- 넘침 검사 `python -I tools/check_overflow.py <번역.json>`(원문 넣으면 넘침 0 확인)
  - rel 줄은 원문 폭 × 1.0 이 한도(보수적, 짧은 버튼은 실제 상자가 더 넓을 수 있음)
  - 변수 태그(이름·숫자)는 폭 0으로 셈 → 「변수 있음」 줄은 따로 봐야 함
- 확인 못 한 위험
  - 부모 상자 배율·부품 magnify 는 계산에 안 넣음
  - Success_00·Failure_00·Win_00 의 T_Char_00… 글자별 상자(애니메이션용으로 보임) — 실기에서 확인
  - 광장 말풍선 Ttl_TalkBalloon_00 은 시스템 폰트 CafeStd_25 — Miiverse 글·Mii 이름만 나와 번역 대상 아님
  - 시험 문구 「확인 중」(동작 확인 화면, 상자 120px)은 133px 로 넘침 → 번역 때 짧게
- 실행 환경: 실기 Wii U Aroma SDCafiine만(Cemu는 안 봄, 이 PC에 없음). SD 경로 `D:\wiiu\sdcafiine\0005000010101F00\NintendoLandKR\content\JpJapanese\`
- 판본: 일본판 본편 + 업데이트 v32 (11/06 사용자 「진행해」)
- 시험 빌드: `python -I tools/build_test.py` → `work/build/test/`(sdcafiine·cemu), 시험 문구 `work/test_strings.json` 16줄
  - 시작 화면 「Wii U GamePad를 터치해서 시작」, 일시정지 메뉴, 광장 메뉴(Ttl_TopMenu_00)
  - L 폰트만 시트 6→7장(칸 384 < 357+56). 멈추면 L 시트 증설부터 의심

## 판본
| 폴더 | 제품 코드 | 지역 | 버전 |
|---|---|---|---|
| `Nintendo Land [Game] [0005000010101f00]` | WUP-P-ALCJ | 일본 | v16 |
| `Nintendo Land [Update] [0005000e10101f00]` | WUP-U-ALCJ | 일본 | v32 |
| `Nintendo Land [Game] [0005000010102000]` | WUP-P-ALCE | 북미 | v0 |
| `Nintendo Land [Update] [0005000e10102000]` | WUP-U-ALCE | 북미 | v32 |

- 원본은 복호화된 폴더(code/content/meta). 해시: `work/hashes/<타이틀ID>.md5`
- 원본 폴더 안 파일은 절대 고치지 않는다. 작업은 `work/` 아래 사본으로.
- 경로에 대괄호가 있으므로 PowerShell은 `-LiteralPath`, 셸 glob·`find -path` 패턴에 경로를 그대로 넣지 않는다.

## 구조 (조사 결과)
- 언어 데이터는 `content/JpJapanese/` 하나에 모임(다른 언어 폴더는 비어 있음)
  - `Message/AllMessage.szs` = Yaz0 → SARC(3) → SARC → MSBT 341개
    - SceneMessage 70, LayoutMessage 233, CommonMessage 38
    - 메시지 4,908개, 약 43,000자, 서로 다른 글자 1,143
    - MSBT: 빅엔디언, UTF-16(enc=1), 구역 LBL1·ATR1·TXT2
    - 태그 상위: 0:0 후리가나(2,673), 0:3 색(746), 6:x·3:x·8:x 변수류
  - `Layout/Font.szs` = Yaz0 → SARC → BFFNT 8개(v3, 시트 1024², 포맷 12=BC4)
  - `Voice/*.sarc` = 음성(일본어 그대로)
- 업데이트 v32가 `AllMessage.szs`·`Font.szs`·`Voice/Ttl.sarc`를 덮어씀 → **업데이트판이 기준**
- 그림(bflim 2,738개)은 `Common`에 있고 지역판끼리 같은 파일. **단, 같은 묶음 안에 일본판 전용 그림이 따로 있음**(4단계에서 발견: `Te_AttractionLogoJP_09·05` 등, 1단계의 「언어별 그림 없음」은 틀렸음)
  - 일본·북미 차이는 Pkm_Cmn.pack 안 .fmp 2개, Static.pack 안 gsys.bgmsconf 1개, RegionLang.txt, rpx, 사운드뿐
- 레이아웃 bflyt 551개, txt1 906개. 박힌 글은 자리 표시용(「１位」「ＷＷＷさん」), 실행 중 LayoutMessage로 덮음(4단계에서 실제 표시 여부 확인)
- RPX(.rodata)의 일본어는 Shift-JIS 디버그 문구(힙·리소스 관리 이름) → 화면 표시 아님(추정)
- meta: 부팅 화면·아이콘은 영어 로고 「Nintendo Land」→ 그대로

### 폰트
| 파일 | 칸(px) | 시트 | 칸 수 | 원본 글자 | 레이아웃 사용 |
|---|---|---|---|---|---|
| LunchMsg_A4 | 42×51 | 4 | 1,748 | 1,547 | 118 |
| LunchM_LA4Packed | 54×62 | 3 | 864 | 608 | 166 |
| LunchRuby_A4 | 21×27 | 1 | 1,656 | 957 | 80 (후리가나) |
| LunchL_LA4Packed | 118×127 | 6 | 384 | 357 | 67 |
| LunchG0/G1_LA4Packed | 57×64 / 56×60 | 1 | 120/128 | 95/96 | 18/9 (영숫자) |
| LunchPic_RGBA8 | 96×70 | 1 | 70 | 40 | 그림 기호 |
| LunchSNum_LA4Packed | 33×32 | 1 | 15 | 14 | 숫자 |
- 쓰는 글자만 담은 부분 폰트. 한글도 번역에 쓴 글자만 넣는다(한자·가나는 빼고 교체).

## 왕복 재빌드 검증 (2026-11-06)
- SARC(바깥 1·안쪽 3·폰트 1) 무변경 재작성 = 원본과 바이트 동일(정렬: 메시지 256, 폰트 8192)
- MSBT 341개 무변경 재작성 = 전부 바이트 동일(구역 사이 0xAB 채움)
- Yaz0 재압축은 아직(압축기 미작성, 압축 결과는 원본과 바이트가 다를 수 있음 → 풀었을 때 같은지로 검증)

## 분야 목록 (안)
- 텍스트(MSBT), 폰트(BFFNT)
- 해당 없음(조사 기준): 지역별 그림 없음, 영상은 부팅 영상뿐, 음성은 일본어 그대로(자막은 MSBT)
- 4단계에서 확인: 3D 모델·텍스처 속 일본어 글자, 전자 설명서(manual.bfma)

## 실행 환경
- 실기 Wii U(Aroma SDCafiine)만. Cemu 확인 안 함(사용자 11/06)

## 폰트 한글 넣기 (2단계에서 정함)
- `tools/nl_font.py`: 환영이문록 도구(bffnt_tool·font_atlas·font_render·addrlib·gtx_lib) 재사용
  - 시트 = BC4 + 시트마다 뱅크 스위즐 회전 + 상하 반전(font_atlas)
  - packed 폰트 값 = 128·D + 127·F, 테두리 반경 3.75px(M·L 모두, 원본 역산 오차 약 2)
  - 크기·굵기 역산값 `work/font_calib.json`: Msg 45/700, M 51/500, L 117/500, Ruby 22/450 (Noto Sans KR VF, 시험용·최종 글꼴 미정)
  - 굵기 측정 획 폭 상한은 셀 높이/8 (`font_render.MAXRUN`), L 폰트 획이 6px 넘음
- 원본 글자는 셀 그대로 옮기고, 한글 폭 = 한자 최빈 폭(Msg 42, M 52, L 110, Ruby 21)
- Yaz0 압축기 `nlib.yaz0_compress`(풀면 원본과 같음 확인), MSBT 문자열 ↔ 바이트 `str_to_msbt`(4,908줄 왕복 일치)

## 도구
- `tools/nlib.py` Yaz0 풀기, SARC 읽기/쓰기, MSBT 읽기/쓰기
- `tools/roundtrip.py`, `tools/roundtrip_msbt.py` 왕복 검증
- `tools/inspect_font.py` BFFNT 조사, `tools/scan_bflyt.py` 레이아웃 조사, `tools/scan_rpx.py` RPX 문자열
- `tools/cmp_regions.py`, `tools/cmp_pack.py` 지역판 비교, `tools/hash_tree.py` 해시
- 파이썬은 `python -I tools/...` 로, 출력은 `sys.stdout.reconfigure(encoding="utf-8")`(`-I`는 PYTHONIOENCODING 무시)
