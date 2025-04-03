import asyncio
from aiohttp import web
from cinemagoer import Cinemagoer
import humanize
import secrets
import json

ia = Cinemagoer()
links = {}  # Store file details and short codes
ads = ["Your Ad Here 1", "Your Ad Here 2", "Your Ad Here 3"]  # Example ads

async def get_imdb_data(search_query):
    loop = asyncio.get_event_loop()
    movie = await loop.run_in_executor(None, ia.search_movie, search_query)
    if movie:
        movie = await loop.run_in_executor(None, ia.get_movie, movie[0].movieID)
        return movie
    return None

def generate_short_code():
    return secrets.token_urlsafe(6)

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
            short_code = generate_short_code()
            links[short_code] = file
            short_url = str(request.url.join(request.app.router['file_redirect'].url_for(short_code=short_code)))
            cap += f"📁 <a href='{short_url}'>[{humanize.naturalsize(file['file_size'])}] {file['file_name']}</a>\n"

        cap += f"\n{secrets.choice(ads)}"

        return web.Response(text=cap, content_type='text/html')

    return web.Response(text="""
    <!DOCTYPE html>
    <html>
    <head><title>Movie Search</title></head>
    <body>
        <form method="POST">
            Search: <input type="text" name="search_query"><br>
            Files (JSON): <textarea name="files_data"></textarea><br>
            <input type="submit" value="Search">
        </form>
    </body>
    </html>
    """, content_type='text/html')

async def file_redirect(request):
    short_code = request.match_info['short_code']
    file_data = links.get(short_code)
    if file_data:
        # In a real app, you'd serve the file or redirect to its download location.
        return web.Response(text=f"Downloading: {file_data['file_name']}. Size: {humanize.naturalsize(file_data['file_size'])}") #Replace with actual file serving logic
    else:
        return web.Response(text="File not found", status=404)

async def main():
    app = web.Application()
    app.router.add_get('/', index)
    app.router.add_post('/', index)
    app.router.add_get('/file/{short_code}', file_redirect, name='file_redirect')
    return app

if __name__ == '__main__':
    web.run_app(asyncio.run(main()))
