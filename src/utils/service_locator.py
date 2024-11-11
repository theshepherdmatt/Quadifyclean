# src/utils/service_locator.py or a separate config validation module
import yaml
import logging

def load_config(config_path='config.yaml'):
    with open(config_path, 'r') as file:
        config = yaml.safe_load(file)
    
    # Example validation
    required_fields = {
        'pins': ['clk_pin', 'dt_pin', 'sw_pin', 'mcp23017_address'],
        'volumio': ['host', 'port', 'api_url'],
        'display': ['logo_path', 'loading_gif_path'],
        'fonts': ['clock_large', 'playback_large', 'playback_medium', 'menu_font'],
        'services': ['tidal', 'qobuz']
    }

    for section, keys in required_fields.items():
        if section not in config:
            logging.error(f"Missing '{section}' section in config.")
            raise ValueError(f"Missing '{section}' section in config.")
        for key in keys:
            if key not in config[section]:
                logging.error(f"Missing '{key}' in '{section}' section.")
                raise ValueError(f"Missing '{key}' in '{section}' section.")
    
    return config

