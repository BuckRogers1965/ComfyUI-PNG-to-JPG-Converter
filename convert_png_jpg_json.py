import os
import subprocess
import argparse
import json
from PIL import Image

def convert_png_to_jpg_with_json(
    source_dir: str,
    quality: int = 85,
    delete_original: bool = False,
    clean_mac_files: bool = False,
    verbose: bool = False,
    silent: bool = False
) -> None:
    """
    Recursively walks a directory tree, converts PNG files to JPG with specified quality,
    and saves ComfyUI workflow metadata as a separate JSON file next to the JPG.
    Reports space saved if original PNGs are deleted. Optionally cleans up macOS '._' files.

    Args:
        source_dir (str): The root directory to start the traversal.
        quality (int): The JPEG compression quality (0-100). Default is 85.
        delete_original (bool): If True, deletes the original PNG file after successful conversion.
        clean_mac_files (bool): If True, deletes files starting with '._' found in the tree.
        verbose (bool): If True, prints detailed progress messages.
        silent (bool): If True, suppresses all output except errors and final summary.
    """
    if not os.path.isdir(source_dir):
        print(f"Error: Source directory '{source_dir}' does not exist.")
        return

    converted_count = 0
    skipped_count = 0
    error_count = 0
    json_created_count = 0
    total_space_saved_bytes = 0
    mac_files_deleted_count = 0
    mac_files_deleted_size_bytes = 0

    if not silent:
        print(f"Starting conversion in '{source_dir}' (Quality: {quality}%, Delete Original: {delete_original}, Clean Mac Files: {clean_mac_files})...")
        print("-" * 50)

    for root, dirs, files in os.walk(source_dir):
        if verbose:
            print(f"Entering directory: {root}")

        if clean_mac_files:
            for filename in files:
                if filename.startswith('._'):
                    mac_file_path = os.path.join(root, filename)
                    try:
                        file_size = os.path.getsize(mac_file_path)
                        os.remove(mac_file_path)
                        mac_files_deleted_count += 1
                        mac_files_deleted_size_bytes += file_size
                        if verbose:
                            print(f"  Deleted macOS junk file: '{mac_file_path}' (Size: {format_bytes(file_size)})")
                    except OSError as e:
                        print(f"  Error deleting macOS junk file '{mac_file_path}': {e}")
                        error_count += 1

        for filename in sorted(files):
            if filename.lower().endswith('.png') and not filename.startswith('._'):
                png_path = os.path.join(root, filename)
                base_name = os.path.splitext(filename)[0]
                jpg_filename = base_name + '.jpg'
                json_filename = base_name + '.json'
                jpg_path = os.path.join(root, jpg_filename)
                json_path = os.path.join(root, json_filename)

                if os.path.exists(jpg_path):
                    if not silent:
                        print(f"  {filename}: SKIPPED (JPG exists)")
                    skipped_count += 1
                    continue

                workflow_data = None
                actions = []
                
                try:
                    # 1. Extract workflow data from PNG using Pillow
                    with Image.open(png_path) as img:
                        if 'workflow' in img.info:
                            workflow_data = img.info['workflow']
                        
                        if verbose and workflow_data:
                            print(f"  Found workflow metadata in '{png_path}'")
                            print(f"    Workflow data type: {type(workflow_data)}")
                            print(f"    Workflow preview: {str(workflow_data)[:200]}...")

                    # 2. Convert PNG to JPG using ImageMagick (pixel data)
                    convert_command = [
                        'convert',
                        png_path,
                        '-quality', str(quality),
                        '-strip',  # Remove existing metadata for clean slate
                        jpg_path
                    ]

                    original_png_size = os.path.getsize(png_path) if os.path.exists(png_path) else 0

                    if verbose:
                        print(f"  Converting '{png_path}' to '{jpg_path}'...")
                    
                    subprocess.run(convert_command, check=True, capture_output=True, text=True)
                    actions.append("JPG created")
                    
                    if verbose:
                        print(f"    Conversion successful (image data): '{jpg_path}'")

                    # 3. Save workflow data as JSON file (raw dump, no extra structure)
                    if workflow_data:
                        try:
                            # If workflow_data is a string, parse it first
                            if isinstance(workflow_data, str):
                                workflow_obj = json.loads(workflow_data)
                            else:
                                workflow_obj = workflow_data
                            
                            # Check if we should save this JSON file
                            should_save = True
                            
                            # Find the most recent JSON file in the same directory
                            json_files = [f for f in os.listdir(root) if f.endswith('.json') and f != json_filename]
                            if json_files:
                                # Sort alphabetically and get the most recent one (highest number)
                                json_files.sort()
                                latest_json_path = os.path.join(root, json_files[-1])  # Last in alphabetical order
                                
                                try:
                                    with open(latest_json_path, 'r', encoding='utf-8') as f:
                                        previous_workflow = json.load(f)
                                    
                                    # Compare workflows, ignoring seed values
                                    if workflows_equal_ignore_seeds(workflow_obj, previous_workflow):
                                        should_save = False
                                        if verbose:
                                            print(f"    Workflow identical to '{json_files[0]}' (only seed differences), skipping JSON creation")
                                except (json.JSONDecodeError, FileNotFoundError, KeyError) as e:
                                    if verbose:
                                        print(f"    Could not compare with previous JSON: {e}")
                            
                            if should_save:
                                # Write the workflow object directly to JSON file
                                with open(json_path, 'w', encoding='utf-8') as json_file:
                                    json.dump(workflow_obj, json_file, indent=2, ensure_ascii=False)
                                
                                json_created_count += 1
                                actions.append("JSON created")
                                if verbose:
                                    print(f"    Created JSON file: '{json_path}'")
                            
                        except Exception as e:
                            print(f"    Error: Could not create JSON file for '{png_path}': {e}")
                            if verbose:
                                print(f"    Workflow data type: {type(workflow_data)}")
                                print(f"    Workflow data preview: {str(workflow_data)[:200]}...")
                    else:
                        if verbose:
                            print(f"    No workflow metadata found in '{png_path}', skipping JSON creation")

                    converted_count += 1

                    if delete_original:
                        try:
                            new_jpg_size = os.path.getsize(jpg_path) if os.path.exists(jpg_path) else 0
                            space_saved_this_file = original_png_size - new_jpg_size
                            total_space_saved_bytes += space_saved_this_file

                            os.remove(png_path)
                            actions.append("PNG deleted")
                            if verbose:
                                print(f"    Deleted original: '{png_path}' (Saved {format_bytes(space_saved_this_file)})")
                        except OSError as e:
                            print(f"    Error deleting '{png_path}': {e}")
                            error_count += 1
                    else:
                        if verbose and os.path.exists(jpg_path):
                            new_jpg_size = os.path.getsize(jpg_path)
                            size_change = original_png_size - new_jpg_size
                            print(f"    Size change: {format_bytes(original_png_size)} -> {format_bytes(new_jpg_size)} (Diff: {format_bytes(size_change)})")

                    # Print concise progress line
                    if not silent:
                        actions_str = ", ".join(actions)
                        print(f"  {filename}: {actions_str}")

                except FileNotFoundError:
                    print(f"Error: 'convert' command not found. Please ensure ImageMagick is installed and in your PATH.")
                    error_count += 1
                    return
                except subprocess.CalledProcessError as e:
                    print(f"  Error converting image data for '{png_path}':")
                    print(f"    Command: {' '.join(e.cmd)}")
                    print(f"    Return Code: {e.returncode}")
                    print(f"    stdout: {e.stdout.strip()}")
                    print(f"    stderr: {e.stderr.strip()}")
                    error_count += 1
                except Image.UnidentifiedImageError:
                    print(f"  Error: Could not identify image format for '{png_path}'. Skipping.")
                    error_count += 1
                except Exception as e:
                    print(f"  An unexpected error occurred with '{png_path}': {e}. Skipping.")
                    error_count += 1

    if not silent:
        print("-" * 50)
        print("Conversion Summary:")
        print(f"  Converted: {converted_count} files")
        print(f"  JSON files created: {json_created_count} files")
        print(f"  Skipped:   {skipped_count} files (JPG already existed)")
        print(f"  Errors:    {error_count} files")
        if delete_original:
            print(f"  Total Space Saved from PNGs: {format_bytes(total_space_saved_bytes)}")
        if clean_mac_files:
            print(f"  Mac Junk Files Deleted: {mac_files_deleted_count} files (Total Size: {format_bytes(mac_files_deleted_size_bytes)})")
        print("Conversion complete.")

