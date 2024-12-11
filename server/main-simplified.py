import _thread as thread
import asyncio

import blpapi
from aiohttp import web
from blpapi import Event as EventType


class BlpapiManager:
    def __init__(self, asyncio_loop):
        # provide an instance to python's async loop, so we can send it information
        # from the other threads created by the blpapi library
        self._asyncio_loop = asyncio_loop
        
        self._session = None
        self._dispatcher = None
        
        # Every outgoing blpapi request needs to have
        # a unique id associated to it.
        # Using an auto-incrementing counter.
        self._correlation_id_counter = 1

        # associate incoming responses to our outgoing requests
        # via their correlation_id stored in this lookup
        self._async_future_dict = {}

    def start(self):
        session_options = blpapi.SessionOptions()
        session_options.setServerHost('nytestsapi01')
        session_options.setServerPort(9294)

        # Create an EventDispatcher with 2 processing threads
        self._dispatcher = blpapi.EventDispatcher(2)

        # Create a Session
        self._session = blpapi.Session(session_options, self._process_event, self._dispatcher)

        self._dispatcher.start()
        self._session.start()

        # In order to authenticate our jwt, we will need to use the apiauth service.
        # we should make sure it is reachable at startup
        if not self._session.openService('//blp/apiauth'):
            print("Failed to open //blp/apiauth")
            raise Exception("Failed to open //blp/apiauth")

    async def auth_req(self, token):
        cur_cid = self._correlation_id_counter
        cid = blpapi.CorrelationId(cur_cid)
        self._correlation_id_counter += 1

        self._async_future_dict[cur_cid] = asyncio.get_event_loop().create_future()

        authOptions = blpapi.AuthOptions.createWithToken(token)
        self._session.generateAuthorizedIdentity(authOptions, cid)
		
        item = await self._async_future_dict[cur_cid]
        self._async_future_dict.pop(cur_cid)

        if item is False:
            print('Identity problem')
            return False
			
        identity = self._session.getAuthorizedIdentity(cid)
        
        return identity

    async def subscribe(self, securities, fields, identity):
        sl = blpapi.SubscriptionList()

        queues = []

        for s in securities:
            cur_cid = self._correlation_id_counter
            self._correlation_id_counter += 1
            self._async_future_dict[cur_cid] = asyncio.Queue(1)  # no need to have more than one data event
            queues.append((s, self._async_future_dict[cur_cid], cur_cid,))

            topic = f'//blp/mktdata/{s}'
            cid = blpapi.CorrelationId(cur_cid)
            print("Subscribing {0} => {1}".format(cid, topic))
            sl.add(topic, fields, correlationId=cid)

        self._session.subscribe(sl, identity)

        try:
            # indefinitely return a stream market data events
            while True:
                for security, q, _cid in queues:
                    if q.empty() is False:
                        item = await q.get()
                        q.task_done()
                        yield security, item

                # to avoid sending back too much data, we can throttle
                # ourselves to once per second
                await asyncio.sleep(1)

        except Exception as ex:
            print('subscription exception')
            print(ex)
        finally:
            print('subscription end')
            self._session.unsubscribe(sl)
            for _security, _q, cid_to_clean in queues:
                self._async_future_dict.pop(cid_to_clean)

    def stop(self):
        self._session.stop()
        self._dispatcher.stop()

    def _process_event(self, event, _session):
        try:
            event_type = event.eventType()
            # Please note that blpapi can receive a large diverse array of events,
            # for a real server implementation, all of relevant ones would have to
            # be handled appropriately/robustly.
			
            if event_type == EventType.RESPONSE:
                for msg in event:
                    correlation_id = msg.correlationIds()[0].value()
                    self._asyncio_loop.call_soon_threadsafe(self._async_future_dict[correlation_id].set_result, True)
            elif event_type == EventType.REQUEST_STATUS:
                for msg in event:
                    if msg.messageType() == 'RequestFailure':
                        correlation_id = msg.correlationIds()[0].value()
                        self._asyncio_loop.call_soon_threadsafe(
                            self._async_future_dict[correlation_id].set_result,
                            False
                        )
            elif event_type == EventType.SUBSCRIPTION_DATA:
                for msg in event:
                    correlation_id = msg.correlationIds()[0].value()

                    if all(msg.hasElement(fld, True) for fld in
                           ['LAST_PRICE', 'EVENT_TIME', 'RT_PX_CHG_NET_1D', 'RT_PX_CHG_PCT_1D']):
                        # we should avoid passing through the actual blpapi object through
                        # the thread boundary, we should just pass back the data
                        data_obj = {
                            'price': msg.getElementAsFloat('LAST_PRICE'),
                            'marketTime': msg.getElementAsString('EVENT_TIME'),
                            'netChange': msg.getElementAsFloat('RT_PX_CHG_NET_1D'),
                            'percentChange': msg.getElementAsFloat('RT_PX_CHG_PCT_1D')
                        }

                        async def task_to_run():
                            if self._async_future_dict[correlation_id].empty():
                                await self._async_future_dict[correlation_id].put(data_obj)

                        self._asyncio_loop.create_task(task_to_run())
            elif event_type == EventType.AUTHORIZATION_STATUS:
                for msg in event:
                    if msg.messageType() == blpapi.Name('AuthorizationSuccess'):
                        correlation_id = msg.correlationIds()[0].value()
                        self._asyncio_loop.call_soon_threadsafe(self._async_future_dict[correlation_id].set_result, True)
                    else:
                        print(msg) # watch for the revoke

        except Exception as ex:
            print("Error in event handler:", ex)
            # Interrupt a "sleep loop" in main thread
            thread.interrupt_main()


class Controller:
    def __init__(self, blpapi_manager):
        self._blpapi_manager = blpapi_manager

    async def entry_route(self, request):
        # aiohttp boilerplate
        ws = web.WebSocketResponse()
        await ws.prepare(request)

        # in order for the server to actually do anything with our JWT,
        # the front end first will need to send it to us
        token = await ws.receive_str()

        identity = await self._blpapi_manager.auth_req(token)
        if identity is False:
            print('Could not authenticate user')
            await ws.send_str('Error: could not authenticate user')
            return

        securities = ['SPX INDEX', 'INDU INDEX', 'NDX INDEX', 'RTY INDEX', 'NKY INDEX']
        currency = ["CAD CURNCY", "JPY CURNCY", "EUR CURNCY", "GBP CURNCY", "ARS CURNCY"]

        fields = ['LAST_PRICE', 'EVENT_TIME', 'RT_PX_CHG_NET_1D', 'RT_PX_CHG_PCT_1D']

        # once we are authenticated, send a request to blpapi library in order to
        # subscribe to live market data.
        async for ticker, data in self._blpapi_manager.subscribe(securities + currency, fields, identity):
            indexes_change = {}
            currency_change = {}

            if ticker in securities:
                indexes_change[ticker] = data
            elif ticker in currency:
                currency_change[ticker] = data

            # as data comes in, we should send it back to front-end
            await ws.send_json({'indexes': indexes_change, 'currency': currency_change})


if __name__ == '__main__':
    loop = asyncio.get_event_loop()

    blpapi_instance = BlpapiManager(loop)
    blpapi_instance.start()

    controller = Controller(blpapi_instance)

    # add our controller method to bind our handler to
    # /live-data
    app = web.Application()
    app.add_routes([web.get('/live-data', controller.entry_route)])
    web.run_app(app, port=3000)

    blpapi_instance.stop()
