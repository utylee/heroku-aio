from aiohttp.web import StreamResponse, HTTPNotAcceptable
import aiohttp_jinja2
import asyncio
import io
import json
import logging
import time

from web.templates.content import get_content


log = logging.getLogger(__name__)


@aiohttp_jinja2.template('index.jinja2')
async def index(request):
    return {
        'title': 'Heroku aiohttp Web Template',
        'gh_repo_url': 'https://github.com/sseg/heroku-aiohttp-web',
        'bootstrap_css_url': '//maxcdn.bootstrapcdn.com/bootstrap/3.3.4/css/bootstrap.min.css',
        'bootstrap_js_url': '//maxcdn.bootstrapcdn.com/bootstrap/3.3.4/js/bootstrap.min.js',
        'jquery_url': '//ajax.googleapis.com/ajax/libs/jquery/1.12.4/jquery.min.js',
        'content': {
            'what_is_this': get_content('index', 'what_is_this'),
            'where_next': get_content('index', 'where_next'),
            'alert_guide': get_content('index', 'alert_guide'),
            'helpful_links': get_content('index', 'helpful_links'),
        }
    }


''' 
    utylee home server들의 status를 확인하는 용도의 프로세스로 활용하기로
    websocket이 아닌 간편하게 SSE를 사용하던데 이  프로세스에 덧붙이기로.
'''
    
async def tick(request):
    if 'text/event-stream' not in request.headers.getall('ACCEPT', []):
        raise HTTPNotAcceptable(reason="'text/event-stream' not found in Accept headers.")

    resp = StreamResponse(
        status=200,
        reason='OK',
        headers={
            'Content-Type': 'text/event-stream',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive'
        }
    )

    log.debug('Opening new event stream on request: %s', request)
    await resp.prepare(request)

    request.app.connections.add(resp)
    resp.should_stop = False
    try:
        while not resp.should_stop:
            #ts = time.monotonic()
            fut = asyncio.open_connection('utylee.dlinkddns.com', 1117, loop=loop)
            try:
                reader, writer = await asyncio.wait_for(fut, timeout=3)
            except:
                ts = 'exception, maybe Timeout...'
                print(ts)
                return

            writer.write('utyleeping'.encode())
            rbuf = await reader.read(100)
            print(f'rbuf:{rbuf}')
            ts = rbuf.decode()

            payload = json.dumps({'data': ts})
            resp.write(build_message(payload, id=ts, event='tick'))
            await resp.drain()
            await asyncio.sleep(5)

    finally:
        request.app.connections.remove(resp)

    return resp


def build_message(data, id=None, event=None):
    buffer = io.BytesIO()
    if id is not None:
        buffer.write('id: {0}\r\n'.format(id).encode('utf-8'))
    if event is not None:
        buffer.write('event: {0}\r\n'.format(event).encode('utf-8'))
    for chunk in data.split('\r\n'):
        buffer.write('data: {0}\r\n'.format(chunk).encode('utf-8'))
    buffer.write(b'\r\n')
    return buffer.getvalue()