def workflows_equal_ignore_seeds(workflow1, workflow2):
    """
    Compare two ComfyUI workflows, ignoring seed values.
    Returns True if workflows are identical except for seed values.
    """
    import copy
    
    # Make deep copies to avoid modifying the original data
    w1 = copy.deepcopy(workflow1)
    w2 = copy.deepcopy(workflow2)
    
    # Remove seed values from both workflows
    normalize_workflow_seeds(w1)
    normalize_workflow_seeds(w2)
    
    # Compare the normalized workflows
    return w1 == w2

def normalize_workflow_seeds(workflow):
    """
    Recursively removes or normalizes seed values in a ComfyUI workflow.
    Handles seeds in direct keys and in widgets_values arrays.
    """
    if isinstance(workflow, dict):
        # Common patterns for seed keys in ComfyUI
        seed_keys = ['seed', 'noise_seed']
        control_keys = ['control_after_generate']
        
        for key in seed_keys:
            if key in workflow:
                workflow[key] = 0  # Normalize to 0
        
        for key in control_keys:
            if key in workflow:
                workflow[key] = "fixed"  # Normalize control setting
        
        # Handle widgets_values array (common in ComfyUI nodes)
        if 'widgets_values' in workflow and isinstance(workflow['widgets_values'], list):
            widgets = workflow['widgets_values']
            # Look for seed patterns in widgets_values
            for i, value in enumerate(widgets):
                # Check if this looks like a seed value (large integer)
                if isinstance(value, int) and value > 1000000:  # Typical seed range
                    # Check if the next value is "randomize" or similar control
                    if i + 1 < len(widgets) and isinstance(widgets[i + 1], str) and widgets[i + 1] in ['randomize', 'increment', 'decrement', 'fixed']:
                        widgets[i] = 0  # Normalize the seed value
        
        # Also check in 'inputs' which is common in ComfyUI node structure
        if 'inputs' in workflow:
            normalize_workflow_seeds(workflow['inputs'])
        
        # Recursively process all nested dictionaries and lists
        for key, value in workflow.items():
            if isinstance(value, (dict, list)):
                normalize_workflow_seeds(value)
    
    elif isinstance(workflow, list):
        for item in workflow:
            normalize_workflow_seeds(item)

