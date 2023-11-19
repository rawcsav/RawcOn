from dotenv import load_dotenv

load_dotenv()

from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True, port=8080, static_files={'/static': '/Users/gavinmason/PycharmProjects/BotifyStats/app/static'})
