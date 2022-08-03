from kivy.config import Config
Config.set('input', 'mouse', 'mouse,multitouch_on_demand')
Config.set('graphics', 'resizable', True)

from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.clock import Clock
from base import Session, Tree
from utils import *
from math import sqrt

# Avoid using size/pos in a layout. They won't work as expected. Use size_hint/pos_hint instead.


mode = 'normal'
switch = 'description'


class Node(Label):

    def is_touched(self, touch) -> bool:
        hshx = self.size_hint_x/2
        hshy = self.size_hint_y/2
        center_x = self.pos_hint['x'] + hshx
        center_y = self.pos_hint['y'] + hshy
        touch_hint = pos_to_hint(touch.pos, self.parent)
        transformed_touch_x = touch_hint['x']-center_x
        transformed_touch_y = touch_hint['y']-center_y
        lhs = ((transformed_touch_x**2)/(hshx**2) + (transformed_touch_y**2)/(hshy**2))
        return lhs <= 1

    def move_to(self, new_pos_hint: dict):
        # Do reassign pos_hint to the object instead of changing its values.
        # That is because simply updating the dict won't trigger the event dispatcher.
        self.pos_hint = new_pos_hint

    def resize_to(self, new_size_hint: list):
        self.size_hint = new_size_hint

    def on_touch_down(self, touch):
        set_label = self.parent.parent.ids['mnp'].set_label
        # only called in normal mode
        if touch.button == 'right' and self.is_touched(touch):
            self.parent.session.state[self.id] += 1
            set_label(f'Node <{self.id}> incremented.')
        elif self.parent.focus == self.id:
            if touch.is_double_tap:
                self.parent.free_focus()
                set_label('Selection freed.')
            else:
                transformed_touch_hint_x = pos_to_hint(touch.pos, self.parent)['x'] - self.size_hint_x / 2
                transformed_touch_hint_y = pos_to_hint(touch.pos, self.parent)['y'] - self.size_hint_y / 2
                self.move_to({'x': transformed_touch_hint_x, 'y': transformed_touch_hint_y})
                set_label(f'Moved Node <{self.id}>.')
        elif self.parent.focus == '' and self.is_touched(touch):
            self.parent.set_focus(self.id)
            set_label(f'Selected Node <{self.id}>.')


class Arrow(Label):

    def is_touched(self, touch) -> bool:
        if not self.collide_point(touch.x, touch.y):
            return False
        start = self.points_wrapper[:2]
        end = self.points_wrapper[2:4]
        point1 = self.points_wrapper[4:6]
        point2 = self.points_wrapper[6:8]
        test_point = [(start[0]+end[0])/2, (start[1]+end[1])/2]
        tx = test_point[0]
        ty = test_point[1]
        if start[0]-end[0] == 0:
            pass
        k = (start[1]-end[1])/(start[0]-end[0])
        bb = [point[1] - k * point[0] for point in [point1, point2]]
        for b in bb:
            if k*tx+b > ty and k*touch.x+b < touch.y:
                return False
            elif k*tx+b < ty and k*touch.x+b > touch.y:
                return False
        if k == 0:
            for terminal in [start, end]:
                if test_point[0] > terminal[0] > touch.x:
                    return False
                elif test_point[0] < terminal[0] < touch.x:
                    return False
        else:
            sk = -1/k
            bb_sk = [point[1]-sk*point[0] for point in [start, end]]
            for b in bb_sk:
                if sk * tx + b > ty and sk * touch.x + b < touch.y:
                    return False
                elif sk * tx + b < ty and sk * touch.x + b > touch.y:
                    return False
        return True

    def on_touch_down(self, touch):
        set_label = self.parent.parent.ids['mnp'].set_label
        tidy_id = key_tuple_to_str(self.id)
        # only called in normal mode
        if self.is_touched(touch):
            if self.parent.focus == self.id:
                if touch.is_double_tap:
                    self.parent.free_focus()
                    set_label('Selection freed.')
                else:
                    set_label(f'Binding: <{tidy_id}>\nValue: {self.value}')
            elif self.parent.focus == '':
                self.parent.set_focus(self.id)
                set_label(f'Selected Binding <{tidy_id}>.')


class AlignedLabel(Label):
    pass


