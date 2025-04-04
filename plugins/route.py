import re, math, logging, secrets, mimetypes, time, json
from info import *
from aiohttp import web
from aiohttp.http_exceptions import BadStatusLine
from TechVJ.bot import multi_clients, work_loads, TechVJBot
from TechVJ.server.exceptions import FIleNotFound, InvalidHash
from TechVJ import StartTime, __version__
from TechVJ.util.custom_dl import ByteStreamer
from TechVJ.util.time_format import get_readable_time
from TechVJ.util.render_template import render_page
from imdb import Cinemagoer

routes = web.RouteTableDef()
ia = Cinemagoer()
links = {}  # Store file details (no short codes)
ads = ["Your Ad Here 1", "Your Ad Here 2", "Your Ad Here 3"]  # Example ads

routes = web.RouteTableDef()

async def get_imdb_data(search_query):
    loop = asyncio.get_event_loop()
    movie = await loop.run_in_executor(None, ia.search_movie, search_query)
    if movie:
        movie = await loop.run_in_executor(None, ia.get_movie, movie[0].movieID)
        return movie
    return None
    
@routes.get("/", allow_head=True)
@routes.post("/")
async def index(request):
    if request.method == 'POST':
        data = await request.post()
        search_query = data['search_query']
        try:
            files = json.loads(data['files_data'])  # Use json.loads instead of eval
        except json.JSONDecodeError:
            return web.Response(text="Invalid files_data", status=400)

        imdb_data = await get_imdb_data(search_query)

        if imdb_data:
            cap = f"<b>{imdb_data['title']} ({imdb_data['year']})</b>\n\n{imdb_data.get('plot')[0] if imdb_data.get('plot') else ''}\n\n"
        else:
            cap = f"<b>Results for {search_query}</b>\n\n"

        for file in files:
            links[file['file_name']] = file #Store file data by file name instead of short code.
            cap += f"📁 <a href='/file/{file['file_name']}'>[{humanize.naturalsize(file['file_size'])}] {file['file_name']}</a>\n"

        cap += f"\n{secrets.choice(ads)}"

        return web.Response(text=cap, content_type='text/html')

    return web.Response(text="""
    <!DOCTYPE html>
    <html>
    <head><title>Movie Search</title></head>
    <body>
        <form method="POST">
            Search: <input type="text" name="search_query"><br>
            <input type="submit" value="Search">
            <a href='https://telegram.me/'>{{search_query}}</a>
        </form>
    </body>
    </html>
    """, content_type='text/html')

@routes.get('/file/{file_name}')
async def file_redirect(request):
    file_name = request.match_info['file_name']
    file_data = links.get(file_name)
    if file_data:
        # In a real app, you'd serve the file or redirect to its download location.
        return web.Response(text=f"Downloading: {file_data['file_name']}. Size: {humanize.naturalsize(file_data['file_size'])}") #Replace with actual file serving logic
    else:
        return web.Response(text="File not found", status=404)


@routes.get(r"/watch/{path:\S+}", allow_head=True)
async def stream_handler(request: web.Request):
    try:
        path = request.match_info["path"]
        match = re.search(r"^([a-zA-Z0-9_-]{6})(\d+)$", path)
        if match:
            secure_hash = match.group(1)
            id = int(match.group(2))
        else:
            id = int(re.search(r"(\d+)(?:\/\S+)?", path).group(1))
            secure_hash = request.rel_url.query.get("hash")
        return web.Response(text=await render_page(id, secure_hash), content_type='text/html')
    except InvalidHash as e:
        raise web.HTTPForbidden(text=e.message)
    except FIleNotFound as e:
        raise web.HTTPNotFound(text=e.message)
    except (AttributeError, BadStatusLine, ConnectionResetError):
        pass
    except Exception as e:
        logging.critical(e.with_traceback(None))
        raise web.HTTPInternalServerError(text=str(e))

