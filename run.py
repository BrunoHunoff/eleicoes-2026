from app import create_app

app = create_app()

if __name__ == "__main__":
    # A porta 5000 (padrão do Flask) é ocupada pelo AirPlay no macOS
    app.run(debug=True, port=5001)
