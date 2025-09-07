use reqwest::Client;
use serde::{Deserialize, Serialize};
use std::error::Error;
use tracing::{debug, error, info, warn};

#[derive(Serialize)]
struct ChatRequest {
    model: String,
    messages: Vec<Message>,
    temperature: f32,
    #[serde(skip_serializing_if = "Option::is_none")]
    max_tokens: Option<u32>,  // Добавляем поле max_tokens
}

#[derive(Serialize)]
struct Message {
    role: String,
    content: String,
}

#[derive(Deserialize)]
struct ChatResponse {
    #[serde(default)]
    choices: Vec<Choice>,
    #[serde(default)]
    usage: Option<Usage>,
}

#[derive(Deserialize)]
struct Choice {
    message: MessageResponse,
}

#[derive(Deserialize)]
struct MessageResponse {
    content: String,
}

#[derive(Deserialize)]
struct Usage {
    prompt_tokens: u32,
    completion_tokens: u32,
}

#[derive(Deserialize)]
struct ErrorResponse {
    error: ErrorDetails,
    #[serde(default)]
    user_id: Option<String>,  // Добавляем поле user_id
}

#[derive(Deserialize)]
struct ErrorDetails {
    message: String,
    #[serde(rename = "type")]
    #[serde(default)]  // Делаем поле опциональным с значением по умолчанию
    error_type: Option<String>,  // Теперь это Option
    code: Option<i32>,
    #[serde(default)]
    metadata: Option<serde_json::Value>,  // Добавляем поле metadata
}

pub struct OpenRouterClient {
    api_key: String,
    base_url: String,
    client: Client,
}

impl OpenRouterClient {
    pub fn new(api_key: &str) -> Self {
        Self {
            api_key: api_key.to_string(),
            base_url: "https://openrouter.ai/api/v1".to_string(),
            client: Client::new(),
        }
    }

    fn calculate_cost(model: &str, prompt_tokens: u32, completion_tokens: u32) -> f64 {
        let (input_price_per_million, output_price_per_million) = match model {
            "openai/gpt-4o-2024-11-20" => (2.5, 10.0),
            "openai/gpt-4.1" => (2.0, 8.0),
            "google/gemini-2.5-flash" => (0.3, 2.5),
            "meta-llama/llama-3.3-70b-instruct" => (0.1, 0.25),
            "meta-llama/llama-4-maverick" => (0.15, 0.6),
            "deepseek/deepseek-chat-v3-0324:free" => (0.3, 0.88),
            "anthropic/claude-sonnet-4" => (3.0, 15.0),
            "anthropic/claude-opus-4" => (15.0, 75.0),
            "google/gemma-3-27b-it" => (0.1, 0.2),
            "x-ai/grok-3-beta" => (3.0, 15.0),
            _ => {
                warn!("Unknown model '{}', defaulting to zero cost", model);
                (0.0, 0.0)
            }
        };
        let input_cost = (prompt_tokens as f64 * input_price_per_million) / 1_000_000.0;
        let output_cost = (completion_tokens as f64 * output_price_per_million) / 1_000_000.0;
        input_cost + output_cost
    }

    pub async fn complete(
        &self,
        system_prompt: &str,
        main_prompt: &str,
        model: &str,
        temperature: f32,
    ) -> Result<(String, f64), Box<dyn Error>> {
        let url = format!("{}/chat/completions", self.base_url);
        
        // Устанавливаем разумный лимит токенов для перевода
        // Для перевода обычно достаточно 500-1000 токенов
        let max_tokens = Some(5000);
        
        let request_body = ChatRequest {
            model: model.to_string(),
            messages: vec![
                Message {
                    role: "system".to_string(),
                    content: system_prompt.to_string(),
                },
                Message {
                    role: "user".to_string(),
                    content: main_prompt.to_string(),
                },
            ],
            temperature,
            max_tokens,  // Устанавливаем лимит токенов
        };
        
        debug!(
            "Sending request to OpenRouter: url={}, model={}, max_tokens={:?}",
            url, model, max_tokens
        );

        let response = self
            .client
            .post(&url)
            .header("Authorization", format!("Bearer {}", self.api_key))
            .json(&request_body)
            .send()
            .await?;

        let status = response.status();
        debug!("Received response with status: {}", status);

        let raw_body = response.text().await?;
        debug!("Raw response body: {}", raw_body);

        if !status.is_success() {
            // Пытаемся распарсить ошибку
            match serde_json::from_str::<ErrorResponse>(&raw_body) {
                Ok(error_response) => {
                    let error_type = error_response.error.error_type.as_deref().unwrap_or("unknown");
                    let code = error_response.error.code;
                    
                    // Специальная обработка для ошибки недостатка кредитов
                    if code == Some(402) {
                        error!(
                            "Insufficient credits for model {}: {}",
                            model, error_response.error.message
                        );
                        return Err(format!(
                            "Insufficient credits: {}. Please add credits at https://openrouter.ai/settings/credits",
                            error_response.error.message
                        )
                        .into());
                    }
                    
                    warn!(
                        "OpenRouter error: status={}, message='{}', type='{}', code={:?}",
                        status,
                        error_response.error.message,
                        error_type,
                        code
                    );
                    
                    return Err(format!(
                        "OpenRouter API error: {} (status: {}, type: {})",
                        error_response.error.message, status, error_type
                    )
                    .into());
                }
                Err(e) => {
                    error!(
                        "Failed to parse error response: {}, raw_body: {}",
                        e, raw_body
                    );
                    return Err(format!("API error (status: {}): {}", status, raw_body).into());
                }
            }
        }

        let chat_response: ChatResponse = serde_json::from_str(&raw_body).map_err(|e| {
            error!(
                "Failed to parse ChatResponse: {}, raw_body: {}",
                e, raw_body
            );
            format!("Error decoding response body: {}", e)
        })?;

        if chat_response.choices.is_empty() {
            error!("No choices in response: {}", raw_body);
            return Err("No choices returned from OpenRouter API".into());
        }

        let (prompt_tokens, completion_tokens) = chat_response
            .usage
            .as_ref()
            .map(|u| (u.prompt_tokens, u.completion_tokens))
            .unwrap_or_else(|| {
                warn!("No usage data in response, defaulting tokens to 0");
                (0, 0)
            });

        let cost = Self::calculate_cost(model, prompt_tokens, completion_tokens);

        Ok((chat_response.choices[0].message.content.clone(), cost))
    }
}