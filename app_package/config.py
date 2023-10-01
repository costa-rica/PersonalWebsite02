import os
from pw_config import ConfigLocal, ConfigDev, ConfigProd

match os.environ.get('FLASK_CONFIG_TYPE'):
    case 'dev':
        config = ConfigDev()
        print('- exFlaskBlueprintFrameworkStarterWithLogin/app_pacakge/config: Development')
    case 'prod':
        config = ConfigProd()
        print('- exFlaskBlueprintFrameworkStarterWithLogin/app_pacakge/config: Production')
    case _:
        config = ConfigLocal()
        print('- exFlaskBlueprintFrameworkStarterWithLogin/app_pacakge/config: Local')