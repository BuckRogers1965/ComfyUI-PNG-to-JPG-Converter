import os
import json
import argparse
import math
import copy # For deep copying workflows

# --- Helper functions (from your previous script, unchanged) ---
def normalize_workflow_seeds(workflow):
    """
    Recursively removes or normalizes seed values and common transient/control elements
    in a ComfyUI workflow for comparison purposes.
    """
    if isinstance(workflow, dict):
        seed_keys = ['seed', 'noise_seed']
        control_keys_to_normalize = ['control_after_generate', 'control_before_generate']
        
        for key in seed_keys:
            if key in workflow and isinstance(workflow[key], (int, float)):
                workflow[key] = 0
        
        for key in control_keys_to_normalize:
            if key in workflow and isinstance(workflow[key], str):
                workflow[key] = "fixed"
        
        if 'widgets_values' in workflow and isinstance(workflow['widgets_values'], list):
            widgets = workflow['widgets_values']
            for i, value in enumerate(widgets):
                if isinstance(value, int) and value > -1:
                    if i + 1 < len(widgets) and isinstance(widgets[i + 1], str) and widgets[i + 1].lower() in ['randomize', 'increment', 'decrement', 'fixed']:
                        widgets[i] = 0
                        widgets[i+1] = "fixed"
                elif isinstance(value, str) and value.lower() in ['randomize', 'increment', 'decrement', 'fixed']:
                    widgets[i] = "fixed"

        if 'inputs' in workflow and isinstance(workflow['inputs'], dict):
            normalize_workflow_seeds(workflow['inputs'])
        
        for key, value in workflow.items():
            if key in ["last_node_id", "last_link_id", "version", "date", "time", "_meta_data_checksum"]:
                continue
            if isinstance(value, (dict, list)):
                normalize_workflow_seeds(value)
    
    elif isinstance(workflow, list):
        for item in workflow:
            normalize_workflow_seeds(item)

def flatten_json_to_paths(obj, path=''):
    """
    Flattens a JSON object into a list of (path, value) tuples.
    Treats lists by index and dictionaries by key.
    """
    paths = []
    if isinstance(obj, dict):
        for k, v in sorted(obj.items()):
            new_path = f"{path}.{k}" if path else k
            if isinstance(v, (dict, list)):
                paths.extend(flatten_json_to_paths(v, new_path))
            else:
                paths.append((new_path, v))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            new_path = f"{path}[{i}]"
            if isinstance(v, (dict, list)):
                paths.extend(flatten_json_to_paths(v, new_path))
            else:
                paths.append((new_path, v))
    return paths

def calculate_json_difference_percentage(json1_data, json2_data):
    """
    Calculates a structural difference percentage between two JSON objects,
    ignoring seed values.
    Returns the percentage difference.
    """
    normalized_json1 = copy.deepcopy(json1_data)
    normalized_json2 = copy.deepcopy(json2_data)
    normalize_workflow_seeds(normalized_json1)
    normalize_workflow_seeds(normalized_json2)

    paths1 = set(flatten_json_to_paths(normalized_json1))
    paths2 = set(flatten_json_to_paths(normalized_json2))

    common_paths = paths1.intersection(paths2)
    unique_to_1 = paths1 - paths2
    unique_to_2 = paths2 - paths1

    total_elements_in_union = len(paths1.union(paths2))
    
    if total_elements_in_union == 0:
        # If both are empty or normalized to empty, they are 0% different
        return 0.0 
    
    difference_count = len(unique_to_1) + len(unique_to_2)
    
    percentage_diff = (difference_count / total_elements_in_union) * 100
    
    return percentage_diff

# --- Main Script Logic ---
def compare_and_delete_jsons(
    source_dir: str,
    delete_threshold_percent: float = None # No change here
) -> None:
    """
    Compares consecutive JSON files in a directory (sorted alphabetically by filename).
    Calculates percentage difference and optionally deletes files below a threshold.

    Args:
        source_dir (str): The root directory containing JSON files.
        delete_threshold_percent (float, optional): If provided, JSON files whose
                                                    difference % to the previous is
                                                    LESS than this value will be deleted.
                                                    Set to 0 to delete exact duplicates (ignoring seeds).
    """
    if not os.path.isdir(source_dir):
        print(f"Error: Source directory '{source_dir}' does not exist.")
        return

    json_files = sorted([f for f in os.listdir(source_dir) if f.lower().endswith('.json') and not f.startswith('._')])

    if not json_files:
        print(f"No JSON files found in '{source_dir}'.")
        return

    # Determine if we are in "deletion mode"
    is_deletion_mode = delete_threshold_percent is not None

    print(f"Comparing JSON files in '{source_dir}' (Delete Threshold: {delete_threshold_percent if is_deletion_mode else 'None'})...")
    print("-" * 50)

    previous_json_data = None
    previous_json_filename = None
    deleted_count = 0
    total_compared = 0

    for i, filename in enumerate(json_files):
        current_json_path = os.path.join(source_dir, filename)
        current_json_data = None

        try:
            with open(current_json_path, 'r', encoding='utf-8') as f:
                current_json_data = json.load(f)
        except json.JSONDecodeError as e:
            print(f"Error: Could not parse '{filename}' (Invalid JSON): {e}. Skipping.")
            continue
        except FileNotFoundError:
            print(f"Error: File '{filename}' not found (might have been deleted by another process). Skipping.")
            continue
        except Exception as e:
            print(f"An unexpected error occurred while reading '{filename}': {e}. Skipping.")
            continue

        if previous_json_data is None:
            print(f"  {filename}: (Initial file, kept by default)")
            previous_json_data = current_json_data
            previous_json_filename = filename
            continue

        total_compared += 1
        percentage_diff = calculate_json_difference_percentage(current_json_data, previous_json_data)

        action = "KEPT" # Default action
        
        # Check for deletion condition
        if is_deletion_mode and percentage_diff < delete_threshold_percent:
            try:
                os.remove(current_json_path)
                deleted_count += 1
                action = "DELETED"
            except OSError as e:
                action = f"DELETE_ERROR ({e})"
        
        # --- ALWAYS PRINT A LINE FOR EVERY FILE ---
        print(f"  {filename} vs {previous_json_filename}: Diff {percentage_diff:.2f}% - {action}")
        
        # Only update previous_json_data if the current file was KEPT.
        # This ensures we compare against the *last kept* unique workflow.
        if action == "KEPT":
            previous_json_data = current_json_data
            previous_json_filename = filename

    print("-" * 50)
    print("Comparison Summary:")
    print(f"  Total JSON files processed: {len(json_files)}")
    print(f"  Files compared: {total_compared}")
    if is_deletion_mode:
        print(f"  Files deleted (diff < {delete_threshold_percent:.2f}%): {deleted_count}")
    print("Comparison complete.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Compares consecutive JSON files (e.g., ComfyUI workflows) and optionally deletes those below a similarity threshold."
    )
    parser.add_argument(
        "source_directory",
        type=str,
        help="The directory containing the JSON files to compare and potentially delete."
    )
    parser.add_argument(
        "-d", "--delete-threshold",
        type=float,
        metavar="PERCENT",
        help="If specified, JSON files with a percentage difference LESS than this value (e.g., 5.3) compared to the previous kept file will be deleted. Set to 0 to delete exact duplicates (ignoring seeds)."
    )

    args = parser.parse_args()

    compare_and_delete_jsons(
        source_dir=args.source_directory,
        delete_threshold_percent=args.delete_threshold
    )
