COLORS = {
    "red": [1, 0, 0, 1],
    "green": [0, 1, 0, 1],
    "blue": [0, 0, 1, 1],
    "yellow": [1, 1, 0, 1],
    "purple": [1, 0, 1, 1],
    "cyan": [0, 1, 1, 1],
    "orange": [1, 0.5, 0, 1],
    "white": [1, 1, 1, 1],
    "gray": [0.5, 0.5, 0.5, 1],
    "black": [0, 0, 0, 1]
    }

MATERIALS = {
    'wood': {
        'roughness': 0.9,
        'metallic': 0.05,
        'specular': 0.5
    },
    'metal': {
        'roughness': 0.3,
        'metallic': 0.8,
        'specular': 0.5
    },
    'plastic': {
        'roughness': 0.5,
        'metallic': 0.1,
        'specular': 0.6
    },
    'glass': {
        'roughness': 0.02,
        'metallic': 0.0,
        'specular': 0.9,
        'transmission': 0.95, 
        'ior': 1.52  # Index of refraction for glass
    },
    'rubber': {
        'roughness': 0.8,
        'metallic': 0.0,
        'specular': 0.1
    },
    'ceramic': {
        'roughness': 0.1,
        'metallic': 0.0,
        'specular': 0.8
    }
}

SIZES = [
    [0.5, 0.5, 1.5],
    [1.5, 0.5, 0.5],
]