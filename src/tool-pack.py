import check_bin as _

from os import system, mkdir, listdir
from os.path import isfile
from sys import argv
from shutil import copy, copytree
from concurrent.futures import ThreadPoolExecutor

system("cls")

if "-y" not in argv:
    if input("Sure? (y/n) ").lower() not in ("yes", "y"):
        raise SystemExit

debug = "--debug" in argv
pack_files: list[tuple[str, bool]] = [
    ("main.py", False),
    ("tk_launcher.py", False),
    ("phigros.py", False),
    *(map(lambda x: (x, False), filter(lambda x: (
        x.startswith("tool-")
        and x.endswith(".py")
        and x not in (
            "tool-pack.py",
            "tool-create-innosetup-config.py"
        )
    ), listdir())))
]
res_files = [
    "_internal",
    
    "bin", "lib", "js",
    "resources", "shaders",
    "7z.dll", "7z.exe",
    "ecwv_installer.exe",
    "icon.ico",
    "libogg.dll", "libvorbis.dll",
    "web_canvas.html",
    "clear_errs.bat"
]
extend = open("_compile_pyiextend.py", "r", encoding="utf-8").read()

system("python -m venv pack_venv")
py = ".\\pack_venv\\Scripts\\python.exe"

system(f"{py} -m pip install --upgrade pip")
system(f"{py} -m pip install -r .\\requirements.txt")
system(f"{py} -m pip install pyinstaller")

pyinstaller = ".\\pack_venv\\Scripts\\pyinstaller.exe"
pyi_makespec = ".\\pack_venv\\Scripts\\pyi-makespec.exe"

spec_name = "spec_script"
system(f"{pyi_makespec} -n {spec_name} -i icon.ico {" ".join(map(lambda x: f"\"{x[0]}\"", pack_files))}")

with open(f"{spec_name}.spec", "a", encoding="utf-8") as f:
    f.seek(0)
    f.write(extend)
    f.write("\n")

system(f"{pyinstaller} {spec_name}.spec")

for file, _ in pack_files:
    system(f"xcopy \".\\dist\\{file.replace(".py", "")}\\*\" .\\ /c /q /e /y")

system("rmdir .\\pack_venv /s /q")
system("rmdir .\\build /s /q")
system("rmdir .\\dist /s /q")

if "--zip" in argv:
    _copy = lambda src, tar: copy(src, tar) if isfile(src) else copytree(src, f"{tar}\\{src}")
    try: mkdir(".\\compile_result")
    except FileExistsError: pass
    for i, _ in pack_files:
        _copy(i.replace(".py", ".exe"), ".\\compile_result")
    for i in res_files:
        _copy(i, ".\\compile_result")
    system("7z a compile_result.zip .\\compile_result\\*")

print("Pack complete!")
system("pause")
