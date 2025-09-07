import openai
import os
import subprocess
import time
import requests
from contextlib import contextmanager
from typing import Dict, Any

# ==============================================================================
# КОНФИГУРАЦИЯ
# ==============================================================================
class Config:
    # Укажите путь ТОЛЬКО к исполняемому файлу KoboldCPP.
    KOBOLDCPP_EXECUTABLE_PATH = r"D:\\koboldcpp\\koboldcpp_cu12.exe" # <-- ИЗМЕНИТЕ ЭТО!
    
    # Укажите путь к файлу конфигурации, который мы создали.
    CONFIG_FILE_PATH = "consensus-translate\config.json"  # <-- ИЗМЕНЕНО С .ini НА .json

    # Параметры хоста и порта (должны совпадать с теми, что в config.json)
    HOST = "127.0.0.1"
    PORT = 5001

# ==============================================================================
# ФИНАЛЬНАЯ ВЕРСИЯ КОНТЕКСТНОГО МЕНЕДЖЕРА
# ==============================================================================
@contextmanager
def kobold_cpp_server():
    """
    Контекстный менеджер для запуска сервера KoboldCPP с использованием файла конфигурации.
    Это самый надежный метод.
    """
    server_process = None
    try:
        if not os.path.exists(Config.KOBOLDCPP_EXECUTABLE_PATH):
            raise FileNotFoundError(f"Исполняемый файл KoboldCPP не найден: {Config.KOBOLDCPP_EXECUTABLE_PATH}")
        if not os.path.exists(Config.CONFIG_FILE_PATH):
            raise FileNotFoundError(f"Файл конфигурации не найден: {Config.CONFIG_FILE_PATH}")

        # Формируем простую и надежную команду
        command = [
            Config.KOBOLDCPP_EXECUTABLE_PATH,
            "--config", Config.CONFIG_FILE_PATH,
        ]

        print("="*50)
        print("Запускаю сервер KoboldCPP с файлом конфигурации...")
        print(f"Команда: {' '.join(command)}")

        server_process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='replace')
        
        print("Ожидание готовности API сервера...")
        start_time = time.time()
        server_ready = False
        while time.time() - start_time < 300:
            if server_process.poll() is not None:
                print("\n[ОШИБКА]: Процесс KoboldCPP неожиданно завершился. Вывод:")
                print(server_process.stdout.read())
                raise RuntimeError("Не удалось запустить сервер KoboldCPP.")
            
            try:
                line = server_process.stdout.readline()
                if line:
                    print(f"[KoboldCPP]: {line.strip()}")
                
                response = requests.get(f"http://{Config.HOST}:{Config.PORT}/api/v1/model", timeout=2)
                if response.status_code == 200:
                    print("\nСервер KoboldCPP готов и отвечает.")
                    server_ready = True
                    break
            except requests.ConnectionError:
                time.sleep(1)
            except Exception:
                pass

        if not server_ready:
            raise RuntimeError("Сервер KoboldCPP не запустился в течение 120 секунд.")

        yield
        
    finally:
        if server_process:
            print("\nОстанавливаю сервер KoboldCPP...")
            server_process.terminate()
            try:
                server_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                print("Сервер не остановился, принудительное завершение.")
                server_process.kill()
            print("Сервер KoboldCPP остановлен.")
        print("="*50)

# ==============================================================================
# Основная логика перевода (ОСТАЕТСЯ БЕЗ ИЗМЕНЕНИЙ)
# ==============================================================================
# ... (вставьте сюда весь остальной код из предыдущих ответов:
# класс KoboldClient, функции strip_outer_brackets, consensus_translate
# и блок if __name__ == "__main__": )
# ...
KOBOLD_CPP_BASE_URL = f"http://{Config.HOST}:{Config.PORT}/v1" 
DUMMY_MODEL_NAME = "local-model" 
DUMMY_API_KEY = "unused"

