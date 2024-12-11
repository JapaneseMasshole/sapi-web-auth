
import logging
import yaml
import hashlib
import base64
import secrets 
import string
import requests
import json

# setup logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)-8s] [%(name)s:%(lineno)s]: %(message)s',
)
LOG = logging.getLogger(__name__)

config = yaml.safe_load(open("./bpipe/config.yml"))  

bsso_domain = config['bsso_domain']


def get_access_token(authCode, codeVerifier, redirect_uri):
        
    accessToken = None
    
    headers = {
         "method":"POST", 
    }

    aTokenPayload = {
        "grant_type":"authorization_code",
        "client_id": config["client_id"],
        "code": authCode,
        "code_verifier":codeVerifier,
        "response_type": 'code',
        "redirect_uri": redirect_uri 
    }

    bssoUrl = f"https://{bsso_domain}/as/token.oauth2"

    LOG.info(f">>> Auth Server sent a POST request to {bssoUrl}: {aTokenPayload}")
    
    bsso_response = requests.post(bssoUrl, data=aTokenPayload, headers=headers)
     
    statusCode = bsso_response.status_code 
    if statusCode == 200:
        LOG.info(bsso_response.content)
        response_dict = json.loads(bsso_response.content)
        accessToken = response_dict["access_token"]
        LOG.info(f"<<< Auth Server received the accessToken from BSSO: {accessToken}")
    else:
        LOG.info(bsso_response.content)
        LOG.info(f"<<< Auth Server failed to get accessToken. \n\n")
        return None

    LOG.info(f"*** Auth Server completed PKCE OAuth\n\n")

    return accessToken
