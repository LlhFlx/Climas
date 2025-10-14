import os

def concat_models(project_root, output_file="all_urls.py"):
    with open(output_file, "w", encoding="utf-8") as outfile:
        for root, dirs, files in os.walk(project_root):
            if "models.py" in files:
                models_path = os.path.join(root, "urls.py")
                rel_path = os.path.relpath(models_path, project_root)

                outfile.write(f"\n\n# ===== From: {rel_path} =====\n\n")
                try:
                    with open(models_path, "r", encoding="utf-8") as infile:
                        outfile.write(infile.read())
                except:
                    pass
    print(f"All models concatenated into {output_file}")

if __name__ == "__main__":
    # Adjust this to your Django project root (where manage.py usually is)
    project_root = os.path.dirname(os.path.abspath(__file__))
    concat_models(project_root)
