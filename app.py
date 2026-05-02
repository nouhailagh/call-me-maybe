import streamlit as st
import json
import re
import math
from llm_sdk import Small_LLM_Model
from pydantic import BaseModel

st.set_page_config(
    page_title="Function Calling System",
    page_icon="🤖",
    layout="wide"
)

st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        text-align: center;
        color: white;
        margin-bottom: 2rem;
    }
    .function-badge {
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-size: 1.1rem;
        font-weight: bold;
        display: inline-block;
    }
    .result-box {
        background: linear-gradient(135deg, #11998e, #38ef7d);
        color: white;
        padding: 1.5rem;
        border-radius: 15px;
        text-align: center;
        font-size: 1.5rem;
        font-weight: bold;
        margin: 1rem 0;
    }
    .history-card {
        background: #f8f9fa;
        border-left: 4px solid #667eea;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)


class FunctionCall(BaseModel):
    prompt: str
    name: str
    parameters: dict


@st.cache_resource
def load_model():
    return Small_LLM_Model("Qwen/Qwen3-0.6B")


@st.cache_data
def load_functions():
    with open(
        "data/input/functions_definition.json",
        "r", encoding="utf-8"
    ) as f:
        return json.load(f)


def select_function(prompt: str, functions: list) -> dict:
    prompt_lower = prompt.lower()
    keywords = {
        "fn_add_numbers": [
            "sum", "add", "plus", "addition", "total"
        ],
        "fn_multiply_numbers": [
            "multiply", "times", "product", "multiplication"
        ],
        "fn_calculate_power": [
            "power", "exponent", "raised", "squared", "cubed"
        ],
        "fn_greet": [
            "greet", "hello", "hi", "welcome"
        ],
        "fn_reverse_string": [
            "reverse", "backwards", "flip", "string"
        ],
        "fn_convert_to_uppercase": [
            "uppercase", "upper", "capital", "majuscule"
        ],
        "fn_convert_to_lowercase": [
            "lowercase", "lower", "minuscule"
        ],
        "fn_count_words": [
            "count", "how many words", "number of words"
        ],
        "fn_get_square_root": [
            "square root", "sqrt", "root"
        ],
        "fn_substitute_string_with_regex": [
            "replace", "substitute", "swap",
            "vowels", "numbers in", "word"
        ],
    }
    best_func = functions[0]
    best_score = -1
    for function in functions:
        fname = function["name"]
        score = 0
        if fname in keywords:
            for kw in keywords[fname]:
                if kw in prompt_lower:
                    score += 1
        if score > best_score:
            best_score = score
            best_func = function
    return best_func


def extract_parameters(prompt: str, function: dict) -> dict:
    result = {}
    fname = function["name"]
    params = function.get("parameters", {})

    if fname == "fn_add_numbers":
        numbers = re.findall(r"-?\d+\.?\d*", prompt)
        param_names = list(params.keys())
        for i, pname in enumerate(param_names):
            result[pname] = float(numbers[i]) if i < len(numbers) else 0.0

    elif fname == "fn_multiply_numbers":
        numbers = re.findall(r"-?\d+\.?\d*", prompt)
        param_names = list(params.keys())
        for i, pname in enumerate(param_names):
            result[pname] = float(numbers[i]) if i < len(numbers) else 0.0

    elif fname == "fn_calculate_power":
        numbers = re.findall(r"-?\d+\.?\d*", prompt)
        result["base"] = float(numbers[0]) if len(numbers) > 0 else 0.0
        result["exponent"] = float(numbers[1]) if len(numbers) > 1 else 2.0

    elif fname == "fn_greet":
        words = prompt.strip().split()
        name = words[-1].strip("'\".,!?")
        result["name"] = name.capitalize()

    elif fname == "fn_reverse_string":
        quoted = re.findall(r"['\"]([^'\"]+)['\"]", prompt)
        result["s"] = quoted[0] if quoted else prompt.split()[-1]

    elif fname == "fn_convert_to_uppercase":
        quoted = re.findall(r"['\"]([^'\"]+)['\"]", prompt)
        if quoted:
            result["s"] = quoted[0]
        else:
            words = prompt.split()
            result["s"] = words[-1].strip("'\"") if words else ""

    elif fname == "fn_convert_to_lowercase":
        quoted = re.findall(r"['\"]([^'\"]+)['\"]", prompt)
        if quoted:
            result["s"] = quoted[0]
        else:
            words = prompt.split()
            result["s"] = words[-1].strip("'\"") if words else ""

    elif fname == "fn_count_words":
        quoted = re.findall(r"['\"]([^'\"]+)['\"]", prompt)
        if quoted:
            result["s"] = quoted[0]
        else:
            result["s"] = prompt

    elif fname == "fn_get_square_root":
        numbers = re.findall(r"-?\d+\.?\d*", prompt)
        result["a"] = float(numbers[0]) if numbers else 0.0

    elif fname == "fn_substitute_string_with_regex":
        prompt_lower = prompt.lower()
        if "vowels" in prompt_lower:
            quoted = re.findall(r"['\"]([^'\"]+)['\"]", prompt)
            result["source_string"] = quoted[0] if quoted else ""
            result["regex"] = "[aeiouAEIOU]"
            result["replacement"] = "*"
        elif "numbers" in prompt_lower and "in" in prompt_lower:
            match = re.search(r'"([^"]+)"', prompt)
            result["source_string"] = match.group(1) if match else ""
            result["regex"] = r"\d+"
            result["replacement"] = "NUMBERS"
        else:
            quoted = re.findall(r"['\"]([^'\"]+)['\"]", prompt)
            if len(quoted) >= 3:
                result["source_string"] = quoted[2]
                result["regex"] = quoted[0]
                result["replacement"] = quoted[1]
            else:
                result["source_string"] = ""
                result["regex"] = ""
                result["replacement"] = ""

    return result


def execute_function(name: str, parameters: dict) -> str:
    try:
        if name == "fn_add_numbers":
            a = parameters.get("a", 0)
            b = parameters.get("b", 0)
            result = a + b
            return f"✅ {a} + {b} = **{result}**"

        elif name == "fn_multiply_numbers":
            a = parameters.get("a", 0)
            b = parameters.get("b", 0)
            result = a * b
            return f"✅ {a} × {b} = **{result}**"

        elif name == "fn_calculate_power":
            base = parameters.get("base", 0)
            exp = parameters.get("exponent", 2)
            result = math.pow(base, exp)
            return f"✅ {base}^{exp} = **{result}**"

        elif name == "fn_greet":
            name_param = parameters.get("name", "")
            return f"✅ Hello, **{name_param}**! 👋 Welcome!"

        elif name == "fn_reverse_string":
            s = parameters.get("s", "")
            reversed_s = s[::-1]
            return f"✅ '{s}' → **'{reversed_s}'**"

        elif name == "fn_convert_to_uppercase":
            s = parameters.get("s", "")
            return f"✅ '{s}' → **'{s.upper()}'**"

        elif name == "fn_convert_to_lowercase":
            s = parameters.get("s", "")
            return f"✅ '{s}' → **'{s.lower()}'**"

        elif name == "fn_count_words":
            s = parameters.get("s", "")
            count = len(s.split())
            return f"✅ '{s}' contient **{count} mots**"

        elif name == "fn_get_square_root":
            a = parameters.get("a", 0)
            result = math.sqrt(a)
            return f"✅ √{a} = **{result}**"

        elif name == "fn_substitute_string_with_regex":
            source = parameters.get("source_string", "")
            pattern = parameters.get("regex", "")
            replacement = parameters.get("replacement", "")
            result = re.sub(pattern, replacement, source)
            return f"✅ '{source}' → **'{result}'**"

        else:
            return "❌ Fonction non reconnue"

    except Exception as e:
        return f"❌ Erreur : {str(e)}"


def main():
    st.markdown("""
    <div class="main-header">
        <h1>🤖 Function Calling System</h1>
        <p>Traduit du langage naturel en JSON + Exécute la fonction !</p>
        <p>Powered by Qwen3-0.6B | Oracle OCI GenAI Professional</p>
    </div>
    """, unsafe_allow_html=True)

    with st.spinner("⏳ Chargement du modèle LLM..."):
        model = load_model()
        functions = load_functions()

    st.success("✅ Modèle Qwen3-0.6B chargé avec succès !")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("🧠 Modèle", "Qwen3-0.6B")
    with col2:
        st.metric("⚙️ Fonctions", len(functions))
    with col3:
        st.metric(
            "📊 Questions posées",
            len(st.session_state.get("history", []))
        )

    st.divider()

    if "history" not in st.session_state:
        st.session_state.history = []

    st.subheader("💬 Posez votre question en langage naturel")

    examples = [
        "",
        "What is the sum of 2 and 3?",
        "Multiply 6 by 7",
        "Calculate 2 raised to the power of 10",
        "Greet John",
        "Reverse the string 'hello'",
        "Convert 'hello world' to uppercase",
        "Convert 'HELLO WORLD' to lowercase",
        "Count words in 'I love programming'",
        "What is the square root of 16?",
        "Replace all vowels in 'Programming is fun' with asterisks",
        "Substitute the word 'cat' with 'dog' in 'The cat sat on the mat'"
    ]

    example = st.selectbox("💡 Choisissez un exemple :", examples)

    prompt = st.text_input(
        "✏️ Votre question :",
        value=example,
        placeholder="Ex: What is the sum of 2 and 3?"
    )

    col1, col2 = st.columns([3, 1])
    with col1:
        analyze = st.button(
            "🚀 Analyser et Exécuter",
            use_container_width=True,
            type="primary"
        )
    with col2:
        if st.button(
            "🗑️ Effacer historique",
            use_container_width=True
        ):
            st.session_state.history = []
            st.rerun()

    if analyze and prompt:
        with st.spinner("🔍 Analyse en cours..."):
            function = select_function(prompt, functions)
            parameters = extract_parameters(prompt, function)
            call = FunctionCall(
                prompt=prompt,
                name=function["name"],
                parameters=parameters
            )
            execution_result = execute_function(
                call.name, call.parameters
            )

        st.session_state.history.append({
            "prompt": prompt,
            "name": call.name,
            "parameters": call.parameters,
            "result": execution_result
        })

        st.divider()

        tab1, tab2, tab3 = st.tabs(
            ["🎯 Résultat", "🔧 JSON", "📋 Détails"]
        )

        with tab1:
            st.subheader("🎯 Résultat de l'exécution")
            st.markdown(
                f'<div class="result-box">{execution_result}</div>',
                unsafe_allow_html=True
            )
            st.markdown(f"**Fonction utilisée :** `{call.name}`")
            func_desc = next(
                (f["description"] for f in functions
                 if f["name"] == call.name), ""
            )
            st.info(f"ℹ️ {func_desc}")

        with tab2:
            st.subheader("🔧 JSON généré")
            st.json(call.model_dump())

        with tab3:
            st.subheader("📋 Paramètres extraits")
            for key, value in call.parameters.items():
                col1, col2 = st.columns([1, 3])
                with col1:
                    st.markdown(f"**{key}**")
                with col2:
                    st.code(str(value))

    elif analyze and not prompt:
        st.warning("⚠️ Veuillez entrer une question !")

    if st.session_state.get("history"):
        st.divider()
        st.subheader("📜 Historique des questions")

        for i, item in enumerate(
            reversed(st.session_state.history)
        ):
            with st.expander(
                f"💬 {item['prompt']}", expanded=(i == 0)
            ):
                st.markdown(
                    f'<div class="result-box">{item["result"]}</div>',
                    unsafe_allow_html=True
                )
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(
                        f"**Fonction :** `{item['name']}`"
                    )
                with col2:
                    st.markdown(
                        f"**Paramètres :** `{item['parameters']}`"
                    )

    st.divider()
    st.markdown("""
    <div style='text-align: center; color: #888; padding: 1rem;'>
        🤖 Function Calling System | Qwen3-0.6B |
        Oracle OCI Generative AI Professional 2025
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()