@routes.get(r"/{path:\S+}", allow_head=True)
async def stream_handler(request: web.Request):
    try:
        path = request.match_info["path"]
        match = re.search(r"^([a-zA-Z0-9_-]{6})(\d+)$", path)
        if match:
            secure_hash = match.group(1)
            id = int(match.group(2))
        else:
            id = int(re.search(r"(\d+)(?:\/\S+)?", path).group(1))
            secure_hash = request.rel_url.query.get("hash")
        return await media_streamer(request, id, secure_hash)
    except InvalidHash as e:
        raise web.HTTPForbidden(text=e.message)
    except FIleNotFound as e:
        raise web.HTTPNotFound(text=e.message)
    except (AttributeError, BadStatusLine, ConnectionResetError):
        pass
    except Exception as e:
        logging.critical(e.with_traceback(None))
        raise web.HTTPInternalServerError(text=str(e))

class_cache = {}

async def media_streamer(request: web.Request, id: int, secure_hash: str):
    range_header = request.headers.get("Range", 0)
    
    index = min(work_loads, key=work_loads.get)
    faster_client = multi_clients[index]
    
    if MULTI_CLIENT:
        logging.info(f"Client {index} is now serving {request.remote}")

    if faster_client in class_cache:
        tg_connect = class_cache[faster_client]
        logging.debug(f"Using cached ByteStreamer object for client {index}")
    else:
        logging.debug(f"Creating new ByteStreamer object for client {index}")
        tg_connect = ByteStreamer(faster_client)
        class_cache[faster_client] = tg_connect
    logging.debug("before calling get_file_properties")
    file_id = await tg_connect.get_file_properties(id)
    logging.debug("after calling get_file_properties")
    
    if file_id.unique_id[:6] != secure_hash:
        logging.debug(f"Invalid hash for message with ID {id}")
        raise InvalidHash
    
    file_size = file_id.file_size

    if range_header:
        from_bytes, until_bytes = range_header.replace("bytes=", "").split("-")
        from_bytes = int(from_bytes)
        until_bytes = int(until_bytes) if until_bytes else file_size - 1
    else:
        from_bytes = request.http_range.start or 0
        until_bytes = (request.http_range.stop or file_size) - 1

    if (until_bytes > file_size) or (from_bytes < 0) or (until_bytes < from_bytes):
        return web.Response(
            status=416,
            body="416: Range not satisfiable",
            headers={"Content-Range": f"bytes */{file_size}"},
        )

    chunk_size = 1024 * 1024
    until_bytes = min(until_bytes, file_size - 1)

    offset = from_bytes - (from_bytes % chunk_size)
    first_part_cut = from_bytes - offset
    last_part_cut = until_bytes % chunk_size + 1

    req_length = until_bytes - from_bytes + 1
    part_count = math.ceil(until_bytes / chunk_size) - math.floor(offset / chunk_size)
    body = tg_connect.yield_file(
        file_id, index, offset, first_part_cut, last_part_cut, part_count, chunk_size
    )

    mime_type = file_id.mime_type
    file_name = file_id.file_name
    disposition = "attachment"

    if mime_type:
        if not file_name:
            try:
                file_name = f"{secrets.token_hex(2)}.{mime_type.split('/')[1]}"
            except (IndexError, AttributeError):
                file_name = f"{secrets.token_hex(2)}.unknown"
    else:
        if file_name:
            mime_type = mimetypes.guess_type(file_id.file_name)
        else:
            mime_type = "application/octet-stream"
            file_name = f"{secrets.token_hex(2)}.unknown"

    return web.Response(
        status=206 if range_header else 200,
        body=body,
        headers={
            "Content-Type": f"{mime_type}",
            "Content-Range": f"bytes {from_bytes}-{until_bytes}/{file_size}",
            "Content-Length": str(req_length),
            "Content-Disposition": f'{disposition}; filename="{file_name}"',
            "Accept-Ranges": "bytes",
        },
    )
