닌텐도 랜드 (Wii U) 한글 패치 {VER}
제작: arqhive

「Nintendo Land」(Wii U, 일본판) 비공식 한국어 팬 패치입니다.
대사·메뉴·안내문 전체, 게임 폰트, 글씨가 그려진 그림(닌자성 기술 이름·일본판 전용 어트랙션 로고)을 한글로 바꿉니다.


[준비물]

- 일본판 「Nintendo Land」의 복호화된 게임 파일 두 가지.
    본편      타이틀 ID 0005000010101F00
    업데이트  타이틀 ID 0005000E10101F00 (v32)
  각 폴더 안에 code, content, meta 폴더가 있어야 합니다. 암호화된 상태(.app)로는 안 됩니다.
  북미판·유럽판에는 적용할 수 없습니다.
- 윈도우 PC와 약 100MB의 여유 공간.
- Wii U 실기: Aroma 등 CFW와 SDCafiine 플러그인, SD 카드.


[한글판 만들기]

1. ALCJ_KPatch_{VER}.zip 을 폴더째 압축을 풉니다.
2. 본편·업데이트 게임 폴더가 함께 든 상위 폴더를 "패치하기.bat"에 끌어다 놓습니다.
   본편 폴더와 업데이트 폴더를 둘 다 골라 한꺼번에 끌어다 놓아도 됩니다.
   그냥 실행하면 경로를 묻습니다.
3. 원본 찾기·확인 → 한글판 만들기 → 결과 확인이 차례로 진행됩니다. 2~3분 걸립니다.
   결과는 ALCJ_KPatch_{VER}\출력 폴더에 생깁니다. 원본 파일은 바뀌지 않습니다.

- 이미 패치한 파일이나 다른 판을 넣으면 원본 확인 단계에서 멈춥니다.


[Wii U 실기 (SDCafiine)]

1. 출력\sdcafiine 폴더 안의 내용을 SD 카드의 wiiu\sdcafiine\ 에 복사합니다.
   다음과 같이 파일이 놓이면 됩니다.

     sd:/wiiu/sdcafiine/0005000010101F00/NintendoLandKR/content/...

2. SDCafiine 플러그인을 켠 상태로 게임을 실행합니다.


[Cemu]

1. 출력\cemu\NintendoLand_Korean 폴더를 Cemu 의 graphicPacks 폴더에 복사합니다.
2. Cemu 의 그래픽팩 설정에서 Nintendo Land → Mods → Korean Translation 을 켭니다.


[알려진 문제]

- 전자 설명서는 일본어 그대로입니다.
- 플라자의 Miiverse 말풍선은 본체 글꼴로 나옵니다.


[글꼴]

한글은 「티머니 둥근바람」(티머니×윤디자인)으로 그렸습니다. 자세한 안내는 licenses 폴더를 보세요.
