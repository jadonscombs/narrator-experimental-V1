"""
Initializer file for AI narrator application. Contains startup environment essentials.
"""

import configparser
import os
import sys
import traceback


def fetch_auth_data(data_needed: str) -> str:
    """
    Internal parent handler to return authentication data.
    Must specify target for data fetching.
    """
    _valid_auth = {
        "elevenlabs_auth" : "ELEVENLABS_API_KEY",
        "openai_auth" : "OPENAI_API_KEY"
    }
    
    if data_needed not in _valid_auth:
        raise RuntimeError("Invalid authentication data requested.")

    # get actual authentication field name for the .ini file
    _auth_fieldname = _valid_auth[data_needed].lower()
    print(f'auth_fieldname: {_auth_fieldname}')

    # read in initialization data
    config = configparser.ConfigParser()
    config.read("utils/api_config.ini")
    
    print(f'config sections: {config.sections()}')
    print(f'config options in AUTH: {config.options("AUTH")}')
    
    truth = "AUTH" in config.sections()
    print(f'truth is: {truth}')

    # if initialization file format is correct, proceed
    if (
        "AUTH" in config.sections()
        and _auth_fieldname in config.options("AUTH")
    ):
        return config["AUTH"][_auth_fieldname]
                
    # this code is only ever reached if an error occurs    
    print(
        "[auth.py] Malformed initialization data. Exiting...",
        file=sys.stderr
    )
    return None
    
    
def fetch_voice_id() -> str:
    """
    Internal parent handler to return ElevenLabs voice ID.
    """

    # read in initialization data
    config = configparser.ConfigParser()
    config.read("utils/target_voice.ini")
    
    print(f'[voice] config sections: {config.sections()}')
    print(f'[voice] config options in ELEVENLABS_VOICE: {config.options("ELEVENLABS_VOICE")}')

    # if initialization file format is correct, proceed
    if (
        "ELEVENLABS_VOICE" in config.sections()
        and "voice_id" in config.options("ELEVENLABS_VOICE")
    ):
        return config["ELEVENLABS_VOICE"]["voice_id"]
                
    # this code is only ever reached if an error occurs    
    print(
        "[auth.py] Malformed initialization data. Exiting...",
        file=sys.stderr
    )
    return None