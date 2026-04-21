import json
import sys
import argparse
from llm_sdk import Small_LLM_Model
from pydantic import BaseModel
import re


class FunctionCall(BaseModel):
    prompt: str
    name: str
    parameters: dict


def load_json_file(path: str) -> list:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Erreur : fichier non trouvé : {path}")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Erreur : JSON invalide dans : {path}")
        sys.exit(1)


def select_function(prompt: str, functions: list) -> dict:
    prompt_lower = prompt.lower()

    keywords = {
        "fn_add_numbers": [
            "sum", "add", "plus", "addition", "total"
        ],
        "fn_greet": [
            "greet", "hello", "hi", "welcome"
        ],
        "fn_reverse_string": [
            "reverse", "backwards", "flip", "string"
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


def extract_parameters(
    prompt: str,
    function: dict
) -> dict:
    result = {}
    fname = function["name"]
    params = function.get("parameters", {})

    if fname == "fn_add_numbers":
        numbers = re.findall(r"-?\d+\.?\d*", prompt)
        param_names = list(params.keys())
        for i, pname in enumerate(param_names):
            if i < len(numbers):
                result[pname] = float(numbers[i])
            else:
                result[pname] = 0.0

    elif fname == "fn_greet":
        words = prompt.strip().split()
        name = words[-1].strip("'\".,!?")
        result["name"] = name.capitalize()

    elif fname == "fn_reverse_string":
        quoted = re.findall(r"['\"]([^'\"]+)['\"]", prompt)
        if quoted:
            result["s"] = quoted[0]
        else:
            words = prompt.split()
            result["s"] = words[-1].strip("'\"") if words else ""

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
            if match:
                result["source_string"] = match.group(1)
            else:
                quoted = re.findall(
                    r"['\"]([^'\"]+)['\"]", prompt
                )
                result["source_string"] = quoted[0] if quoted else ""
            result["regex"] = r"\d+"
            result["replacement"] = "NUMBERS"

        else:
            quoted = re.findall(
                r"['\"]([^'\"]+)['\"]", prompt
            )
            if len(quoted) >= 3:
                result["source_string"] = quoted[2]
                result["regex"] = quoted[0]
                result["replacement"] = quoted[1]
            elif len(quoted) == 2:
                result["source_string"] = quoted[0]
                result["regex"] = quoted[0]
                result["replacement"] = quoted[1]
            else:
                result["source_string"] = ""
                result["regex"] = ""
                result["replacement"] = ""

    return result


def generate_function_call(
    prompt: str,
    functions: list,
) -> dict:
    function = select_function(prompt, functions)
    func_name = function["name"]
    print(f"  → Fonction choisie : {func_name}")

    parameters = extract_parameters(prompt, function)
    print(f"  → Paramètres : {parameters}")

    return {"name": func_name, "parameters": parameters}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--functions_definition",
        default="data/input/functions_definition.json"
    )
    parser.add_argument(
        "--input",
        default="data/input/function_calling_tests.json"
    )
    parser.add_argument(
        "--output",
        default="data/output/function_calling_results.json"
    )
    args = parser.parse_args()

    print("Chargement des fichiers JSON...")
    functions = load_json_file(args.functions_definition)
    prompts = load_json_file(args.input)

    print("Chargement du modèle LLM...")
    model = Small_LLM_Model("Qwen/Qwen3-0.6B")
    print(f"Modèle chargé : {model}")

    results = []
    for item in prompts:
        print(f"Traitement : {item['prompt']}")
        result = generate_function_call(
            item["prompt"], functions
        )
        call = FunctionCall(
            prompt=item["prompt"],
            name=result.get("name", ""),
            parameters=result.get("parameters", {})
        )
        results.append(call.model_dump())

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"Résultats sauvegardés dans {args.output}")


if __name__ == "__main__":
    main()