class KoboldClient:
    def __init__(self, base_url: str, api_key: str):
        self.client = openai.OpenAI(base_url=base_url, api_key=api_key)
    def complete(self, system_prompt: str, user_prompt: str, temperature: float = 0.7) -> str:
        # ... (код без изменений)
        print(f"\n--- Запрос к KoboldCPP ---\nSYSTEM: {system_prompt}\nUSER: {user_prompt}\n--------------------------\n")
        chat_completion = self.client.chat.completions.create(
            model=DUMMY_MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature,
        )
        response_text = chat_completion.choices[0].message.content
        print(f"--- Ответ от KoboldCPP ---\n{response_text}\n--------------------------\n")
        return response_text

def strip_outer_brackets(s: str) -> str:
    return s.strip().strip('[]')

def consensus_translate(sentence: str, target_lang: str, source_lang: str = "English") -> Dict[str, Any]:
    # ... (код без изменений)
    kobold_client = KoboldClient(base_url=KOBOLD_CPP_BASE_URL, api_key=DUMMY_API_KEY)
    
    print("\n=============================================")
    print("=== ЭТАП 1: Генерация вариантов перевода ===")
    print("=============================================\n")
    
    translate_system_prompt = (
        f"Translate naturally idiomatically and accurately; "
        f"ONLY return the translation; JUST TRANSLATE THE TEXT INSIDE THE BRACKETS, NOTHING ELSE; "
        f"target {target_lang}\n"
        f"Source language: {source_lang};"
    )
    translate_user_prompt = f"[[[{sentence}]]]"

    translations = []
    for i in range(3):
        print(f"--- Запрос на перевод #{i+1} ---")
        translation_text = kobold_client.complete(
            system_prompt=translate_system_prompt,
            user_prompt=translate_user_prompt,
            temperature=0.8
        )
        translations.append(strip_outer_brackets(translation_text))

    if not translations:
        raise ValueError("Не удалось получить ни одного перевода от модели.")
        
    print("\nПолученные варианты перевода:")
    for i, t in enumerate(translations):
        print(f"{i+1}. {t}")

    print("\n=============================================")
    print("=== ЭТАП 2: Синтез и оценка переводов    ===")
    print("=============================================\n")

    eval_system_prompt = (
        f"You are an expert editor. Synthesize a new translation from {source_lang} to {target_lang} "
        f"by combining the strengths of the provided translations. Focus on idiomatic and natural phrasing. "
        f"First, provide a brief reasoning (1-2 sentences). Then, provide the final translation inside a Markdown code block."
    )
    translations_formatted = "\n".join(f"- \"{t}\"" for t in translations)
    eval_user_prompt = (
        f"Original text: \"{sentence}\"\n\n"
        f"Translations to synthesize:\n{translations_formatted}"
    )
    eval_response = kobold_client.complete(
        system_prompt=eval_system_prompt,
        user_prompt=eval_user_prompt,
        temperature=0.5
    )
    
    synthesized_translation = ""
    try:
        start = eval_response.find("```") + 3
        end = eval_response.rfind("```")
        if start != 2 and end != -1:
            synthesized_translation = eval_response[start:end].strip()
        else:
            synthesized_translation = eval_response
    except Exception:
        synthesized_translation = eval_response

    return {
        "initial_translations": translations,
        "final_translation": strip_outer_brackets(synthesized_translation)
    }

if __name__ == "__main__":
    text_to_translate = "The field of artificial intelligence is moving at a breakneck pace, with new breakthroughs announced almost weekly."
    target_language = "Russian"
    
    try:
        with kobold_cpp_server():
            final_result = consensus_translate(
                sentence=text_to_translate,
                target_lang=target_language,
            )
            
            print("\n\n================= ИТОГОВЫЙ РЕЗУЛЬТАТ =================")
            # ... (остальной код)
            print(f"Исходный текст: {text_to_translate}")
            print("-" * 50)
            print("Варианты, сгенерированные моделью:")
            for i, t in enumerate(final_result['initial_translations']):
                print(f"  {i+1}: {t}")
            print("-" * 50)
            print("Синтезированный (финальный) перевод:")
            print(f"  -> {final_result['final_translation']}")
            print("========================================================\n")

    except Exception as e:
        print(f"\nПроизошла критическая ошибка: {e}")