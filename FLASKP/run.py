from app import create_app

app = create_app()

@app.route('/test')
def test_route():
    return "TEST WORKING!"

if __name__ == '__main__':
    app.run(debug=True)