class MainPanel(FloatLayout):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.focus = ''
        self.round = 0
        self.run_event = None
        self.cache = {}
        self.mode_value_dict = {'plus_one': 1, 'plus_two': 2, 'minus_one': -1, 'minus_two': -2}
        self.session = Session(Tree())
        self.map_nodes(self.session.get_names())
        self.refresh_arrows()

    def set_focus(self, widget_id: str) -> bool:
        child_dict = self.get_child_dict()
        if widget_id in child_dict.keys():
            self.focus = widget_id
            widget = child_dict[widget_id]
            widget.color_wrapper = widget.color_dict['focus']
            return True
        else:
            return False

    def free_focus(self):
        child_dict = self.get_child_dict()
        if self.focus in child_dict.keys():
            widget = child_dict[self.focus]
            if isinstance(widget, Arrow):
                value = self.session.get_bindings()[widget.id]
                widget.color_wrapper = widget.color_dict[value]
            elif isinstance(widget, Node):
                widget.color_wrapper = widget.color_dict['default']
        self.focus = ''

    def map_nodes(self, names: list) -> bool:
        if not names:
            return False
        i = 0
        for name in names:
            new_node = Node(pos_hint={'x': (i % 10)*0.1, 'y': (i//10)*0.1}, size_hint=[0.1, 0.1])
            new_node.id = name
            new_node.color_wrapper = new_node.color_dict['default']
            self.add_widget(new_node)
            i += 1
        return True

    def correct_nodes(self) -> bool:
        node_list = self.get_nodes()
        child_dict = self.get_child_dict()
        if not node_list:
            return False
        current_names = [node.id for node in node_list]
        for name in current_names:
            if name not in self.session.get_names():
                self.remove_widget(child_dict[name])
        to_map = []
        for name in self.session.get_names():
            if name not in current_names:
                to_map.append(name)
        self.map_nodes(to_map)
        self.refresh_arrows()
        return True

    def refresh_arrows(self) -> bool:
        self.clear_widgets(self.get_arrows())
        if not self.session.get_bindings():
            return False
        for key_tuple, value in self.session.get_bindings().items():
            child_dict = self.get_child_dict()
            start_node = child_dict[key_tuple[0]]
            end_node = child_dict[key_tuple[1]]

            # transform start/end pos_hint and convert to pos
            transformed_pos = []
            for node in [start_node, end_node]:
                dummy_hint = {'x': node.pos_hint['x'] + node.size_hint_x/2, 'y': node.pos_hint['y'] + node.size_hint_y/2}
                transformed_pos.append(dummy_hint)
            transformed_pos = [hint_to_pos(dummy_hint, self) for dummy_hint in transformed_pos]
            start = transformed_pos[0]
            end = transformed_pos[1]

            new_arrow = Arrow()
            new_arrow.id = key_tuple
            new_arrow.value = value

            # draw points and set pos_hint, size_hint
            new_arrow.points_wrapper = infer_points(start, end)
            pos = [min(start[0], end[0]), min(start[1], end[1])]
            size_hint = [abs(start[0]-end[0])/self.width, abs(start[1]-end[1])/self.height]
            new_arrow.pos_hint = pos_to_hint(pos, self)
            new_arrow.size_hint = size_hint

            # set color
            new_arrow.color_wrapper = new_arrow.color_dict[value]
            if self.focus == new_arrow.id:
                new_arrow.color_wrapper = new_arrow.color_dict['focus']

            self.add_widget(new_arrow)
        return True

    def generate_id(self) -> str:
        existing_names = self.session.get_names()
        id_number = 0
        while True:
            id_str = 'ud' + str(id_number)
            if id_str not in existing_names:
                return id_str
            id_number += 1

    def get_nodes(self) -> list:
        return [child for child in self.children if isinstance(child, Node)]

    def get_arrows(self) -> list:
        return [child for child in self.children if isinstance(child, Arrow)]

    def get_child_dict(self) -> dict:
        return {child.id: child for child in self.children}

    def correct_scores(self):
        node_list = self.get_nodes()
        if node_list:
            for node in node_list:
                name = node.id
                node.text = str(self.session.state[name])

    def exe_round(self):
        set_label = self.parent.ids['mnp'].set_label
        set_label(f'Executing Round <{self.round}> ...')
        self.session.restore()
        self.session.fire()
        self.correct_scores()
        self.round += 1

    def toggle_run(self):
        set_label = self.parent.ids['mnp'].set_label
        if self.run_event is None:
            self.run_event = Clock.schedule_interval(lambda dt: self.exe_round(), 3)
            set_label('<session run started>')
            self.parent.ids['rp'].ids['run'].text = 'RUNNING'
        else:
            self.run_event.cancel()
            set_label('<session run stopped>')
            self.run_event = None
            self.round = 0
            self.parent.ids['rp'].ids['run'].text = 'RUN'

    def clear_modal(self, exempt: str = None):
        if self.focus != '' and exempt != 'normal':
            self.free_focus()
        if 'upstream' in self.cache and exempt not in self.mode_value_dict.keys():
            upstream = self.cache['upstream']
            child_dict = self.get_child_dict()
            if upstream in child_dict:
                upstream_as_node = child_dict[upstream]
                upstream_as_node.color_wrapper = upstream_as_node.color_dict['default']
            self.cache.clear()

    def nuke(self):
        if self.run_event is not None:
            self.toggle_run()
        self.clear_modal()
        self.clear_widgets()
        empty_tree = Tree()
        self.session = Session(empty_tree)

    def on_touch_down(self, touch):
        if not self.collide_point(touch.x, touch.y):
            return False
        set_label = self.parent.ids['mnp'].set_label
        global mode
        self.clear_modal(exempt=mode)
        set_label(f'Mode: {mode}.')
        if mode == 'normal':
            for node in self.get_nodes():
                node.on_touch_down(touch)
            if True not in [node.is_touched(touch) for node in self.get_nodes()]:
                for arrow in self.get_arrows():
                    arrow.on_touch_down(touch)
        elif mode == 'point':
            new_id = self.generate_id()
            self.session.modify_tree(f'create {new_id}')
            new_node = Node(size_hint=[0.1, 0.1])
            new_node.id = new_id
            new_node.color_wrapper = new_node.color_dict['default']
            transformed_touch_hint_x = pos_to_hint(touch.pos, self)['x'] - new_node.size_hint_x/2
            transformed_touch_hint_y = pos_to_hint(touch.pos, self)['y'] - new_node.size_hint_y/2
            new_node.pos_hint = {'x': transformed_touch_hint_x, 'y': transformed_touch_hint_y}
            self.add_widget(new_node)
            set_label(f'Created new Node <{new_id}>.')
        elif mode == 'remove':
            to_remove = []
            for node in self.get_nodes():
                if node.is_touched(touch):
                    to_remove.append(node.id)
            for arrow in self.get_arrows():
                if arrow.is_touched(touch):
                    to_remove.append(arrow.id)
            death_report = []
            for widget_id in to_remove:
                if isinstance(widget_id, tuple):
                    widget_id = key_tuple_to_str(widget_id)
                self.session.modify_tree(f'remove {widget_id}')
                death_report.append(widget_id)
            child_dict = self.get_child_dict()
            to_remove = [child_dict[widget_id] for widget_id in to_remove]
            self.clear_widgets(to_remove)
            death_report = ' '.join(death_report)
            if death_report != '':
                set_label(f'Removed {death_report}.')
        elif mode in self.mode_value_dict.keys():
            child_dict = self.get_child_dict()
            value = self.mode_value_dict[mode]
            if 'upstream' not in self.cache:
                upstream = ''
                for node in self.get_nodes():
                    if node.is_touched(touch):
                        upstream = node.id
                if upstream != '':
                    set_label(f'From <{upstream}> to <...>?')
                    self.cache['upstream'] = upstream
                    upstream_as_node = child_dict[upstream]
                    upstream_as_node.color_wrapper = upstream_as_node.color_dict['upstream_sel']
            else:
                upstream = self.cache['upstream']
                downstream = ''
                for node in self.get_nodes():
                    if node.id != upstream and node.is_touched(touch):
                        downstream = node.id
                key_tuple = (upstream, downstream)
                if downstream != '' and key_tuple not in self.session.get_bindings():
                    self.session.modify_tree(f'update {key_tuple_to_str(key_tuple)} {value}')
                    set_label(f'Created a binding from <{upstream}> to <{downstream}> (value={value}).')
                else:
                    set_label('Cancelled: Please choose a valid downstream node!')
                self.cache.clear()
                upstream_as_node = child_dict[upstream]
                upstream_as_node.color_wrapper = upstream_as_node.color_dict['default']
        self.correct_scores()
        self.refresh_arrows()


class RightPanel(FloatLayout):

    def sel_mode(self, sel: str):
        global mode
        mode = sel
        mode_text_dict = {'point': 'POINT', 'remove': 'REMOVE',
                          'plus_one': '+1', 'plus_two': '+2', 'minus_one': '-1', 'minus_two': '-2'}
        if sel != 'normal':
            self.ids[sel].text = mode_text_dict[sel] + '(SEL)'
        for mode_tag in mode_text_dict.keys():
            if mode_tag != mode:
                self.ids[mode_tag].text = mode_text_dict[mode_tag].upper()

    def point_press(self):
        global mode
        if mode == 'point':
            self.sel_mode('normal')
        else:
            self.sel_mode('point')

    def plus_one_press(self):
        global mode
        if mode == 'plus_one':
            self.sel_mode('normal')
        else:
            self.sel_mode('plus_one')

    def plus_two_press(self):
        global mode
        if mode == 'plus_two':
            self.sel_mode('normal')
        else:
            self.sel_mode('plus_two')

    def minus_one_press(self):
        global mode
        if mode == 'minus_one':
            self.sel_mode('normal')
        else:
            self.sel_mode('minus_one')

    def minus_two_press(self):
        global mode
        if mode == 'minus_two':
            self.sel_mode('normal')
        else:
            self.sel_mode('minus_two')

    def remove_press(self):
        global mode
        if mode == 'remove':
            self.sel_mode('normal')
        else:
            self.sel_mode('remove')

    def run_press(self):
        self.parent.ids['mp'].toggle_run()

    def mini_press(self):
        self.parent.ids['mnp'].switch()


class HelpLabel(AlignedLabel):
    pass


class MiniPanel(FloatLayout):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # specify aesthetics of widgets
        self.label = AlignedLabel()
        self.label.size_hint = [1, 1]
        self.label.pos_hint = {'x': 0, 'y': 0}
        self.textbox = TextInput()
        self.textbox.size_hint = [1, 0.9]
        self.textbox.pos_hint = {'x': 0, 'y': 0.1}
        self.interpret = Button()
        self.interpret.text = 'INTERPRET'
        self.interpret.size_hint = [1, 0.1]
        self.interpret.pos_hint = {'x': 0, 'y': 0}
        self.interpret.bind(on_press=lambda x: self.run_interpret())
        # global variable switch is initialized to 'description' at the very start
        self.add_widget(self.label)

    def set_label(self, text: str):
        self.label.text = text

    def run_interpret(self):
        block = self.textbox.text
        lines = block.splitlines()
        line_feedback = []
        for line in lines:
            feedback = self.cmd_porter(line)
            line_feedback.append(feedback)
        lines = [str(line_feedback[i])+'/'+line for i, line in enumerate(lines)]
        self.textbox.text = '\n'.join(lines)

    def cmd_porter(self, cmd: str) -> bool:
        modify_tree_verbs = ['create', 'update', 'remove']
        tokens = cmd.split()
        if len(tokens) == 0:
            return False
        verb = tokens[0]
        success = False
        if verb in modify_tree_verbs:
            success = self.parent.ids['mp'].session.modify_tree(cmd)
            self.parent.ids['mp'].correct_nodes()
        elif verb == 'nuke':
            self.parent.ids['mp'].nuke()
            success = True
        return success

    def switch(self):
        global switch
        if switch == 'description':
            self.remove_widget(self.label)
            self.add_widget(self.textbox)
            self.add_widget(self.interpret)
            switch = 'script'
        elif switch == 'script':
            self.remove_widget(self.textbox)
            self.remove_widget(self.interpret)
            self.add_widget(self.label)
            switch = 'description'


class MainScreenLayout(FloatLayout):
    pass


class VisApp(App):

    def build(self):
        self.title = 'Inhibition Simulator'
        layout = MainScreenLayout()
        return layout


if __name__ == '__main__':
    VisApp().run()
