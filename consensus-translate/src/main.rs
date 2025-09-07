use consensus_translate::{Language, TranslationStyle, TranslationType};
use std::env;
use tokio::fs;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    tracing_subscriber::fmt::init();


    let key = "OPENROUTER_API_KEY";
    std::env::set_var(key, "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"); // Sets AAA to 123
    
    let openrouter_api_key = env::var("OPENROUTER_API_KEY")
        .expect("Не установлена переменная окружения OPENROUTER_API_KEY");

    // Путь к файлу: из аргумента или по умолчанию input.txt
    let file_path = env::args().nth(1).unwrap_or_else(|| "input.txt".to_string());

    // Читаем файл асинхронно
    let text_to_translate = fs::read_to_string(&file_path).await?;

    let target_language = Language::Russian;
    let source_language = Some(Language::English);
    let translation_type = TranslationType::Eloquent;
    let translation_style = TranslationStyle::Formal;
    let enable_sensitive_logs = true;

    println!("Переводим текст из файла '{}'", file_path);

    match consensus_translate::consensus_translate(
        text_to_translate,
        target_language,
        translation_type,
        translation_style,
        source_language,
        openrouter_api_key,
        enable_sensitive_logs,
    )
    .await
    {
        Ok(response) => {
            println!("\n--- Результаты перевода ---");
            for item in response.translations {
                if item.combined {
                    println!("\n[Синтезированный перевод (модель: {})]", item.model);
                    println!("Текст: {}", item.text);
                } else {
                    println!("\n[Перевод от модели: {}]", item.model);
                    println!("Текст: {}", item.text);
                    if let Some(duration) = item.duration_ms {
                        println!("Время выполнения: {} мс", duration);
                    }
                }
            }
            println!(
                "\nОбщая стоимость: {} (тысячных долей цента)",
                response.total_cost_thousandths_cent
            );
        }
        Err(e) => {
            eprintln!("\n--- Произошла ошибка ---");
            eprintln!("{}", e);
        }
    }

    Ok(())
}