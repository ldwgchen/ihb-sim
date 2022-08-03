from utils import analyze_key_tuple_str


class Tree:

    def __init__(self):
        self.names = []
        self.bindings = {}

    def create_name(self, new_name: str) -> bool:
        if new_name in self.names:
            return False
        self.names.append(new_name)
        return True

    def update_binding(self, key_tuple: tuple, value: int) -> bool:
        for name in key_tuple:
            if name not in self.names:
                return False
        self.bindings.update({key_tuple: value})
        return True

    def remove_binding(self, key_tuple: tuple) -> bool:
        if key_tuple not in self.bindings:
            return False
        self.bindings.pop(key_tuple)

    def remove_name(self, name: str) -> bool:
        if name not in self.names:
            return False
        self.names.remove(name)
        scheduled_removal_key_tuples = []
        for key_tuple in self.bindings.keys():
            if name in key_tuple:
                scheduled_removal_key_tuples.append(key_tuple)
        for key_tuple in scheduled_removal_key_tuples:
            self.bindings.pop(key_tuple)
        return True


class Session:

    def __init__(self, init_tree: Tree):
        self.tree = init_tree
        self.state = {name: 0 for name in self.tree.names}

    def correct_state(self):
        state_names = list(self.state.keys())
        for name in state_names:
            if name not in self.tree.names:
                self.state.pop(name)
        for name in self.tree.names:
            if name not in self.state.keys():
                self.state[name] = 0

    def get_names(self) -> list:
        return self.tree.names

    def get_bindings(self) -> dict:
        return self.tree.bindings

    def modify_tree(self, cmd: str) -> bool:
        tokens = cmd.split()
        if len(tokens) < 2:
            return False
        verb = tokens[0]
        nouns = tokens[1:]
        success = False
        if verb == 'create':
            # create a name
            if len(nouns) != 1:
                return False
            success = self.tree.create_name(nouns[0])
        elif verb == 'update':
            # update a binding
            if len(nouns) != 2:
                return False
            key_tuple_str = nouns[0]
            value_str = nouns[1]
            test_value_str = value_str
            if test_value_str[0] == '-':
                test_value_str = test_value_str[1:]
            if key_tuple_str[0] != '(' or key_tuple_str[-1] != ')' or not test_value_str.isnumeric():
                return False
            key_tuple = analyze_key_tuple_str(key_tuple_str)
            value = int(value_str)
            success = self.tree.update_binding(key_tuple, value)
        elif verb == 'remove':
            # remove a name/binding
            if len(nouns) != 1:
                return False
            noun = nouns[0]
            if noun[0] == '(' and noun[-1] == ')':
                key_tuple = analyze_key_tuple_str(noun)
                success = self.tree.remove_binding(key_tuple)
            else:
                success = self.tree.remove_name(noun)
        self.correct_state()
        return success

    def restore(self):
        to_restore = []
        # find negatives
        for name in self.state.keys():
            if self.state[name] < 0:
                to_restore.append(name)

        # find loners and bottoms
        # a loner is: not in upstream_names and not in downstream_names
        # a bottom is: in downstream_names but not in upstream_names
        # hence: not in upstream_names -> either a loner or a bottom
        upstream_names = []
        for key_tuple in self.tree.bindings:
            upstream_names.append(key_tuple[0])
        for name in self.tree.names:
            if name not in upstream_names:
                to_restore.append(name)

        for name in to_restore:
            self.state[name] = 0

    def fire(self):
        # fire through bindings
        actions = {}
        to_tire = []
        for key_tuple in self.tree.bindings.keys():
            upstream = key_tuple[0]
            downstream = key_tuple[1]
            value = self.tree.bindings[key_tuple]
            if self.state[upstream] > 0:
                to_tire.append(upstream)
                if downstream in actions.keys():
                    actions[downstream] += value
                else:
                    actions[downstream] = value
        for tired in to_tire:
            self.state[tired] = 0
        for actionable in actions.keys():
            self.state[actionable] += actions[actionable]
