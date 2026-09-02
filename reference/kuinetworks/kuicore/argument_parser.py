import argparse

class ArgumentParser:
    def __init__(self, description, flags):
        self.parser = argparse.ArgumentParser(description=description)
        self.add_arguments(flags)
        self.args = None

    def add_arguments(self, flags):
        for flag in flags:
            name = '--' + flag["name"]
            kwargs = {
                'type': self.get_type(flag),
                'required': 'required' in flag and flag['required'],
                'help': flag['help']
            }
            if 'choices' in flag:
                kwargs['choices'] = flag['choices']
            if 'default' in flag:
                kwargs['default'] = flag['default']
            self.parser.add_argument(name, **kwargs)

    def get_type(self, flag):
        if 'type' in flag:
            if flag['type'] == 'int_range':
                return lambda x: self.int_range_type(x, flag['range'])
            return flag['type']
        return str

    def int_range_type(self, value, value_range):
        ivalue = int(value)
        if ivalue not in value_range and ivalue != -1:
            raise argparse.ArgumentTypeError(f"Value must be in {value_range} or -1")
        return ivalue
    def parse(self):
        self.args = self.parser.parse_args()
        return self.args
    
