import flet as ft

def main(page: ft.Page):
    page.title = "Stack Control Example"

    # Stack 위젯 생성
    stack_container = ft.Stack(
        [
            # 1. 배경 역할을 하는 파란색 컨테이너
            ft.Container(
                width=200,
                height=200,
                bgcolor=ft.colors.BLUE_200,
                border_radius=ft.border_radius.all(10)
            ),

            # 2. 왼쪽 상단에 위치하는 빨간색 원 (Container로 위치 지정)
            ft.Container(
                width=50,
                height=50,
                bgcolor=ft.colors.RED_ACCENT,
                border_radius=ft.border_radius.all(25), # 원 모양
                top=10,  # Stack 상단에서 10만큼 아래
                left=10   # Stack 왼쪽에서 10만큼 오른쪽
            ),

            # 3. 오른쪽 하단에 위치하는 텍스트
            ft.Text(
                "Stacked Text",
                color=ft.colors.WHITE,
                size=16,
                weight=ft.FontWeight.BOLD,
                bottom=20, # Stack 하단에서 20만큼 위
                right=20  # Stack 오른쪽에서 20만큼 왼쪽
            ),

            # 4. 중앙에 위치하는 아이콘 (left, top, width, height 조합)
            ft.Container(
                content=ft.Icon(name=ft.icons.FAVORITE, color=ft.colors.PINK, size=40),
                top=75,   # (200 - 50) / 2 = 75 (대략 중앙)
                left=75,  # (200 - 50) / 2 = 75 (대략 중앙)
                width=50,
                height=50,
                alignment=ft.alignment.center # 아이콘을 컨테이너 중앙에
            ),
        ],
        width=200, # Stack 자체의 크기
        height=200
    )

    page.add(stack_container)

ft.app(target=main)