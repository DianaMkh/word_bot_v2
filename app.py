import requests


def translation(word) -> str:
    APP_ID = "e62cad1e"
    APP_KEY = "lukd5sn6nl44boi9k8d8vtvleylvncdc"

    url = f"https://od-api-sandbox.oxforddictionaries.com/api/v2/translations/en/ru/{word.lower()}"

    headers = {
        "app_id": APP_ID,
        "app_key": APP_KEY
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json()

        try:
            translations = data['results'][0]['lexicalEntries'][0]['entries'][0]['senses'][0]['translations']
            for t in translations:
                return f"{word} → {t['text']}"
        except (KeyError, IndexError):
            return "Перевод не найден в ответе."
    else:
        return f"Ошибка {response.status_code}: {response.text}"

