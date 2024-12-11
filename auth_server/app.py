# Copyright 2023 Bloomberg Finance L.P.

# Sample code provided by Bloomberg is made available for illustration purposes 
# only. Sample code is modifiable by individual users and is not reviewed for 
# reliability, accuracy and is not supported as part of any Bloomberg service.  
# Users are solely responsible for the selection of and use or intended use of 
# the sample code, its applicability, accuracy and adequacy, and the resultant 
# output thereof. Sample code is proprietary and confidential to Bloomberg and 
# neither the recipient nor any of its representatives may distribute, publish 
# or display such code to any other party, other than information disclosed to 
# its employees on a need-to-know basis in connection with the purpose for which 
# such code was provided. Sample code provided by Bloomberg is provided without 
# any representations or warranties and subject to modification by Bloomberg in 
# its sole discretion.
 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR 
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS 
# FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL BLOOMBERG BE 
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, 
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE 
# \USE OR OTHER DEALINGS IN THE SOFTWARE.
 

from fastapi import FastAPI , Request
from fastapi.templating import Jinja2Templates
from bpipe.bpipe_auth import BpipeAuthSession
import common.helperfunctions as helperfunc
from common.helperfunctions import LOG as logger

from starlette.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn 


bpipeAuthSession = BpipeAuthSession()

app = FastAPI() 
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)  

templates = Jinja2Templates(directory="html/") 
    
@app.get("/")
def main(request:Request): 
    # redirecting request to main html page
    return templates.TemplateResponse('index.html', context={'request': request})


@app.get("/appurl/")
def main(request:Request): 
    # redirecting request to html 
    return templates.TemplateResponse('appurl.html', context={'request': request})


@app.get("/redirect/")
def redirect(request:Request): 
    # redirecting request to html 
    return templates.TemplateResponse('redirect.html', context={'request': request})



class AuthParams(BaseModel):
    auth_id: str
    auth_code: str
    code_verifier: str
    redirect_uri: str

###  start of api calls
@app.post("/api/authenticate_user/")
def authenticate_user(payload: AuthParams):  

    auth_id = payload.auth_id
    auth_code = payload.auth_code
    code_verifier = payload.code_verifier
    redirect_uri = payload.redirect_uri

    logger.info(f"Received request to authenticate with SAPI from user: {auth_id} ")
    
    access_token = helperfunc.get_access_token(auth_code, code_verifier, redirect_uri)
    is_authorized, message  = bpipeAuthSession.authenticate_user(auth_id,access_token)  
 
    return {"authorized": is_authorized, 
            "message": message}



if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8052, reload=True) 