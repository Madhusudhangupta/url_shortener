import sqlite3
from hashids import Hashids
from flask import Flask, render_template, request, flash, redirect, url_for


def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

app = Flask(__name__)
app.config['SECRET_KEY'] = 'somerandomstring'

hashids = Hashids(min_length=4, salt=app.config['SECRET_KEY'])


@app.route('/', methods=['GET', 'POST'])
def index():
    conn = get_db_connection()

    if request.method == 'POST':
        url = request.form['url']

        if not url:
            flash('PLease insert url!')
            return redirect(url_for('index'))

        existing_url_data = conn.execute('SELECT * FROM URLS WHERE original_url = ?', (url,)).fetchone()

        if existing_url_data:
            url_id = existing_url_data['id']
            hashid = hashids.encode(url_id)
            short_url = request.host_url + hashid

        else:
            url_data = conn.execute('INSERT INTO URLS (original_url) VALUES (?)',
                                    (url,))
            conn.commit()

            url_id = url_data.lastrowid
            hashid = hashids.encode(url_id)
            short_url = request.host_url + hashid

        conn.close()
        return render_template('index.html', short_url=short_url)
    return render_template('index.html')



@app.route('/<id>')
def url_redirect(id):
    conn = get_db_connection()

    original_id = hashids.decode(id)
    if original_id:
        original_id = original_id[0]
        url_data = conn.execute('SELECT original_url, clicks FROM urls'
                                ' WHERE id = (?)', (original_id,)
                                ).fetchone()
        original_url = url_data['original_url']
        clicks = url_data['clicks']

        conn.execute('UPDATE urls SET clicks = ? WHERE id = ?',
                     (clicks+1, original_id))

        conn.commit()
        conn.close()
        return redirect(original_url)
    else:
        flash('Invalid URL')
        return redirect(url_for('index'))
    


@app.route('/history')
def history():
    conn = get_db_connection()

    search_query = request.args.get('search', '')

    if search_query:
        db_urls = conn.execute(
            'SELECT id, created, original_url, clicks FROM urls'
            ' WHERE original_url LIKE ?',
            ('%' + search_query + '%',)
        ).fetchall()
    else:
        db_urls = conn.execute('SELECT id, created, original_url, clicks FROM urls'
            ).fetchall()
    conn.close()

    urls = []
    for url in db_urls:
        url = dict(url)
        url['short_url'] = request.host_url + hashids.encode(url['id'])
        urls.append(url)

    """
    if not urls:
        message = 'Ah ah.... Try other keywords'
    else:
        message = None
    
    return render_template('history.html', urls=urls, search_query=search_query, message=message)
    """

    return render_template('history.html', urls=urls, search_query=search_query)