def format_bytes(bytes_value: int) -> str:
    """Formats bytes into human-readable units (KB, MB, GB)."""
    if bytes_value < 1024:
        return f"{bytes_value} B"
    elif bytes_value < 1024 * 1024:
        return f"{bytes_value / 1024:.2f} KB"
    elif bytes_value < 1024 * 1024 * 1024:
        return f"{bytes_value / (1024 * 1024):.2f} MB"
    else:
        return f"{bytes_value / (1024 * 1024 * 1024):.2f} GB"

def inspect_png_metadata(png_path: str) -> None:
    """
    Debug function to inspect PNG metadata structure.
    Use this to understand what's in your PNG files.
    """
    try:
        with Image.open(png_path) as img:
            print(f"Inspecting: {png_path}")
            print(f"Image format: {img.format}")
            print(f"Image size: {img.size}")
            print(f"Image mode: {img.mode}")
            print("\nMetadata keys found:")
            for key in img.info:
                print(f"  {key}: {type(img.info[key])}")
                if key in ['workflow', 'prompt']:
                    data = img.info[key]
                    print(f"    Content preview: {str(data)[:200]}...")
                    if isinstance(data, str):
                        try:
                            parsed = json.loads(data)
                            print(f"    JSON validation: OK (type: {type(parsed)})")
                        except json.JSONDecodeError as e:
                            print(f"    JSON validation: FAILED - {e}")
    except Exception as e:
        print(f"Error inspecting {png_path}: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Recursively convert PNG images to JPG with ComfyUI workflow metadata saved as JSON files and optionally clean up macOS junk files."
    )
    parser.add_argument(
        "source_directory",
        type=str,
        help="The root directory to start searching for PNG files."
    )
    parser.add_argument(
        "-q", "--quality",
        type=int,
        default=85,
        choices=range(0, 101),
        metavar="{0-100}",
        help="JPEG compression quality (0-100). Default is 85."
    )
    parser.add_argument(
        "-d", "--delete-original",
        action="store_true",
        help="Delete the original PNG file after successful conversion."
    )
    parser.add_argument(
        "-m", "--clean-mac-files",
        action="store_true",
        help="Delete files starting with '._' (macOS junk files)."
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output with detailed information for each file."
    )
    parser.add_argument(
        "-s", "--silent",
        action="store_true",
        help="Suppress all output except errors and final summary."
    )
    parser.add_argument(
        "--inspect",
        type=str,
        help="Inspect metadata of a specific PNG file (debugging)."
    )

    args = parser.parse_args()

    if args.inspect:
        inspect_png_metadata(args.inspect)
    else:
        convert_png_to_jpg_with_json(
            source_dir=args.source_directory,
            quality=args.quality,
            delete_original=args.delete_original,
            clean_mac_files=args.clean_mac_files,
            verbose=args.verbose,
            silent=args.silent
        )
