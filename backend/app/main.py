from . import create_app

app = create_app()


if __name__ == "__main__":
    # For local development convenience
    port = app.config.get("PORT", 8000)
    app.run(host="0.0.0.0", port=port, debug=app.config.get("DEBUG", False))