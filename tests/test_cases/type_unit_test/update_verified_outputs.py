import sys
import os
import yaml
import json
sys.path.append('/Users/mikestorey/source/agile-learning-institute/mongodb_configurator/mongodb_configurator_api')

os.environ['TYPE_FOLDER'] = os.path.abspath('types')
from configurator.utils.config import Config
from configurator.services.type_services import Type

Config._instance = None
config = Config.get_instance()

json_dir = 'verified_output/json_schema'
bson_dir = 'verified_output/bson_schema'
files = [f for f in os.listdir('types') if f.endswith('.yaml')]

for file in files:
    t = Type(file)
    js = t.property.get_json_schema()
    bs = t.property.get_bson_schema()
    with open(os.path.join(json_dir, file), 'w') as f:
        yaml.dump(js, f, sort_keys=False)
    with open(os.path.join(bson_dir, file.replace('.yaml','.json')), 'w') as f:
        json.dump(bs, f, indent=2)
    print(f'Updated: {file}') 