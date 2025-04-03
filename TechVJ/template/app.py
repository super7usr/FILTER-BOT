from flask import Flask, render_template, request, redirect, url_for
import asyncio
import aiohttp
import aiohttp import web
from cinemagoer import Cinemagoer
import humanize
import secrets

app = web.RouteTableDef()
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

@app.route('/', methods=['GET', 'POST'])
async def index():
    if request.method == 'POST':
        search_query = request.form['search_query']
        files_data = request.form['files_data']  # Assuming JSON string of files
        files = eval(files_data) #eval is dangerous, but used here for simplicity. Replace with proper JSON parsing in production.

        imdb_data = await get_imdb_data(search_query)

        if imdb_data:
            cap = f"<b>{imdb_data['title']} ({imdb_data['year']})</b>\n\n{imdb_data.get('plot')[0] if imdb_data.get('plot') else ''}\n\n"
        else:
            cap = f"<b>Results for {search_query}</b>\n\n"

        for file in files:
            short_code = generate_short_code()
            links[short_code] = file
            short_url = url_for('file_redirect', short_code=short_code, _external=True)
            cap += f"📁 <a href='{short_url}'>[{humanize.naturalsize(file['file_size'])}] {file['file_name']}</a>\n"

        cap += f"\n{secrets.choice(ads)}"

        return render_template('results.html', caption=cap)

    return render_template('search.html')

@app.route('/file/<short_code>')
def file_redirect(short_code):
    file_data = links.get(short_code)
    if file_data:
        # In a real app, you'd serve the file or redirect to its download location.
        return f"Downloading: {file_data['file_name']}. Size: {humanize.naturalsize(file_data['file_size'])}" #Replace with actual file serving logic
    else:
        return "File not found", 404
