from typing import List, Dict, Any


def get_metrics_from_eval_file(eval_abs_path: str, needed_key: List[str] = None) -> Dict[str, Any]:
    metrics_dict = {}
    with open(eval_abs_path, 'r') as ner_eval_file:
        ner_eval_lines = ner_eval_file.readlines()
        for line in ner_eval_lines:
            pairs = line.strip("\r\n").strip("\n").split(" = ")
            metrics_dict[pairs[0]] = float(pairs[1])
    if needed_key is not None:
        result = {key: metrics_dict[key] for key in needed_key if key in metrics_dict}
    else:
        result = metrics_dict
    return result
