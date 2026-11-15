import math
from datetime import datetime

from kivy.app import App
from kivy.core.window import Window
from kivy.graphics import Color, RoundedRectangle
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget

BG_COLOR      = (0.12, 0.13, 0.16, 1)
CARD_COLOR    = (0.18, 0.20, 0.24, 1)
TITLE_COLOR   = (1, 1, 1, 1)
TEXT_COLOR    = (0.95, 0.95, 0.95, 1)
HINT_COLOR    = (0.75, 0.78, 0.82, 1)

BTN_PRIMARY   = (0.20, 0.55, 0.90, 1)
BTN_ACTION    = (0.20, 0.65, 0.40, 1)
BTN_SAVE      = (0.25, 0.55, 0.85, 1)
BTN_BACK      = (0.75, 0.30, 0.30, 1)

PADDING       = 20
SPACING       = 12
BTN_HEIGHT    = 48
TITLE_HEIGHT  = 44
ROW_HEIGHT    = 44
FONT_TITLE    = '22sp'
FONT_LABEL    = '15sp'
FONT_RESULT   = '14sp'

TAB_PUE_CU = {
    1.5: 19, 2.5: 27, 4: 38, 6: 46, 10: 70,
    16: 90, 25: 115, 35: 140, 50: 175,
}
TAB_PUE_AL = {
    2.5: 21, 4: 29, 6: 38, 10: 55,
    16: 70, 25: 90, 35: 110, 50: 135,
}

STANDARDS = (1.5, 2.5, 4, 6, 10, 16, 25, 35, 50)
BREAKERS  = (6, 10, 16, 20, 25, 32, 40, 50, 63)

MATERIALS = {
    'Медь (γ=56)': 56,
    'Алюминий (γ=34)': 34,
}


def pick_section_pue(current, material_key):
    table = TAB_PUE_CU if material_key.startswith('Медь') else TAB_PUE_AL
    for section in STANDARDS:
        if section in table and table[section] >= current:
            return section, table[section]
    return None, None


def pick_section_drop(current, length, voltage, gamma, phase):
    k = 2 if phase == '1ф' else 1.732
    s_calc = (k * current * length) / (gamma * 0.05 * voltage)
    for section in STANDARDS:
        if section >= s_calc:
            return section, s_calc
    return STANDARDS[-1], s_calc


def save_result(screen_name, text):
    try:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open('calc_results.txt', 'a', encoding='utf-8') as f:
            f.write(f"\n{'=' * 50}\n")
            f.write(f"[{timestamp}] {screen_name}\n")
            f.write(f"{'-' * 50}\n")
            f.write(text + "\n")
        return True
    except Exception as e:
        print(f'Ошибка сохранения: {e}')
        return False


def make_button(text, color, on_press):
    btn = Button(
        text=text,
        font_size='16sp',
        size_hint=(1, None),
        height=BTN_HEIGHT,
        background_normal='',
        background_down='',
        background_color=color,
        color=(1, 1, 1, 1),
    )
    btn.bind(on_press=on_press)
    return btn


def make_title(text):
    return Label(
        text=text,
        font_size=FONT_TITLE,
        bold=True,
        color=TITLE_COLOR,
        size_hint=(1, None),
        height=TITLE_HEIGHT,
    )


def make_field(default, filt='float'):
    return TextInput(
        text=str(default),
        multiline=False,
        input_filter=filt,
        font_size=FONT_LABEL,
        size_hint=(1, None),
        height=ROW_HEIGHT,
    )


def make_result_box(height):
    box = BoxLayout(size_hint=(1, None), height=height, padding=10)
    with box.canvas.before:
        Color(*CARD_COLOR)
        box._rect = RoundedRectangle(pos=box.pos, size=box.size, radius=[8])
    box.bind(
        pos=lambda *_: setattr(box._rect, 'pos', box.pos),
        size=lambda *_: setattr(box._rect, 'size', box.size),
    )
    label = Label(
        text='Результат появится здесь',
        font_size=FONT_RESULT,
        halign='left',
        valign='top',
        color=TEXT_COLOR,
    )
    label.bind(size=label.setter('text_size'))
    box.add_widget(label)
    return box, label


def make_screen_scroll():
    scroll = ScrollView()
    layout = BoxLayout(
        orientation='vertical',
        padding=PADDING,
        spacing=SPACING,
        size_hint_y=None,
    )
    layout.bind(minimum_height=layout.setter('height'))
    scroll.add_widget(layout)
    return scroll, layout


