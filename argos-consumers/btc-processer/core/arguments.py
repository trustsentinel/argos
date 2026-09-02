import argparse

def int_range(value):
    ivalue = int(value)
    if ivalue == -1 or ivalue in range(0, 11):
        return ivalue
    raise argparse.ArgumentTypeError(f"Invalid maxpeers value: {value}")
def setup(flags, description):
    parser = argparse.ArgumentParser(description=description)
    for flag in flags:
        kwargs = {
            'help': flag['help'],
            'default': flag.get('default')
        }
        if 'choices' in flag:
            kwargs['choices'] = flag['choices']
        if 'type' in flag:
            kwargs['type'] = flag['type']
        if 'required' in flag and flag['name'].startswith('--'):
            kwargs['required'] = flag['required']

        parser.add_argument(flag['name'], **kwargs)

    return parser.parse_args()
