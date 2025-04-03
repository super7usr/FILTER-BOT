import asyncio
from aiohttp import web
from imdb import Cinemagoer
import humanize
import secrets
import json

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

@routes.get("/movie")
async def movie_search(request):
    search_query = request.query.get('q')
    if not search_query:
        return web.Response(text="Please provide a movie query using '?q=movie_name'", status=400)

    imdb_data = await get_imdb_data(search_query)

    if imdb_data:
        cap = f"<b>{imdb_data['title']} ({imdb_data['year']})</b>\n\n{imdb_data.get('plot')[0] if imdb_data.get('plot') else ''}\n\n"
        return web.Response(text=cap, content_type='text/html')
    else:
        return web.Response(text=f"No movie found with the name '{search_query}'. It might not be released or added yet.", content_type='text/html')

