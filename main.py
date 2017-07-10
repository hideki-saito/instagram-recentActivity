import os
import sys
import logging
import codecs
import json
import datetime

from config import *

try:
    from instagram_private_api import (
        Client, ClientError, ClientLoginError,
        ClientCookieExpiredError, ClientLoginRequiredError,
        __version__ as client_version)
except ImportError:
    import sys
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    from instagram_private_api import (
        Client, ClientError, ClientLoginError,
        ClientCookieExpiredError, ClientLoginRequiredError,
        __version__ as client_version)


def to_json(python_object):
    if isinstance(python_object, bytes):
        return {'__class__': 'bytes',
                '__value__': codecs.encode(python_object, 'base64').decode()}
    raise TypeError(repr(python_object) + ' is not JSON serializable')

def from_json(json_object):
    if '__class__' in json_object and json_object['__class__'] == 'bytes':
        return codecs.decode(json_object['__value__'].encode(), 'base64')
    return json_object

def onlogin_callback(api, new_settings_file):
    cache_settings = api.settings
    with open(new_settings_file, 'w') as outfile:
        json.dump(cache_settings, outfile, default=to_json)
        print('SAVED: {0!s}'.format(new_settings_file))

def getAttribute(obj):
    output = {}
    for key, value in obj.__dict__.items():
        if type(value) is list:
            output[key] = [getAttribute(item) for item in value]
        else:
            try:
                output[key] = getAttribute(value)
            except:
                output[key] = value

    return output

class Instagram_DataService():
    '''Main class of the project'''
    def __init__(self, username, password):
        '''
        :param username: Instagram Login Username
        :param password: Instagram Login Password
        '''
        device_id = None
        try:
            settings_file = settings_file_path
            if not os.path.isfile(settings_file):
                # settings file does not exist
                print('Unable to find file: {0!s}'.format(settings_file_path))

                # login new
                self.client = Client(
                    username, password,
                    on_login=lambda x: onlogin_callback(x, settings_file_path))
            else:
                with open(settings_file) as file_data:
                    cached_settings = json.load(file_data, object_hook=from_json)
                print('Reusing settings: {0!s}'.format(settings_file))

                device_id = cached_settings.get('device_id')
                # reuse auth settings
                self.client = Client(
                    username, password,
                    settings=cached_settings)

        except (ClientCookieExpiredError, ClientLoginRequiredError) as e:
            print('ClientCookieExpiredError/ClientLoginRequiredError: {0!s}'.format(e))

            # Login expired
            # Do relogin but use default ua, keys and such
            self.client = Client(
                username, password,
                device_id=device_id,
                on_login=lambda x: onlogin_callback(x, settings_file_path))

        except ClientLoginError as e:
            print('ClientLoginError {0!s}'.format(e))
            exit(9)
        except ClientError as e:
            print('ClientError {0!s} (Code: {1:d}, Response: {2!s})'.format(e.msg, e.code, e.error_response))
            exit(9)
        except Exception as e:
            print('Unexpected Exception: {0!s}'.format(e))
            exit(99)

        self.user_id = self.client.username_info(username)['user']['pk']


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print ("Invalid command. ex: python main.pyt [targetUsername]")
        sys.exit()
    else:
        target_username = sys.argv[1]

    # Making logger cutomized
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    settings_file_path = "settings"

    # Generate Instagram_DataService object with above username and password
    service = Instagram_DataService(username, password)

    following_recent_activities_raw = service.client.getFollowingRecentActivity()
    following_recent_activities = following_recent_activities_raw['stories']
    logger.info(following_recent_activities_raw)

    activities = {}
    for activity in following_recent_activities:
        args = activity['args']
        username = args['text'].split()[0]
        activity_properties = {}
        activity_properties['activity'] = args['text']
        try:
            activity_properties['media'] = args['media']
        except:
            pass

        activity_properties['time'] = datetime.datetime.fromtimestamp(int(args['timestamp'])).strftime('%Y-%m-%d %H:%M:%S')

        activities[username] = activity_properties

    # print (json.dumps(activities, indent=2))
    # target_username = input("Input username you are targeting: ")

    print(json.dumps(activities[target_username], indent=2))

# 1499313403