def build_grid(rows):

    grid = GridLayout(
        cols=2,
        spacing=SPACING,
        size_hint=(1, None),
        height=len(rows) * ROW_HEIGHT + (len(rows) - 1) * SPACING,
        row_default_height=ROW_HEIGHT,
        row_force_default=True,
        col_default_width=180,
        col_force_default=True,
    )

    for label_text, widget in rows:
        lbl = Label(
            text=label_text,
            font_size=FONT_LABEL,
            color=TEXT_COLOR,
            halign='right',
            valign='middle',
            size_hint_y=None,
            height=ROW_HEIGHT,
        )
        lbl.bind(size=lbl.setter('text_size'))

        grid.add_widget(lbl)
        grid.add_widget(widget)

    return grid

class MenuScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=30, spacing=18)
        layout.add_widget(Label(
            text='Калькулятор электрика',
            font_size='24sp', bold=True,
            color=TITLE_COLOR,
            size_hint=(1, 0.25),
        ))

        for text, name in (
            ('Сечение кабеля', 'section'),
            ('Падение напряжения', 'drop'),
            ('Автомат / Ток КЗ', 'breaker'),
            ('Произвольный расчёт', 'custom'),
        ):
            layout.add_widget(make_button(
                text, BTN_PRIMARY,
                lambda _i, n=name: self.open_screen(n),
            ))

        layout.add_widget(Widget())
        self.add_widget(layout)

    def open_screen(self, name):
        self.manager.current = name


class SectionCalcScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        scroll, layout = make_screen_scroll()
        layout.add_widget(make_title('Расчёт сечения кабеля'))

        self.current_input  = make_field(16)
        self.voltage_input  = make_field(220)
        self.length_input   = make_field(10)

        self.material_spinner = Spinner(
            text='Медь (γ=56)',
            values=('Медь (γ=56)', 'Алюминий (γ=34)'),
            font_size=FONT_LABEL,
            size_hint=(1, None),
            height=ROW_HEIGHT,
        )
        self.phase_spinner = Spinner(
            text='1ф', values=('1ф', '3ф'),
            font_size=FONT_LABEL,
            size_hint=(1, None),
            height=ROW_HEIGHT,
        )

        layout.add_widget(build_grid([
            ('Ток (А):',            self.current_input),
            ('Напряжение (В):',     self.voltage_input),
            ('Длина линии (м):',    self.length_input),
            ('Материал:',           self.material_spinner),
            ('Сеть:',               self.phase_spinner),
        ]))

        layout.add_widget(make_button('Рассчитать', BTN_ACTION, self.calculate))
        result_box, self.result_label = make_result_box(260)
        layout.add_widget(result_box)
        layout.add_widget(make_button('Сохранить результат', BTN_SAVE, self.save_to_file))
        layout.add_widget(make_button('Назад в меню', BTN_BACK, self.go_back))

        self.add_widget(scroll)

    def save_to_file(self, instance):
        if self.result_label.text and not self.result_label.text.startswith('Результат появится'):
            if save_result('Расчёт сечения кабеля', self.result_label.text):
                self.result_label.text += '\n\nСохранено в calc_results.txt'
            else:
                self.result_label.text += '\n\nОшибка сохранения'
        else:
            self.result_label.text = 'Сначала выполните расчёт!'

    def calculate(self, instance):
        try:
            I = float(self.current_input.text)
            U = float(self.voltage_input.text)
            L = float(self.length_input.text)
            material = self.material_spinner.text
            gamma = MATERIALS[material]
            phase = self.phase_spinner.text

            s_pue, i_allow = pick_section_pue(I, material)
            s_drop, s_raw = pick_section_drop(I, L, U, gamma, phase)

            candidates = [x for x in (s_pue, s_drop) if x is not None]
            if not candidates:
                self.result_label.text = 'Сечение вне таблицы ПУЭ — проверьте данные.'
                return
            s_final = max(candidates)

            k = 2 if phase == '1ф' else 1.732
            dU = (k * I * L) / (gamma * s_final)
            percent = dU / U * 100

            self.result_label.text = (
                f"Материал: {material}, сеть: {phase}\n"
                f"Ток нагрузки: {I:.1f} А, длина: {L:.1f} м\n\n"
                f"— По ПУЭ (нагрев):\n"
                f"  S = {s_pue if s_pue else '—'} мм², "
                f"Iдоп = {i_allow if i_allow else '—'} А\n\n"
                f"— По потере напряжения (5%):\n"
                f"  Sрасe = {s_raw:.2f} мм² → {s_drop} мм²\n"
                f"  Формула: S = {k:.3f}·I·L / (γ·ΔU·U)\n\n"
                f"— ИТОГО: {s_final} мм² ({material.split()})\n"
                f"  ΔU = {dU:.2f} В ({percent:.1f}%) — норма 5%"
            )
        except Exception as e:
            self.result_label.text = f'Ошибка: {e}'

    def go_back(self, instance):
        self.manager.current = 'menu'


class VoltageDropScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        scroll, layout = make_screen_scroll()
        layout.add_widget(make_title('Расчёт падения напряжения'))

        self.current_input  = make_field(16)
        self.section_input  = make_field(2.5)
        self.length_input   = make_field(20)
        self.voltage_input  = make_field(220)

        self.material_spinner = Spinner(
            text='Медь (γ=56)',
            values=('Медь (γ=56)', 'Алюминий (γ=34)'),
            font_size=FONT_LABEL,
            size_hint=(1, None),
            height=ROW_HEIGHT,
        )
        self.phase_spinner = Spinner(
            text='1ф', values=('1ф', '3ф'),
            font_size=FONT_LABEL,
            size_hint=(1, None),
            height=ROW_HEIGHT,
        )

        layout.add_widget(build_grid([
            ('Ток (А):',          self.current_input),
            ('Сечение (мм²):',    self.section_input),
            ('Длина (м):',        self.length_input),
            ('Напряжение (В):',   self.voltage_input),
            ('Материал:',         self.material_spinner),
            ('Сеть:',             self.phase_spinner),
        ]))

        layout.add_widget(make_button('Рассчитать', BTN_ACTION, self.calculate))
        result_box, self.result_label = make_result_box(220)
        layout.add_widget(result_box)
        layout.add_widget(make_button('Сохранить результат', BTN_SAVE, self.save_to_file))
        layout.add_widget(make_button('Назад в меню', BTN_BACK, self.go_back))

        self.add_widget(scroll)

    def save_to_file(self, instance):
        if self.result_label.text and not self.result_label.text.startswith('Результат появится'):
            if save_result('Падение напряжения', self.result_label.text):
                self.result_label.text += '\n\nСохранено в calc_results.txt'
            else:
                self.result_label.text += '\n\nОшибка сохранения'
        else:
            self.result_label.text = 'Сначала выполните расчёт!'

    def calculate(self, instance):
        try:
            I = float(self.current_input.text)
            S = float(self.section_input.text)
            L = float(self.length_input.text)
            U = float(self.voltage_input.text)
            gamma = MATERIALS[self.material_spinner.text]
            phase = self.phase_spinner.text
            k = 2 if phase == '1ф' else 1.732

            dU = (k * I * L) / (gamma * S)
            percent = dU / U * 100
            status = 'OK' if percent <= 5.0 else 'ПРЕВЫШЕНИЕ'

            self.result_label.text = (
                f"Формула: ΔU = {k:.3f}·I·L / (γ·S)\n"
                f"ΔU = {dU:.2f} В ({percent:.1f}%)\n"
                f"Норма: < 3% (освещение) / < 5% (силовые)\n"
                f"Статус: {status}\n"
                f"γ = {gamma} м/(Ом·мм²), сеть {phase}"
            )
        except Exception as e:
            self.result_label.text = f'Ошибка: {e}'

    def go_back(self, instance):
        self.manager.current = 'menu'


class BreakerScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        scroll, layout = make_screen_scroll()
        layout.add_widget(make_title('Выбор автомата / Ток КЗ'))

        self.power_input   = make_field(3500)
        self.voltage_input = make_field(220)
        self.res_input     = make_field(0.5)

        self.char_spinner  = Spinner(
            text='C (×5..10)',
            values=('B (×3..5)', 'C (×5..10)', 'D (×10..20)'),
            font_size=FONT_LABEL,
            size_hint=(1, None),
            height=ROW_HEIGHT,
        )

        layout.add_widget(build_grid([
            ('Мощность (Вт):',              self.power_input),
            ('Напряжение (В):',             self.voltage_input),
            ('Сопротивление петли (Ом):',   self.res_input),
            ('Характеристика:',             self.char_spinner),
        ]))

        layout.add_widget(make_button('Рассчитать всё', BTN_ACTION, self.calculate))
        result_box, self.result_label = make_result_box(260)
        layout.add_widget(result_box)
        layout.add_widget(make_button('Сохранить результат', BTN_SAVE, self.save_to_file))
        layout.add_widget(make_button('Назад в меню', BTN_BACK, self.go_back))

        self.add_widget(scroll)

    def save_to_file(self, instance):
        if self.result_label.text and not self.result_label.text.startswith('Результат появится'):
            if save_result('Выбор автомата / Ток КЗ', self.result_label.text):
                self.result_label.text += '\n\nСохранено в calc_results.txt'
            else:
                self.result_label.text += '\n\nОшибка сохранения'
        else:
            self.result_label.text = 'Сначала выполните расчёт!'

    def calculate(self, instance):
        try:
            P = float(self.power_input.text)
            U = float(self.voltage_input.text)
            Z = float(self.res_input.text)
            char = self.char_spinner.text

            if Z <= 0:
                self.result_label.text = 'Сопротивление должно быть > 0!'
                return

            I_load = P / U
            rec_breaker = BREAKERS[-1]
            for b in BREAKERS:
                if b >= I_load * 1.1:
                    rec_breaker = b
                    break

            I_kz = U / Z

            if char.startswith('B'):
                k_mult = 5
            elif char.startswith('C'):
                k_mult = 10
            else:
                k_mult = 20

            i_trip_min = k_mult * rec_breaker
            kz_ok = I_kz >= i_trip_min
            kz_ok_3 = I_kz >= 3 * rec_breaker

            self.result_label.text = (
                f"Ток нагрузки: {I_load:.1f} А\n"
                f"Автомат: {rec_breaker} А ({char.split()})\n"
                f"Ток КЗ: {I_kz:.1f} А\n\n"
                f"Проверка по КЗ:\n"
                f"  Iкз ≥ {k_mult}·Iном = {i_trip_min:.0f} А → "
                f"{'OK' if kz_ok else 'НЕ ОК'}\n"
                f"  Iкз ≥ 3·Iном = {3 * rec_breaker} А → "
                f"{'OK' if kz_ok_3 else 'НЕ ОК'}\n\n"
                f"Формулы: Iн=P/U; Iкз=U/Z; Iн=1.1·Iнагр"
            )
        except Exception as e:
            self.result_label.text = f'Ошибка: {e}'

    def go_back(self, instance):
        self.manager.current = 'menu'


class CustomCalcScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        scroll, layout = make_screen_scroll()

        layout.add_widget(make_title('Произвольный расчёт'))
        layout.add_widget(Label(
            text='Переменные: a, b, c | Знаки: + - * / ** sqrt()',
            font_size='13sp',
            color=HINT_COLOR,
            size_hint=(1, None), height=30,
        ))

        self.formula_input = TextInput(
            text='a / (b * c)', multiline=False,
            font_size=FONT_LABEL,
            size_hint=(1, None),
            height=ROW_HEIGHT,
        )
        self.a_input = make_field(2200)
        self.b_input = make_field(220)
        self.c_input = make_field(0.95)

        layout.add_widget(build_grid([
            ('Формула:',        self.formula_input),
            ('Переменная a:',   self.a_input),
            ('Переменная b:',   self.b_input),
            ('Переменная c:',   self.c_input),
        ]))

        layout.add_widget(make_button('Рассчитать формулу', BTN_ACTION, self.calculate))
        result_box, self.result_label = make_result_box(140)
        layout.add_widget(result_box)
        layout.add_widget(make_button('Сохранить результат', BTN_SAVE, self.save_to_file))
        layout.add_widget(make_button('Назад в меню', BTN_BACK, self.go_back))

        self.add_widget(scroll)

    def save_to_file(self, instance):
        if self.result_label.text and not self.result_label.text.startswith('Результат появится'):
            if save_result('Произвольный расчёт', self.result_label.text):
                self.result_label.text += '\n\nСохранено в calc_results.txt'
            else:
                self.result_label.text += '\n\nОшибка сохранения'
        else:
            self.result_label.text = 'Сначала выполните расчёт!'

    def calculate(self, instance):
        try:
            a = float(self.a_input.text)
            b = float(self.b_input.text)
            c = float(self.c_input.text)
            expr = self.formula_input.text

            allowed = {
                'a': a, 'b': b, 'c': c,
                'sqrt': math.sqrt, 'pi': math.pi,
            }
            res = eval(expr, {"__builtins__": None}, allowed)

            self.result_label.text = f"Формула: {expr}\nРезультат: {res:.4f}"
        except Exception as e:
            self.result_label.text = f'Ошибка в формуле: {e}'

    def go_back(self, instance):
        self.manager.current = 'menu'


class ElectroCalcApp(App):
    def build(self):
        Window.clearcolor = BG_COLOR
        sm = ScreenManager()
        sm.add_widget(MenuScreen(name='menu'))
        sm.add_widget(SectionCalcScreen(name='section'))
        sm.add_widget(VoltageDropScreen(name='drop'))
        sm.add_widget(BreakerScreen(name='breaker'))
        sm.add_widget(CustomCalcScreen(name='custom'))
        return sm


if __name__ == '__main__':
    ElectroCalcApp().run()
