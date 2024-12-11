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
 
from blpapi import * 
from common.helperfunctions import LOG as logger
import yaml 

# Define Name class variables
MarketDataEvents = Name('MarketDataEvents') 
SessionStarted = Name('SessionStarted') 
SessionTerminated = Name('SessionTerminated') 

# load config file with bpipe settings
config = yaml.safe_load(open("./bpipe/config.yml"))  
import common.helperfunctions as helperfunc
logger.info(config)



class UserAuth(): 

    def __init__(self , auth_id): 
        self.authorized = False 
        self.pending = True
        self.identity = None
        self.authMsg = "N/A" 
        self.auth_id = auth_id
 
    def isPending(self):
        return self.pending
    
    def getAuthId(self):
        return self.auth_id
 
    def isAuthorized(self):
        return self.authorized
 
    def setAuthorized(self, authStatus): 
        self.authorized = authStatus
        self.pending = False
    
    def getIdentity(self) -> Identity: 
        return self.identity
    
    def setIdentity(self, identity): 
        self.identity = identity
    
    def setAuthMsg(self,str):
        self.authMsg = str
    
    def getAuthMsg(self):
        return self.authMsg
     

class SessionEventHandler(object): 
    
    def __init__(self, authUsers): 
        self.authUsers = authUsers
    
    def processEvent(self, event,session):
        try:
            if event.eventType() == Event.AUTHORIZATION_STATUS or \
                event.eventType() == Event.REQUEST_STATUS:
                return self.processAuthEvents(event, session)
            else:
                return self.processMiscEvents(event)
        except  Exception as e:
            print ("Library Exception !!! %s" % e.description())
        return False
   
    def processMiscEvents(self, event):
        for msg in event:
            print(msg)
        
    def processAuthEvents(self, event,session):
        for msg in event:
            print(msg) 

            authCID = msg.correlationIds()[0].value()
           

            if msg.messageType() ==  Name("AuthorizationSuccess"):
                userAuth = self.authUsers.get(authCID)
                if ( userAuth != None):
                    userAuth.setAuthorized(True) 
                    userAuth.setIdentity(session.getAuthorizedIdentity(CorrelationId(authCID)))
                    logger.info(f"Authorization Successful. User Identity retreived. => authCID: {authCID}")

            elif msg.messageType() ==  Name("AuthorizationFailure") or msg.messageType() ==  Name("RequestFailure"): 
                
                userAuth = self.authUsers.get(authCID)
                if ( userAuth != None):
                    logger.info(f"Authorization Failed => authCID: {authCID}")
                    userAuth.setAuthorized(False)
                    userAuth.setAuthMsg(msg.toString())


class BpipeAuthSession:
  
    def __init__(self): 

        self.authUsers = {} 

        self.blpSession = None
        self.isStarted = False 
        self.authService = None 
        self.appName = config['application']
        self.createSession(config)
     
     
    def authenticate_user(self,auth_id, access_token):   
        
        # create user object with identity to store in cache for re-use
        auth_user = UserAuth(auth_id)
        self.authUsers[auth_id] = auth_user

        # authenticate and generate user identity in sapi with access token
        authOptions = AuthOptions.createWithToken(access_token)
        self.blpSession.generateAuthorizedIdentity(authOptions, CorrelationId(auth_id))
        
        # wait till user auth returns
        while auth_user.isPending():
            pass
        
        auth_user.setAuthMsg(f'User ({auth_id} ) logged in successfully')
        return  auth_user.isAuthorized(), auth_user.getAuthMsg()
    

    '''
    Create and start a new BLPAPI session
    '''
    def createSession(self,config):
        
        
        tlsOptions = TlsOptions.createFromFiles(config["tls_credentials"],
                                            config["password"],
                                            config["root_certificate"])

        options = None                                   
        if  config["internet"].upper() == "Y":
            options = SessionOptions()
            if "hosts" in config:
                for i, host in enumerate(config["hosts"]):
                    options.setServerAddress(host, config['port'], i)
                options.setAutoRestartOnDisconnection(True)

            else:
                options.setServerAddress(config['host'], config['port'], 0)
            options.setTlsOptions(tlsOptions) 
            logger.info("**** Connecting over Internet")
        
        
        options.setSessionIdentityOptions(AuthOptions.createWithApp(config["application"]))
        options.setAutoRestartOnDisconnection(True)  # auto-reconnect if connection is down
        options.setNumStartAttempts(3)   # attempt to restart 3 times before giving up
        eventHandler = SessionEventHandler(self.authUsers)
        self.blpSession = Session(options, eventHandler.processEvent)


        if self.blpSession.start():
            self.isStarted = True
            self.blpSession.openService("//blp/apiauth")
            self.authService = self.blpSession.getService("//blp/apiauth")
            logger.info("Blpapi session open") 
        else:
            self.isStarted = False
            logger.info("Blpapi session failed to open") 
 
