import sys
sys.path.insert(0, '..')
import mbam

db = mbam.MMongo()
# updates the new template key
key = {"zero": 0, "inf": 1}
db.update_temp_key(key)

# adds these template keys if not already found in the DB -- used in examples.
templates = [
    {"key": (0, 1), "template": "1/inf_1", "label": "epsilon", "class": "ma"},
    {"key": (1, 0), "template": "zero_1", "label": "epsilon", "class": "ma"},
    {"key": (0, 2), "template": "inf_1/inf_2", "label": "inf1_over_inf_2", "class": "ma"},
    {"key": (0, 1), "template": "1/inf_1", "label": "epsilon", "class": "mm"},
    {"key": (1, 0), "template": "zero_1", "label": "epsilon", "class": "mm"},
    {"key": (0, 2), "template": "inf_1/inf_2", "label": "inf1_over_inf_2", "class": "mm"},
]

db.save_temps(templates)
