import os
from pw_config import ConfigWorkstation, ConfigDev, ConfigProd

match os.environ.get('FLASK_CONFIG_TYPE'):
    case 'dev':
        config = ConfigDev()
        print('- PersonalWebsite02/app_pacakge/config: Development')
    case 'prod':
        config = ConfigProd()
        print('- PersonalWebsite02/app_pacakge/config: Production')
    case _:
        config = ConfigWorkstation()
        print('- PersonalWebsite02/app_pacakge/config: Workstation')