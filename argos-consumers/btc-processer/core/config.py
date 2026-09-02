import yaml
import os
from dotenv import load_dotenv

class ConfigLoader:
    def __init__(self):
        load_dotenv()
        environment = os.getenv('ENV_PROFILE', 'default')
        config_file = f'config_{environment}.yaml'
        config_path = os.path.join(os.getcwd(), config_file)

        if not os.path.exists(config_path):
            config_file = 'config.yaml'
            config_path = os.path.join(os.getcwd(), config_file)

        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Neither config_{environment}.yaml nor config.yaml exists.")

        with open(config_path, 'r') as file:
            self.config = yaml.safe_load(file)

    def get(self, key, default=None):
        keys = key.split(".")
        value = self.config
        for k in keys:
            value = value.get(k, default)
            if value is default:
                break
        return value
