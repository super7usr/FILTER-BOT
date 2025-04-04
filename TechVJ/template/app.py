import asyncio
from aiohttp import web
import humanize
import os
from utils import temp
from database.ia_filterdb import get_all_search_results

routes = web.RouteTableDef()

async def get_cap(file_ids, search_query):
    cap = f"<b>Tʜᴇ Rᴇꜱᴜʟᴛꜱ Fᴏʀ ☞ {search_query}\n\n</b>"
    cap += "<b>\n\n<u>🍿 Your Movie Files 👇</u></b>\n\n"

    for file_id in file_ids:
        file_details = await get_file_details(file_id)  # Assuming you have get_file_details
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

    db_data = await get_all_search_results(search_query)

    if db_data:  # Check if db_data is not empty
        file_ids = [item["file_id"] for item in db_data] #Extract file_ids from db_data
        cap = await get_cap(file_ids, search_query)
        return web.Response(text=cap, content_type="text/html")
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
