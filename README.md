# Ladder app
파이썬, Flet UI, Gemini, CoPilot을 활용하여 생성한 사다리 애플리케이션입니다. AI를 활용한 연습 겸해서 사다리게임을 제작하였습니다.(jaekwonyi@naver.com)
This is a ladder game application created using Python, Flet UI, Gemini and CoPilot. I developed it as practice while experimenting with AI tools.(jaekwonyi@naver.com)

## Run the app

### uv

Run as a desktop app:

```
uv run flet run
```

Run as a web app:

```
uv run flet run --web
```

### Poetry

Install dependencies from `pyproject.toml`:

```
poetry install
```

Run as a desktop app:

```
poetry run flet run
```

Run as a web app:

```
poetry run flet run --web
```

For more details on running the app, refer to the [Getting Started Guide](https://flet.dev/docs/getting-started/).

## Build the app

### Android

```
flet build apk -v
```

For more details on building and signing `.apk` or `.aab`, refer to the [Android Packaging Guide](https://flet.dev/docs/publish/android/).

### iOS

```
flet build ipa -v
```

For more details on building and signing `.ipa`, refer to the [iOS Packaging Guide](https://flet.dev/docs/publish/ios/).

### macOS

```
flet build macos -v
```

For more details on building macOS package, refer to the [macOS Packaging Guide](https://flet.dev/docs/publish/macos/).

### Linux

```
flet build linux -v
```

For more details on building Linux package, refer to the [Linux Packaging Guide](https://flet.dev/docs/publish/linux/).

### Windows

```
flet build windows -v
```

For more details on building Windows package, refer to the [Windows Packaging Guide](https://flet.dev/docs/publish/windows/).
# ladder_flet
Ladder game (사다리 게임) built with Flet and Python. Supports 2-10 players, dynamic UI, and animation. See main.py for details.
