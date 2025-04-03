import asyncio
from aiohttp import web
from imdb import Cinemagoer
import humanize
import secrets
import json
from utils import temp

ia = Cinemagoer()
ads = ["Your Ad Here 1", "Your Ad Here 2", "Your Ad Here 3"]  # Example ads

routes = web.RouteTableDef()

async def get_imdb_data(search_query):
    loop = asyncio.get_event_loop()
    movie = await loop.run_in_executor(None, ia.search_movie, search_query)
    if movie:
        movie = await loop.run_in_executor(None, ia.get_movie, movie[0].movieID)
        return movie
    return None

async def get_cap(settings, remaining_seconds, files, query, total_results, search):
    if settings.get("imdb"):
        imdb_cap = query.get("IMDB_CAP") #assuming query object has IMDB_CAP.
        if imdb_cap:
            cap = imdb_cap
        else:
            imdb = await get_imdb_data(search) if settings.get("imdb") else None
            if imdb:
                TEMPLATE = """<b>{title} ({year})</b>\n\n{plot}\n\n""" #using a simple template for web.
                cap = TEMPLATE.format(
                    title=imdb.get('title'),
                    year=imdb.get('year'),
                    plot=imdb.get('plot')[0] if imdb.get('plot') else ''
                )
            else:
                cap = f"<b>Tʜᴇ Rᴇꜱᴜʟᴛꜱ Fᴏʀ ☞ {search}\n\nʀᴇsᴜʟᴛ sʜᴏᴡ ɪɴ ☞ {remaining_seconds} sᴇᴄᴏɴᴅs\n\n</b>"
        cap += "<b>\n\n<u>🍿 Your Movie Files 👇</u></b>\n\n"
    else:
        cap = f"<b>Tʜᴇ Rᴇꜱᴜʟᴛꜱ Fᴏʀ ☞ {search}\n\nʀᴇsᴜʟᴛ sʜᴏᴡ ɪɴ ☞ {remaining_seconds} sᴇᴄᴏɴᴅs\n\n</b>"
        cap += "<b><u>🍿 Your Movie Files 👇</u></b>\n\n"

    for file in files:
        file_name = ' '.join(filter(lambda x: not x.startswith(('[', '@', 'www.')), file['file_name'].split()))
        cap += f"<b>📁 <a href='https://telegram.me/{temp['U_NAME']}?start=files_{file['file_id']}'>[{humanize.naturalsize(file['file_size'])}] {file_name}\n\n</a></b>"

    return cap

@routes.get("/movie")
async def movie_search(request):
    search_query = request.query.get('q')
    if not search_query:
        return web.Response(text="Please provide a movie query using '?q=movie_name'", status=400)

    imdb_data = await get_imdb_data(search_query)

    if imdb_data:
        files = [{"file_id": secrets.token_hex(8), "file_name": "example.mp4", "file_size": 1024 * 1024}] #example file list.
        cap = await get_cap({"imdb": True}, 60, files, request.query, 1, search_query)
        return web.Response(text=cap, content_type='text/html')
    else:
        return web.Response(text=f"No movie found with the name '{search_query}'. It might not be released or added yet.", content_type='text/html')

