use crate::{languages::Language, TranslationSource};

// const GPT4O: &'static str = "openai/gpt-4o-2024-11-20";
// const GPT41: &'static str = "openai/gpt-4.1";
// const GEMINI_FLASH2_5: &'static str = "google/gemini-2.5-flash";
const LLAMA33_70B: &'static str = "meta-llama/llama-3.3-70b-instruct:free";
const LLAMA4MAV: &'static str = "meta-llama/llama-4-maverick:free";
const DEEPSEEKV3: &'static str = "deepseek/deepseek-chat-v3-0324:free";
const GLM45AIR: &'static str = "z-ai/glm-4.5-air:free";
const QWEN2_72B: &'static str = "qwen/qwen-2.5-72b-instruct:free";
// const QWEN3_14B: &'static str = "qwen/qwen3-14b:free";
// const SONNET4: &'static str = "anthropic/claude-sonnet-4";
// const OPUS4: &'static str = "anthropic/claude-opus-4";

const GEMMA3_27B: &'static str = "google/gemma-3-27b-it:free";
// const GROK3: &'static str = "x-ai/grok-3-beta";

pub struct SourceResponse {
    pub translate_sources: Vec<TranslationSource>,
    pub eval_source: TranslationSource,
}

pub fn get_appropriate_sources(target_lang: Language) -> SourceResponse {
    match target_lang {
        Language::Chinese | Language::ChineseTraditional => SourceResponse {
            translate_sources: vec![
                // TranslationSource::Openrouter(GPT4O),
                // TranslationSource::Openrouter(GPT41),
                // TranslationSource::Openrouter(GEMINI_FLASH2_5),
                TranslationSource::Openrouter(DEEPSEEKV3),
                // TranslationSource::Openrouter(GROK3),
            ],
            eval_source:  TranslationSource::Openrouter(GLM45AIR),
        },
        Language::Esperanto => SourceResponse {
            translate_sources: vec![
                // TranslationSource::Openrouter(GPT41),
                // TranslationSource::Openrouter(GPT4O),
                // TranslationSource::Openrouter(GROK3),
                // TranslationSource::Openrouter(GEMINI_FLASH2_5),
                TranslationSource::Openrouter(DEEPSEEKV3),
            ],
            eval_source:  TranslationSource::Openrouter(GLM45AIR),
        },
        Language::French => SourceResponse {
            translate_sources: vec![
                TranslationSource::Openrouter(LLAMA33_70B),
                TranslationSource::Openrouter(LLAMA4MAV),
                TranslationSource::Openrouter(DEEPSEEKV3),
                // TranslationSource::Openrouter(GEMINI_FLASH2_5),
                // TranslationSource::Openrouter(GPT41),
                // TranslationSource::Openrouter(GPT4O),
            ],
            eval_source:  TranslationSource::Openrouter(GLM45AIR),
        },
        Language::German => SourceResponse {
            translate_sources: vec![
                // TranslationSource::Openrouter(GPT4O),
                //TranslationSource::Openrouter(GEMMA3_27B),
                // TranslationSource::Openrouter(GROK3),
                TranslationSource::Openrouter(LLAMA4MAV),
                TranslationSource::Openrouter(DEEPSEEKV3),
                // TranslationSource::Openrouter(GEMINI_FLASH2_5),
            ],
            eval_source:  TranslationSource::Openrouter(GLM45AIR),
        },
        Language::Hungarian => SourceResponse {
            translate_sources: vec![
                // TranslationSource::Openrouter(GPT4O),
                // TranslationSource::Openrouter(SONNET4),
                // TranslationSource::Openrouter(GROK3),
                TranslationSource::Openrouter(LLAMA4MAV),
                TranslationSource::Openrouter(DEEPSEEKV3),
                // TranslationSource::Openrouter(GEMINI_FLASH2_5),
            ],
            eval_source:  TranslationSource::Openrouter(GLM45AIR),
        },
        Language::Italian => SourceResponse {
            translate_sources: vec![
                // TranslationSource::Openrouter(GPT41),
                // TranslationSource::Openrouter(GPT4O),
                //TranslationSource::Openrouter(GEMMA3_27B),
                TranslationSource::Openrouter(LLAMA4MAV),
                TranslationSource::Openrouter(DEEPSEEKV3),
                // TranslationSource::Openrouter(GEMINI_FLASH2_5),
            ],
            eval_source:  TranslationSource::Openrouter(GLM45AIR),
        },
        Language::Japanese => SourceResponse {
            translate_sources: vec![
                // TranslationSource::Openrouter(GPT41),
                // TranslationSource::Openrouter(SONNET4),
                //// TranslationSource::Openrouter(GROK3),
                //TranslationSource::Openrouter(LLAMA4MAV),
                TranslationSource::Openrouter(DEEPSEEKV3),
                // TranslationSource::Openrouter(GEMINI_FLASH2_5),
            ],
            eval_source:  TranslationSource::Openrouter(GLM45AIR),
        },
        Language::Korean => SourceResponse {
            translate_sources: vec![
                // TranslationSource::Openrouter(GPT41),
                // TranslationSource::Openrouter(SONNET4),
                //TranslationSource::Openrouter(GEMMA3_27B),
                // TranslationSource::Openrouter(GROK3),
                TranslationSource::Openrouter(DEEPSEEKV3),
            ],
            eval_source:  TranslationSource::Openrouter(GLM45AIR),
        },
        Language::Spanish => SourceResponse {
            translate_sources: vec![
                // TranslationSource::Openrouter(SONNET4),
                // TranslationSource::Openrouter(GPT4O),
                TranslationSource::Openrouter(LLAMA4MAV),
                TranslationSource::Openrouter(DEEPSEEKV3),
                // TranslationSource::Openrouter(GEMINI_FLASH2_5),
            ],
            eval_source:  TranslationSource::Openrouter(GLM45AIR),
        },
        Language::Swedish => SourceResponse {
            translate_sources: vec![
                TranslationSource::Openrouter(LLAMA33_70B),
                // TranslationSource::Openrouter(GPT4O),
                // TranslationSource::Openrouter(GPT41),
                // TranslationSource::Openrouter(GROK3),
                TranslationSource::Openrouter(DEEPSEEKV3),
            ],
            eval_source:  TranslationSource::Openrouter(GLM45AIR),
        },
        Language::Ukrainian => SourceResponse {
            translate_sources: vec![
                // TranslationSource::Openrouter(GPT41),
                // TranslationSource::Openrouter(GEMINI_FLASH2_5),
                // TranslationSource::Openrouter(GPT4O),
                // TranslationSource::Openrouter(GROK3),
            ],
            eval_source:  TranslationSource::Openrouter(GLM45AIR),
        },
        Language::Vietnamese => SourceResponse {
            translate_sources: vec![
                // TranslationSource::Openrouter(GPT41),
                //TranslationSource::Openrouter(GEMMA3_27B),
                // TranslationSource::Openrouter(GPT4O),
                // TranslationSource::Openrouter(GROK3),
                TranslationSource::Openrouter(DEEPSEEKV3),
            ],
            eval_source:  TranslationSource::Openrouter(GLM45AIR),
        },
        Language::Welsh | Language::Thai | Language::Klingon => SourceResponse {
            translate_sources: vec![
                 TranslationSource::Openrouter(GLM45AIR),
                // TranslationSource::Openrouter(SONNET4),
                // TranslationSource::Openrouter(GPT4O),
                // TranslationSource::Openrouter(GROK3),
            ],
            eval_source:  TranslationSource::Openrouter(GLM45AIR),
        },
        Language::Unknown | _ => SourceResponse {
            translate_sources: vec![
                // TranslationSource::Openrouter(GEMMA3_27B),
                // TranslationSource::Openrouter(SONNET4),
                // TranslationSource::Openrouter(GPT41),
                TranslationSource::Openrouter(LLAMA4MAV),
                TranslationSource::Openrouter(GLM45AIR),
                // // TranslationSource::Openrouter(GEMINI_FLASH2_5),
                // TranslationSource::Openrouter(GEMMA3_27B),
                TranslationSource::Openrouter(LLAMA33_70B),
                TranslationSource::Openrouter(QWEN2_72B),
                // TranslationSource::Openrouter(QWEN3_14B),
            ],
            eval_source: TranslationSource::Openrouter(DEEPSEEKV3),
        },
    }
}
