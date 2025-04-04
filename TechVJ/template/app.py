import asyncio
from aiohttp import web
from imdb import Cinemagoer
import humanize
import secrets
import json
from utils import temp
from database.ia_filterdb import get_search_results as get_file_ids_from_imdb_search
import os

ia = Cinemagoer()

routes = web.RouteTableDef()

async def get_imdb_data(search_query):
    loop = asyncio.get_event_loop()
    movie = await loop.run_in_executor(None, ia.search_movie, search_query)
    if movie:
        movie = await loop.run_in_executor(None, ia.get_movie, movie[0].movieID)
        return movie
    return None

async def get_cap(file_ids, search):
    cap = f"<b>Tʜᴇ Rᴇꜱᴜʟᴛꜱ Fᴏʀ ☞ {search}\n\n</b>"
    cap += "<b>\n\n<u>🍿 Your Movie Files 👇</u></b>\n\n"

    for file_id in file_ids:
        file_details = await database.get_file_details(file_id)
        if file_details:
            file_name = " ".join(
                filter(lambda x: not x.startswith(("[", "@", "www.")), file_details["file_name"].split())
            )
            cap += f"<b>📁 <a href='https://telegram.me/{temp['U_NAME']}?start=files_{file_id}'>[{humanize.naturalsize(file_details['file_size'])}] {file_name}\n\n</a></b>"
        else:
            cap += f"<b>📁 File with ID {file_id} not found.\n\n</b>"

    return cap

@routes.get("/movie")
async def movie_search(request):
    search_query = request.query.get("q")
    if not search_query:
        return web.Response(text="Please provide a movie query using '?q=movie_name'", status=400)

    imdb_data = await get_imdb_data(search_query)

    if imdb_data:
        file_ids = await get_file_ids_from_imdb_search(imdb_data["imdb_id"])

        if file_ids:
            cap = await get_cap(file_ids, search_query)
            return web.Response(text=cap, content_type="text/html")
        else:
            return web.Response(text="No files found for this movie.", content_type="text/html")

    else:
        return web.Response(
            text=f"No movie found with the name '{search_query}'. It might not be released or added yet.",
            content_type="text/html",
        )

@routes.get("/favicon.ico")
async def favicon(request):
    favicon_path = os.path.join(os.getcwd(), "favicon.ico")
    try:
        return web.FileResponse(favicon_path)
    except FileNotFoundError:
        return web.Response(status=404)

